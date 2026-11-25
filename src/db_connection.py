import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def get_database_engine(database: str) -> Engine:
    """
    Create a SQLAlchemy connection to the source or warehouse database.
    Source is read-only. Warehouse receives ETL data.
    """

    if database not in ("source", "warehouse"):
        raise ValueError(
            "Database must be either 'source' or 'warehouse'."
        )

    prefix = "SOURCE_DB" if database == "source" else "WAREHOUSE_DB"

    host = os.getenv(f"{prefix}_HOST")
    port = os.getenv(f"{prefix}_PORT", "5432")
    name = os.getenv(f"{prefix}_NAME")
    user = os.getenv(f"{prefix}_USER")
    password = os.getenv(f"{prefix}_PASSWORD")
    sslmode = os.getenv(f"{prefix}_SSLMODE")

    required = {
        "HOST": host,
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
    }

    missing = [
        key for key, value in required.items()
        if not value
    ]

    if missing:
        raise ValueError(
            f"Missing {database} configuration: {', '.join(missing)}"
        )

    connection_url = (
        f"postgresql+psycopg2://"
        f"{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )

    if sslmode:
        connection_url += f"?sslmode={quote_plus(sslmode)}"

    return create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=1800
    )
