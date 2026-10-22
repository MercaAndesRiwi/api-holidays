"""Domain protocols and contracts for the public holidays ingestion service."""

from __future__ import annotations

from typing import Any, Iterable, Protocol


class HolidaysProvider(Protocol):
    """Abstract contract for public holidays data providers."""

    def fetch_holidays(self, country_code: str, year: int) -> list[dict[str, Any]]:
        """Fetch holidays for a given country code and year."""
        ...


class HolidaysRepositoryProtocol(Protocol):
    """Abstract contract for holidays storage and persistence."""

    def create_table_if_not_exists(self) -> None:
        """Ensure the storage table or schema exists."""
        ...

    def upsert_holidays(self, holidays: Iterable[dict[str, Any]]) -> int:
        """Insert or update holidays avoiding duplicate records."""
        ...
