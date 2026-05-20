"""Unit tests for app.services.price_service — get_recent_prices."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import Engine

from app.services.price_service import get_recent_prices


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_engine(max_date_value, df: pd.DataFrame | None = None):
    """Create a mock engine with configurable max_date scalar and read_sql result.

    Returns (engine, patch_read_sql) where patch_read_sql is a context manager
    that patches pd.read_sql to return the given DataFrame.
    """
    engine = MagicMock(spec=Engine)

    # Each call to engine.connect() returns a fresh context manager mock
    def _connect_side_effect():
        conn = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=conn)
        ctx.__exit__ = MagicMock(return_value=False)
        # conn.execute(...).scalar() returns max_date_value
        result_mock = MagicMock()
        result_mock.scalar.return_value = max_date_value
        conn.execute.return_value = result_mock
        return ctx

    engine.connect.side_effect = _connect_side_effect
    return engine


# ---------------------------------------------------------------------------
# Tests: days parameter clamping
# ---------------------------------------------------------------------------


class TestDaysClamping:
    """Requirement 5.1, 5.2 — days parameter is clamped to [1, 30]."""

    def test_days_above_30_clamped_to_30(self):
        """days=50 should be clamped to 30 in the returned dict."""
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=50)

        assert result["days"] == 30

    def test_days_below_1_clamped_to_1(self):
        """days=0 should be clamped to 1 in the returned dict."""
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=0)

        assert result["days"] == 1

    def test_negative_days_clamped_to_1(self):
        """days=-5 should be clamped to 1."""
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=-5)

        assert result["days"] == 1

    def test_days_within_range_unchanged(self):
        """days=15 should remain 15."""
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=15)

        assert result["days"] == 15


# ---------------------------------------------------------------------------
# Tests: no price records (max_date is None)
# ---------------------------------------------------------------------------


class TestNoPriceRecords:
    """Requirement 5.3 — empty database returns success with empty provinces."""

    def test_no_records_returns_success_true(self):
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=7)

        assert result["success"] is True

    def test_no_records_returns_empty_provinces(self):
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=7)

        assert result["provinces"] == []

    def test_no_records_returns_count_zero(self):
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=7)

        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Tests: multiple provinces aggregation
# ---------------------------------------------------------------------------


class TestMultipleProvinces:
    """Requirement 5.4 — correct aggregation per province."""

    @pytest.fixture
    def multi_province_df(self):
        """DataFrame with 3 days of data for DakLak and GiaLai."""
        base = date(2024, 6, 1)
        rows = [
            {"region": "DakLak", "date": base, "price_vnd_per_kg": 90000.0},
            {"region": "DakLak", "date": base + timedelta(days=1), "price_vnd_per_kg": 92000.0},
            {"region": "DakLak", "date": base + timedelta(days=2), "price_vnd_per_kg": 95000.0},
            {"region": "GiaLai", "date": base, "price_vnd_per_kg": 88000.0},
            {"region": "GiaLai", "date": base + timedelta(days=1), "price_vnd_per_kg": 89000.0},
            {"region": "GiaLai", "date": base + timedelta(days=2), "price_vnd_per_kg": 91000.0},
        ]
        return pd.DataFrame(rows)

    def test_returns_one_entry_per_province(self, multi_province_df):
        max_date = date(2024, 6, 3)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=multi_province_df):
            result = get_recent_prices(engine, days=7)

        assert result["count"] == 2
        names = [p["name"] for p in result["provinces"]]
        assert "DakLak" in names
        assert "GiaLai" in names

    def test_province_has_correct_display_name(self, multi_province_df):
        max_date = date(2024, 6, 3)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=multi_province_df):
            result = get_recent_prices(engine, days=7)

        daklak = next(p for p in result["provinces"] if p["name"] == "DakLak")
        assert daklak["display_name"] == "Dak Lak"

    def test_current_price_is_last_chronological(self, multi_province_df):
        max_date = date(2024, 6, 3)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=multi_province_df):
            result = get_recent_prices(engine, days=7)

        daklak = next(p for p in result["provinces"] if p["name"] == "DakLak")
        assert daklak["current_price"] == 95000.0

    def test_avg_price_rounded_to_zero_decimals(self, multi_province_df):
        max_date = date(2024, 6, 3)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=multi_province_df):
            result = get_recent_prices(engine, days=7)

        daklak = next(p for p in result["provinces"] if p["name"] == "DakLak")
        expected_avg = round((90000.0 + 92000.0 + 95000.0) / 3, 0)
        assert daklak["avg_price"] == expected_avg

    def test_min_and_max_price(self, multi_province_df):
        max_date = date(2024, 6, 3)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=multi_province_df):
            result = get_recent_prices(engine, days=7)

        daklak = next(p for p in result["provinces"] if p["name"] == "DakLak")
        assert daklak["min_price"] == 90000.0
        assert daklak["max_price"] == 95000.0


# ---------------------------------------------------------------------------
# Tests: price_change computation
# ---------------------------------------------------------------------------


class TestPriceChange:
    """Requirement 5.5 — price_change = last - first price."""

    def test_price_change_is_last_minus_first(self):
        base = date(2024, 6, 1)
        df = pd.DataFrame([
            {"region": "DakLak", "date": base, "price_vnd_per_kg": 80000.0},
            {"region": "DakLak", "date": base + timedelta(days=1), "price_vnd_per_kg": 85000.0},
            {"region": "DakLak", "date": base + timedelta(days=2), "price_vnd_per_kg": 90000.0},
        ])
        max_date = date(2024, 6, 3)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=7)

        daklak = result["provinces"][0]
        # price_change = last (90000) - first (80000) = 10000
        assert daklak["price_change"] == 10000.0

    def test_price_change_percent_computed_correctly(self):
        base = date(2024, 6, 1)
        df = pd.DataFrame([
            {"region": "DakLak", "date": base, "price_vnd_per_kg": 80000.0},
            {"region": "DakLak", "date": base + timedelta(days=1), "price_vnd_per_kg": 90000.0},
        ])
        max_date = date(2024, 6, 2)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=7)

        daklak = result["provinces"][0]
        # change = 90000 - 80000 = 10000
        # percent = (10000 / 80000) * 100 = 12.5
        assert daklak["price_change_percent"] == 12.5


# ---------------------------------------------------------------------------
# Tests: price_change_percent=None when previous price is zero
# ---------------------------------------------------------------------------


class TestPriceChangePercentZeroPrevious:
    """Requirement 5.6 — price_change_percent is None when earliest price is 0."""

    def test_zero_previous_price_returns_none_percent(self):
        base = date(2024, 6, 1)
        df = pd.DataFrame([
            {"region": "DakLak", "date": base, "price_vnd_per_kg": 0.0},
            {"region": "DakLak", "date": base + timedelta(days=1), "price_vnd_per_kg": 50000.0},
        ])
        max_date = date(2024, 6, 2)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=7)

        daklak = result["provinces"][0]
        assert daklak["price_change"] == 50000.0
        assert daklak["price_change_percent"] is None


# ---------------------------------------------------------------------------
# Tests: single price record
# ---------------------------------------------------------------------------


class TestSinglePriceRecord:
    """Requirement 5.7 — single record means price_change=None, price_change_percent=None."""

    def test_single_record_price_change_is_none(self):
        base = date(2024, 6, 1)
        df = pd.DataFrame([
            {"region": "DakLak", "date": base, "price_vnd_per_kg": 95000.0},
        ])
        max_date = date(2024, 6, 1)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=7)

        daklak = result["provinces"][0]
        assert daklak["price_change"] is None

    def test_single_record_price_change_percent_is_none(self):
        base = date(2024, 6, 1)
        df = pd.DataFrame([
            {"region": "DakLak", "date": base, "price_vnd_per_kg": 95000.0},
        ])
        max_date = date(2024, 6, 1)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=7)

        daklak = result["provinces"][0]
        assert daklak["price_change_percent"] is None


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st


# Feature: unit-tests, Property 5: Price service days parameter clamping
class TestDaysClampingProperty:
    """**Validates: Requirements 5.1, 5.2**"""

    @pytest.mark.property
    @settings(max_examples=100)
    @given(days=st.one_of(
        st.integers(max_value=0),   # below 1
        st.integers(min_value=31),  # above 30
    ))
    def test_days_outside_range_are_clamped(self, days):
        """For any integer outside [1, 30], effective days is clamped to [1, 30]."""
        engine = _make_mock_engine(max_date_value=None)

        result = get_recent_prices(engine, days=days)

        assert 1 <= result["days"] <= 30
        if days > 30:
            assert result["days"] == 30
        elif days < 1:
            assert result["days"] == 1


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


@pytest.mark.property
class TestPriceAggregationCorrectnessProperty:
    """Property 6: Price aggregation correctness.

    For any set of price records grouped by province with more than one record,
    the service SHALL compute:
    - current_price = last chronological price
    - price_change = last - first
    - price_change_percent = (price_change / first_price) * 100 rounded to 2dp
      (or None when first price is 0)

    **Validates: Requirements 5.4, 5.5, 5.8**
    """

    # Feature: unit-tests, Property 6: Price aggregation correctness

    from hypothesis import given, settings, strategies as st, assume

    @given(
        prices=st.lists(
            st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20,
        )
    )
    @settings(max_examples=100)
    def test_price_aggregation_with_positive_first_price(self, prices):
        """When first price > 0, current_price, price_change, and price_change_percent are correct."""
        from hypothesis import assume

        assume(prices[0] > 0)

        base = date(2024, 1, 1)
        rows = [
            {"region": "DakLak", "date": base + timedelta(days=i), "price_vnd_per_kg": p}
            for i, p in enumerate(prices)
        ]
        df = pd.DataFrame(rows)

        max_date = base + timedelta(days=len(prices) - 1)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=30)

        assert result["success"] is True
        assert result["count"] == 1

        province = result["provinces"][0]

        # current_price = last chronological price
        expected_current = prices[-1]
        assert province["current_price"] == expected_current

        # price_change = last - first
        expected_change = prices[-1] - prices[0]
        assert province["price_change"] == expected_change

        # price_change_percent = (change / first) * 100 rounded to 2dp
        expected_percent = round(expected_change / prices[0] * 100, 2)
        assert province["price_change_percent"] == expected_percent

    @given(
        prices=st.lists(
            st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20,
        )
    )
    @settings(max_examples=100)
    def test_price_aggregation_with_zero_first_price(self, prices):
        """When first price is 0, price_change_percent should be None."""
        # Force first price to 0
        prices_with_zero_first = [0.0] + prices[1:]

        base = date(2024, 1, 1)
        rows = [
            {"region": "DakLak", "date": base + timedelta(days=i), "price_vnd_per_kg": p}
            for i, p in enumerate(prices_with_zero_first)
        ]
        df = pd.DataFrame(rows)

        max_date = base + timedelta(days=len(prices_with_zero_first) - 1)
        engine = _make_mock_engine(max_date_value=max_date)

        with patch("app.services.price_service.pd.read_sql", return_value=df):
            result = get_recent_prices(engine, days=30)

        province = result["provinces"][0]

        # current_price = last chronological price
        assert province["current_price"] == prices_with_zero_first[-1]

        # price_change = last - first (first is 0)
        expected_change = prices_with_zero_first[-1] - 0.0
        assert province["price_change"] == expected_change

        # price_change_percent = None when first is 0
        assert province["price_change_percent"] is None
