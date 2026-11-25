import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from src.db_connection import get_database_engine


def main():
    engine = get_database_engine("warehouse")

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT current_database(), current_user;")
            )

            database, user = result.fetchone()

            print("WAREHOUSE CONNECTION SUCCESSFUL")
            print(f"Database: {database}")
            print(f"User: {user}")

            schemas = connection.execute(
                text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name IN (
                        'staging',
                        'analytics',
                        'etl_metadata'
                    )
                    ORDER BY schema_name;
                """)
            )

            print("\nExisting warehouse schemas:")

            for row in schemas:
                print(f"- {row.schema_name}")

    except Exception as error:
        print("WAREHOUSE CONNECTION FAILED")
        print(error)

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
