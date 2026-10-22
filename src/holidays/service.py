"""Domain service for public holidays ingestion orchestration."""

from __future__ import annotations

import logging
from typing import Sequence

from holidays.protocols import HolidaysProvider, HolidaysRepositoryProtocol

logger = logging.getLogger(__name__)


class HolidayIngestionService:
    """High-level use case coordinating public holidays ingestion.

    Adheres to the Dependency Inversion Principle (DIP) by depending
    only on abstractions (HolidaysProvider and HolidaysRepositoryProtocol)
    and to the Open/Closed Principle (OCP) by allowing extension of new
    providers and repositories without modifying this class.
    """

    def __init__(
        self,
        provider: HolidaysProvider,
        repository: HolidaysRepositoryProtocol,
    ) -> None:
        self._provider = provider
        self._repository = repository

    def ingest(self, country_codes: Sequence[str], years: Sequence[int]) -> int:
        """Fetch and persist public holidays for the specified country codes and years."""
        self._repository.create_table_if_not_exists()

        total = 0
        for country_code in country_codes:
            for year in years:
                holidays = self._provider.fetch_holidays(country_code, year)
                self._repository.upsert_holidays(holidays)
                total += len(holidays)
                logger.info("Public holidays observed: %s %d = %d", country_code, year, len(holidays))

        logger.info("Total records received: %d", total)
        return total
