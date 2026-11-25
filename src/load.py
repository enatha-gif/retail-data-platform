import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from src.extract import SOURCE_TABLES

SCHEMA = "staging"


def load_batch(
    engine: Engine,
    table_name: str,
    rows: list[dict]
) -> int:
    """
    Insert or update one batch of records in the staging schema.
    Returns the number of rows processed.
    """

    if table_name not in SOURCE_TABLES:
        raise ValueError(f"Unsupported staging table: {table_name}")

    if not rows:
        return 0

    metadata = MetaData()

    table = Table(
        table_name,
        metadata,
        schema=SCHEMA,
        autoload_with=engine
    )

    primary_key = SOURCE_TABLES[table_name]
    valid_columns = set(table.columns.keys())

    cleaned_rows = [
        {
            key: value
            for key, value in row.items()
            if key in valid_columns
        }
        for row in rows
    ]

    statement = insert(table).values(cleaned_rows)

    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name != primary_key
    }

    statement = statement.on_conflict_do_update(
        index_elements=[table.c[primary_key]],
        set_=update_columns
    )

    with engine.begin() as connection:
        connection.execute(statement)

    return len(cleaned_rows)


if __name__ == "__main__":
    print("Supported staging tables:")

    for table_name in SOURCE_TABLES:
        print(f"- staging.{table_name}")

    print("\nLoading strategy: INSERT ON CONFLICT DO UPDATE")
