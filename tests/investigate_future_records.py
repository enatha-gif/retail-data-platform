import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from src.db_connection import get_database_engine


def main():
    engine = get_database_engine("source")

    try:
        with engine.connect() as connection:

            print("\nORDER_ITEMS WATERMARK INVESTIGATION")
            print("=" * 70)

            summary = connection.execute(text("""
                SELECT
                    NOW() AS source_time,
                    MAX(updated_at) AS maximum_timestamp,
                    MAX(updated_at) FILTER (
                        WHERE updated_at <= NOW()
                    ) AS latest_valid_timestamp,
                    COUNT(*) FILTER (
                        WHERE updated_at > NOW()
                    ) AS future_records
                FROM shop.order_items
            """)).fetchone()

            print(f"Source time: {summary.source_time}")
            print(f"Maximum timestamp: {summary.maximum_timestamp}")
            print(f"Latest valid timestamp: {summary.latest_valid_timestamp}")
            print(f"Future-dated records: {summary.future_records}")

            print("\nFUTURE-DATED RECORDS")
            print("-" * 70)

            rows = connection.execute(text("""
                SELECT
                    order_item_id,
                    order_id,
                    product_id,
                    created_at,
                    updated_at
                FROM shop.order_items
                WHERE updated_at > NOW()
                ORDER BY updated_at
            """)).fetchall()

            for row in rows:
                print(
                    f"Item ID: {row.order_item_id} | "
                    f"Order ID: {row.order_id} | "
                    f"Product ID: {row.product_id} | "
                    f"Created: {row.created_at} | "
                    f"Updated: {row.updated_at}"
                )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
