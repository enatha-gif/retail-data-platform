import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential

from src.db_connection import get_database_engine
from src.extract import SOURCE_TABLES, extract_table
from src.load import load_batch
from src.logger import get_logger


logger = get_logger("retail_etl")

FULL_LOAD_TABLES = {"categories", "products"}
CHUNK_SIZE = 1000


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def load_with_retry(engine, table_name, rows):
    return load_batch(engine, table_name, rows)


def get_watermark(warehouse_connection, table_name):
    result = warehouse_connection.execute(
        text("""
            SELECT last_updated_at
            FROM etl_metadata.etl_watermarks
            WHERE table_name = :table_name
        """),
        {"table_name": table_name}
    )

    row = result.fetchone()
    return row[0] if row else None


def create_run_log(warehouse_engine, table_name):
    with warehouse_engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO etl_metadata.etl_run_log (
                    table_name,
                    status
                )
                VALUES (:table_name, 'running')
                RETURNING run_id
            """),
            {"table_name": table_name}
        )

        return result.scalar_one()


def finish_run_log(
    warehouse_engine,
    run_id,
    status,
    rows_extracted,
    rows_loaded,
    error_message=None
):
    with warehouse_engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE etl_metadata.etl_run_log
                SET
                    finished_at = NOW(),
                    status = :status,
                    rows_extracted = :rows_extracted,
                    rows_loaded = :rows_loaded,
                    error_message = :error_message
                WHERE run_id = :run_id
            """),
            {
                "run_id": run_id,
                "status": status,
                "rows_extracted": rows_extracted,
                "rows_loaded": rows_loaded,
                "error_message": (
                    error_message[:4000]
                    if error_message else None
                )
            }
        )


def save_watermark(
    warehouse_engine,
    table_name,
    last_updated_at,
    rows_loaded
):
    with warehouse_engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO etl_metadata.etl_watermarks (
                    table_name,
                    last_updated_at,
                    last_run_at,
                    rows_loaded
                )
                VALUES (
                    :table_name,
                    :last_updated_at,
                    NOW(),
                    :rows_loaded
                )
                ON CONFLICT (table_name)
                DO UPDATE SET
                    last_updated_at = COALESCE(
                        GREATEST(
                            etl_metadata.etl_watermarks.last_updated_at,
                            EXCLUDED.last_updated_at
                        ),
                        etl_metadata.etl_watermarks.last_updated_at,
                        EXCLUDED.last_updated_at
                    ),
                    last_run_at = NOW(),
                    rows_loaded =
                        etl_metadata.etl_watermarks.rows_loaded
                        + EXCLUDED.rows_loaded
            """),
            {
                "table_name": table_name,
                "last_updated_at": last_updated_at,
                "rows_loaded": rows_loaded
            }
        )


def process_table(
    source_connection,
    warehouse_engine,
    table_name
):
    logger.info("Starting table: %s", table_name)

    rows_extracted = 0
    rows_loaded = 0
    latest_valid_updated_at = None

    run_id = create_run_log(warehouse_engine, table_name)

    try:
        # Get the source database's current time.
        source_now = source_connection.execute(
            text("SELECT NOW()")
        ).scalar_one()

        with warehouse_engine.connect() as connection:
            previous_watermark = get_watermark(
                connection,
                table_name
            )

        if table_name in FULL_LOAD_TABLES:
            watermark = None
            logger.info(
                "%s: full extraction selected",
                table_name
            )
        else:
            watermark = previous_watermark

            if watermark is None:
                logger.info(
                    "%s: first run, performing full extraction",
                    table_name
                )
            else:
                logger.info(
                    "%s: incremental extraction from %s up to %s",
                    table_name,
                    watermark,
                    source_now
                )

        batches = extract_table(
            connection=source_connection,
            table_name=table_name,
            last_updated_at=watermark,
            chunk_size=CHUNK_SIZE
        )

        for batch in batches:
            batch_count = len(batch)
            rows_extracted += batch_count

            # Only valid timestamps can advance the watermark.
            valid_timestamps = [
                row["updated_at"]
                for row in batch
                if (
                    row.get("updated_at") is not None
                    and row["updated_at"] <= source_now
                )
            ]

            if valid_timestamps:
                batch_max_timestamp = max(valid_timestamps)

                if (
                    latest_valid_updated_at is None
                    or batch_max_timestamp > latest_valid_updated_at
                ):
                    latest_valid_updated_at = batch_max_timestamp

            loaded = load_with_retry(
                warehouse_engine,
                table_name,
                batch
            )

            rows_loaded += loaded

            logger.info(
                "%s: extracted %s, loaded %s",
                table_name,
                batch_count,
                loaded
            )

        save_watermark(
            warehouse_engine,
            table_name,
            latest_valid_updated_at,
            rows_loaded
        )

        finish_run_log(
            warehouse_engine,
            run_id,
            "success",
            rows_extracted,
            rows_loaded
        )

        logger.info(
            "%s completed successfully. Extracted=%s, Loaded=%s",
            table_name,
            rows_extracted,
            rows_loaded
        )

        if (
            table_name == "order_items"
            and latest_valid_updated_at is not None
        ):
            logger.info(
                "order_items watermark limited to valid timestamp: %s",
                latest_valid_updated_at
            )

    except Exception as error:
        finish_run_log(
            warehouse_engine,
            run_id,
            "failed",
            rows_extracted,
            rows_loaded,
            str(error)
        )

        logger.exception(
            "ETL failed for table %s",
            table_name
        )

        raise


def run_pipeline():
    source_engine = get_database_engine("source")
    warehouse_engine = get_database_engine("warehouse")

    logger.info("=" * 60)
    logger.info("RETAIL DATA PLATFORM ETL STARTED")
    logger.info(
        "Started at: %s",
        datetime.now(timezone.utc)
    )
    logger.info("=" * 60)

    try:
        with source_engine.connect() as source_connection:
            for table_name in SOURCE_TABLES:
                process_table(
                    source_connection,
                    warehouse_engine,
                    table_name
                )

        logger.info("=" * 60)
        logger.info("ALL TABLES PROCESSED SUCCESSFULLY")
        logger.info("ETL pipeline finished.")
        logger.info("=" * 60)

    except Exception:
        logger.error(
            "ETL pipeline stopped because a table failed."
        )
        raise

    finally:
        source_engine.dispose()
        warehouse_engine.dispose()


if __name__ == "__main__":
    run_pipeline()
