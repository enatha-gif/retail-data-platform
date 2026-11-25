import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from src.db_connection import get_database_engine

TABLES = [
    "categories",
    "customers",
    "addresses",
    "products",
    "orders",
    "order_items",
    "payments",
]

def main():
    engine = get_database_engine("source")

    try:
        with engine.connect() as connection:
            print("\nSOURCE TIMESTAMP INVESTIGATION")
            print("=" * 80)

            for table in TABLES:
                query = text(f"""
                    SELECT
                        COUNT(*) AS total_records,
                        MIN(updated_at) AS earliest_update,
                        MAX(updated_at) AS latest_update,
                        COUNT(*) FILTER (
                            WHERE updated_at > NOW()
                        ) AS future_records,
                        NOW() AS source_current_time
                    FROM shop.{table}
                """)

                row = connection.execute(query).fetchone()

                print(f"\nTable: {table}")
                print(f"Total records: {row.total_records}")
                print(f"Earliest updated_at: {row.earliest_update}")
                print(f"Latest updated_at: {row.latest_update}")
                print(f"Future-dated records: {row.future_records}")
                print(f"Source database time: {row.source_current_time}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
