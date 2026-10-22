"""PostgreSQL database connection helper."""

import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine


def get_engine() -> Engine:
    """Create a SQLAlchemy Engine instance from environment variables."""
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("POS_DB_USER"),
        password=os.getenv("POS_DB_PASSWORD"),
        host=os.getenv("POS_DB_HOST", "localhost"),
        port=int(os.getenv("POS_DB_PORT", "5432")),
        database=os.getenv("POS_DB_NAME"),
    )
    return create_engine(database_url)
