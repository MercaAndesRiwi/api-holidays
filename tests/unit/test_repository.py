"""Unit tests for HolidaysRepository."""

from datetime import date
from unittest.mock import MagicMock

from holidays.repository import HolidaysRepository


def test_create_table_if_not_exists():
    mock_conn = MagicMock()
    repo = HolidaysRepository(connection=mock_conn)
    repo.create_table_if_not_exists()

    assert mock_conn.execute.called
    stmt = str(mock_conn.execute.call_args[0][0])
    assert "CREATE TABLE IF NOT EXISTS public.holidays" in stmt


def test_upsert_holidays_empty_returns_zero():
    mock_conn = MagicMock()
    repo = HolidaysRepository(connection=mock_conn)
    result = repo.upsert_holidays([])

    assert result == 0
    assert not mock_conn.execute.called


def test_upsert_holidays_batch_success():
    mock_conn = MagicMock()
    repo = HolidaysRepository(connection=mock_conn)
    holidays = [
        {
            "country_code": "CO",
            "holiday_date": date(2026, 1, 1),
            "holiday_name": "New Year's Day",
            "source": "Nager.Date API v4",
        },
        {
            "country_code": "CO",
            "holiday_date": date(2026, 5, 1),
            "holiday_name": "Labor Day",
            "source": "Nager.Date API v4",
        },
    ]

    result = repo.upsert_holidays(holidays)

    assert result == 2
    assert mock_conn.execute.called
    args = mock_conn.execute.call_args[0]
    stmt = str(args[0])
    batch_data = args[1]
    assert "INSERT INTO public.holidays" in stmt
    assert "ON CONFLICT" in stmt
    assert len(batch_data) == 2
