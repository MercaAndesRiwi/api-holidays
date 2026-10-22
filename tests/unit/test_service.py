"""Unit tests for HolidayIngestionService (SOLID - LSP, OCP, DIP)."""

from datetime import date
from typing import Any

from holidays.service import HolidayIngestionService


class InMemoryRepository:
    """In-memory test implementation of HolidaysRepositoryProtocol."""

    def __init__(self) -> None:
        self.table_created = False
        self.stored_holidays: list[dict[str, Any]] = []

    def create_table_if_not_exists(self) -> None:
        self.table_created = True

    def upsert_holidays(self, holidays: list[dict[str, Any]]) -> int:
        self.stored_holidays.extend(holidays)
        return len(holidays)


class StaticHolidayProvider:
    """Alternative implementation of HolidaysProvider demonstrating LSP and OCP."""

    def fetch_holidays(self, country_code: str, year: int) -> list[dict[str, Any]]:
        return [
            {
                "country_code": country_code,
                "holiday_date": date(year, 1, 1),
                "holiday_name": f"Holiday {country_code}",
                "source": "Static Provider Test",
            }
        ]


def test_service_ingest_orchestration():
    provider = StaticHolidayProvider()
    repo = InMemoryRepository()

    service = HolidayIngestionService(provider=provider, repository=repo)
    total = service.ingest(country_codes=["CO", "PE"], years=[2026])

    assert total == 2
    assert repo.table_created is True
    assert len(repo.stored_holidays) == 2
    assert repo.stored_holidays[0]["country_code"] == "CO"
    assert repo.stored_holidays[1]["country_code"] == "PE"


def test_service_ingest_empty_countries():
    provider = StaticHolidayProvider()
    repo = InMemoryRepository()

    service = HolidayIngestionService(provider=provider, repository=repo)
    total = service.ingest(country_codes=[], years=[2026])

    assert total == 0
    assert repo.table_created is True
    assert len(repo.stored_holidays) == 0
