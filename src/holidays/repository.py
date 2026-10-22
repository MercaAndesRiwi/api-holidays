"""Data access repository for public holidays."""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection

from holidays.db import get_engine


class HolidaysRepository:
    """CRUD operations for the public.holidays table."""

    def __init__(self, connection: Connection | None = None):
        self._owns_connection = connection is None
        self.connection = connection or get_engine().connect()

    def create_table_if_not_exists(self) -> None:
        """Create public.holidays table if it does not already exist."""
        self.connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS public.holidays (
                    holiday_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    country_code VARCHAR(2) NOT NULL,
                    holiday_date DATE NOT NULL,
                    holiday_name VARCHAR(150) NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    CONSTRAINT uq_holiday_country_date_name
                        UNIQUE (country_code, holiday_date, holiday_name)
                )
                """
            )
        )

    def upsert_holidays(self, holidays: Iterable[dict]) -> int:
        """Insert or update holidays in batch. Returns the number of processed rows."""
        holidays_list = list(holidays)
        if not holidays_list:
            return 0

        self.connection.execute(
            text(
                """
                INSERT INTO public.holidays (
                    country_code,
                    holiday_date,
                    holiday_name,
                    source
                )
                VALUES (
                    :country_code,
                    :holiday_date,
                    :holiday_name,
                    :source
                )
                ON CONFLICT (
                    country_code,
                    holiday_date,
                    holiday_name
                )
                DO UPDATE SET source = EXCLUDED.source
                """
            ),
            holidays_list,
        )

        if self._owns_connection:
            self.connection.commit()
            self.connection.close()

        return len(holidays_list)
