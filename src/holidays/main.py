"""Entry point for public holidays ingestion.

Integrated validations (self-contained, no external orchestrator required):
- Verifies PostgreSQL environment variables.
- Verifies database connectivity.
- Validates COUNTRY_CODES is non-empty and contains valid country codes.
- Validates YEARS contains valid years.
- Tests connectivity with the Nager.Date API.
"""

from __future__ import annotations

import logging
import os
import sys

from sqlalchemy import text

from holidays.client import NagerDateClient
from holidays.config import API_URL, COUNTRY_CODES, YEARS
from holidays.db import get_engine
from holidays.repository import HolidaysRepository
from holidays.service import HolidayIngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("holidays")


def validate_environment() -> None:
    """Validate required environment variables."""
    required_vars = ["POS_DB_HOST", "POS_DB_PORT", "POS_DB_NAME", "POS_DB_USER", "POS_DB_PASSWORD"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error("Missing required environment variables: %s", missing)
        logger.info("Copy .env.example to .env and configure your PostgreSQL credentials.")
        sys.exit(1)

    valid_countries = {"CO", "PE", "EC", "BO", "CL"}
    invalid = [c for c in COUNTRY_CODES if c not in valid_countries]
    if invalid:
        logger.error("Invalid countries in COUNTRY_CODES: %s. Allowed: %s", invalid, sorted(valid_countries))
        sys.exit(1)

    if not YEARS:
        logger.error("YEARS cannot be empty.")
        sys.exit(1)

    for year in YEARS:
        if year < 1900 or year > 2100:
            logger.error("Invalid year in YEARS: %s. Must be between 1900 and 2100.", year)
            sys.exit(1)

    logger.info("Environment validation: OK")


def validate_database_connection() -> None:
    """Validate PostgreSQL database connection."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        logger.info("PostgreSQL database connection: OK")
    except Exception as exc:
        logger.error("Could not connect to PostgreSQL: %s", str(exc).encode("ascii", "replace").decode("ascii"))
        sys.exit(1)


def validate_nager_date_api() -> None:
    """Validate that the Nager.Date API responds."""
    try:
        client = NagerDateClient(base_url=API_URL, max_retries=2)
        client.fetch_holidays(COUNTRY_CODES[0], YEARS[0])
        logger.info("Nager.Date API validation: OK")
    except Exception as exc:
        logger.error("Could not connect to Nager.Date API: %s", exc)
        sys.exit(1)


def load_holidays() -> None:
    """Orchestrate public holidays fetch and load via the domain service."""
    validate_environment()
    validate_database_connection()
    validate_nager_date_api()

    # Dependency Injection (Composition Root)
    client = NagerDateClient(base_url=API_URL)
    engine = get_engine()

    try:
        with engine.begin() as connection:
            repo = HolidaysRepository(connection)
            service = HolidayIngestionService(provider=client, repository=repo)
            service.ingest(country_codes=COUNTRY_CODES, years=YEARS)
    finally:
        engine.dispose()


if __name__ == "__main__":
    load_holidays()
