from sqlalchemy import text
from sqlalchemy.engine import Connection

SOURCE_TABLES = {
    "categories": "category_id",
    "customers": "customer_id",
    "addresses": "address_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
    "payments": "payment_id",
}

CHUNK_SIZE = 1000


def extract_table(
    connection: Connection,
    table_name: str,
    last_updated_at=None,
    chunk_size: int = CHUNK_SIZE
):
    """
    Extract records from the read-only Supabase source.

    First extraction:
        Read all records, including records with future timestamps.

    Incremental extraction:
        Read records from the saved watermark up to the source
        database's current time.
    """

    if table_name not in SOURCE_TABLES:
        raise ValueError(f"Unsupported source table: {table_name}")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    primary_key = SOURCE_TABLES[table_name]

    query = f"SELECT * FROM shop.{table_name}"
    parameters = {}

    if last_updated_at is not None:
        query += """
            WHERE updated_at >= :last_updated_at
              AND updated_at <= NOW()
        """
        parameters["last_updated_at"] = last_updated_at

    query += f" ORDER BY updated_at, {primary_key}"

    statement = text(query)

    result = connection.execution_options(
        stream_results=True
    ).execute(statement, parameters)

    try:
        while True:
            rows = result.fetchmany(chunk_size)

            if not rows:
                break

            yield [
                dict(row._mapping)
                for row in rows
            ]

    finally:
        result.close()
