"""Public holidays configuration settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_URL = os.getenv("API_URL", "https://nagerholidays.com/api/v4/Holidays")

_COUNTRY_CODES_RAW = os.getenv("COUNTRY_CODES", "CO,PE,EC,BO,CL")
COUNTRY_CODES = [c.strip() for c in _COUNTRY_CODES_RAW.split(",") if c.strip()]

_YEARS_RAW = os.getenv("YEARS", "2026")
YEARS = [int(y.strip()) for y in _YEARS_RAW.split(",") if y.strip()]

# Database configuration
DB_HOST = os.getenv("POS_DB_HOST", "localhost")
DB_PORT = int(os.getenv("POS_DB_PORT", "5432"))
DB_NAME = os.getenv("POS_DB_NAME", "")
DB_USER = os.getenv("POS_DB_USER", "")
DB_PASSWORD = os.getenv("POS_DB_PASSWORD", "")
