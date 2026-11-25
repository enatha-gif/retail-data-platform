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
            result = connection.execute(
                text("SELECT current_database(), current_user;")
            )
            database, user = result.fetchone()

            print("SOURCE CONNECTION SUCCESSFUL")
            print(f"Database: {database}")
            print(f"User: {user}")

            result = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'shop'
                    AND table_name IN (
                        'categories',
                        'customers',
                        'addresses',
                        'products',
                        'orders',
                        'order_items',
                        'payments'
                    );
                """)
            )

            print(f"Source tables found: {result.scalar()}")

    except Exception as error:
        print("SOURCE CONNECTION FAILED")
        print(error)

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
