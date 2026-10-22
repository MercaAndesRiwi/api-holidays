"""Client for the Nager.Date public holidays API."""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NagerDateClient:
    """Synchronous client to query public holidays from Nager.Date with retry logic."""

    def __init__(
        self,
        base_url: str = "https://nagerholidays.com/api/v4/Holidays",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        client: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._headers = {"User-Agent": "MercadAndesHolidays/1.0"}
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=self.timeout, headers=self._headers)

    def fetch_holidays(self, country_code: str, year: int) -> list[dict[str, Any]]:
        """Fetch the list of holidays for a given country code and year with retries."""
        url = f"{self.base_url}/{country_code}/{year}"

        owns_client = self._client is None
        client = self._get_client()

        try:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    break
                except (httpx.HTTPError, httpx.TimeoutException) as exc:
                    if attempt < self.max_retries:
                        sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                        logger.warning(
                            "Error requesting %s (attempt %d/%d): %s. Retrying in %.1fs...",
                            url,
                            attempt,
                            self.max_retries,
                            exc,
                            sleep_time,
                        )
                        time.sleep(sleep_time)
                    else:
                        logger.error(
                            "All %d attempts failed for %s: %s",
                            self.max_retries,
                            url,
                            exc,
                        )
                        raise
        finally:
            if owns_client:
                client.close()

        if not isinstance(data, list):
            raise ValueError(f"Unexpected response for {country_code}/{year}: expected a list.")

        holidays: list[dict[str, Any]] = []
        for item in data:
            holidays.append(
                {
                    "country_code": country_code,
                    "holiday_date": date.fromisoformat(item["date"]),
                    "holiday_name": item["name"],
                    "source": "Nager.Date API v4",
                }
            )

        return holidays
