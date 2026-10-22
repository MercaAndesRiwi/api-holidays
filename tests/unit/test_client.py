"""Unit tests for the Nager.Date public holidays API client."""

from datetime import date
from unittest.mock import MagicMock

import httpx
import pytest

from holidays.client import NagerDateClient


def test_fetch_holidays_success():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = [
        {"date": "2026-01-01", "name": "New Year's Day"}
    ]
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    client = NagerDateClient(client=mock_client)
    holidays = client.fetch_holidays("CO", 2026)

    assert len(holidays) == 1
    assert holidays[0]["country_code"] == "CO"
    assert holidays[0]["holiday_date"] == date(2026, 1, 1)
    assert holidays[0]["holiday_name"] == "New Year's Day"
    assert holidays[0]["source"] == "Nager.Date API v4"


def test_fetch_holidays_returns_empty():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    client = NagerDateClient(client=mock_client)
    holidays = client.fetch_holidays("CO", 2026)
    assert holidays == []


def test_fetch_holidays_retry_then_succeeds():
    mock_client = MagicMock(spec=httpx.Client)

    req = httpx.Request("GET", "https://nagerholidays.com/api/v4/Holidays/CO/2026")
    fail_mock = MagicMock(spec=httpx.Response)
    fail_mock.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=req, response=httpx.Response(500, request=req)
    )

    success_mock = MagicMock(spec=httpx.Response)
    success_mock.raise_for_status.return_value = None
    success_mock.json.return_value = [{"date": "2026-05-01", "name": "Labor Day"}]

    mock_client.get.side_effect = [fail_mock, success_mock]

    client = NagerDateClient(client=mock_client, max_retries=2, backoff_factor=0.01)
    holidays = client.fetch_holidays("CO", 2026)

    assert len(holidays) == 1
    assert holidays[0]["holiday_name"] == "Labor Day"
    assert mock_client.get.call_count == 2


def test_fetch_holidays_raises_after_max_retries():
    mock_client = MagicMock(spec=httpx.Client)
    req = httpx.Request("GET", "https://nagerholidays.com/api/v4/Holidays/CO/2026")
    mock_client.get.side_effect = httpx.ConnectTimeout("Timeout", request=req)

    client = NagerDateClient(client=mock_client, max_retries=2, backoff_factor=0.01)
    with pytest.raises(httpx.ConnectTimeout):
        client.fetch_holidays("CO", 2026)

    assert mock_client.get.call_count == 2


def test_fetch_holidays_invalid_json_format():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"error": "not a list"}
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    client = NagerDateClient(client=mock_client)
    with pytest.raises(ValueError, match="expected a list"):
        client.fetch_holidays("CO", 2026)
