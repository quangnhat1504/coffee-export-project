"""Unit tests for app.services.weather_service.

Tests cover:
- Invalid province rejection
- Yearly aggregation query selection
- Specific year filtering
- Recent12 record limit
- Statistics computation for non-empty DataFrames
- Empty DataFrame handling

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import Engine

from app.services.weather_service import get_weather_for_province
from tests.conftest import make_weather_df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_engine_with_df(df: pd.DataFrame):
    """Create a mock engine that returns the given DataFrame from pd.read_sql."""
    engine = MagicMock(spec=Engine)
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    engine.connect.return_value = ctx
    return engine


# ---------------------------------------------------------------------------
# Tests: Invalid province
# ---------------------------------------------------------------------------


class TestInvalidProvince:
    """Requirement 6.1: Invalid province returns error."""

    def test_invalid_province_returns_failure(self):
        engine = MagicMock(spec=Engine)
        result = get_weather_for_province(engine, "InvalidProvince")

        assert result["success"] is False
        assert result["status_code"] == 400
        assert result["error"] == "Invalid province"

    def test_invalid_province_empty_string(self):
        engine = MagicMock(spec=Engine)
        result = get_weather_for_province(engine, "")

        assert result["success"] is False
        assert result["status_code"] == 400
        assert result["error"] == "Invalid province"


# ---------------------------------------------------------------------------
# Tests: Yearly aggregation query
# ---------------------------------------------------------------------------


class TestYearlyAggregation:
    """Requirement 6.2: aggregate='yearly' with year=None uses yearly query."""

    @patch("pandas.read_sql")
    def test_yearly_aggregate_executes_yearly_query(self, mock_read_sql):
        """When aggregate='yearly' and year=None, the yearly aggregation query is used."""
        yearly_df = pd.DataFrame({
            "year": [2020, 2021, 2022],
            "temperature_mean": [23.5, 24.0, 23.8],
            "precipitation_sum": [1500.0, 1600.0, 1550.0],
            "humidity_mean": [75.0, 76.0, 74.5],
        })
        mock_read_sql.return_value = yearly_df

        engine = _mock_engine_with_df(yearly_df)
        result = get_weather_for_province(engine, "DakLak", aggregate="yearly", year=None)

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["data"]) == 3

        # Verify the query text contains GROUP BY year (yearly aggregation)
        call_args = mock_read_sql.call_args
        query_text = str(call_args[0][0])
        assert "GROUP BY year" in query_text


# ---------------------------------------------------------------------------
# Tests: Specific year filtering
# ---------------------------------------------------------------------------


class TestSpecificYearFilter:
    """Requirement 6.3: Specific year filters data to that year only."""

    @patch("pandas.read_sql")
    def test_specific_year_filters_data(self, mock_read_sql):
        """When year is provided, the query filters to that year."""
        year_df = pd.DataFrame({
            "year": [2022] * 6,
            "month": [1, 2, 3, 4, 5, 6],
            "temperature_mean": [22.0, 22.5, 23.0, 24.0, 25.0, 26.0],
            "precipitation_sum": [80.0, 90.0, 120.0, 150.0, 200.0, 250.0],
            "humidity_mean": [72.0, 73.0, 74.0, 75.0, 76.0, 77.0],
        })
        mock_read_sql.return_value = year_df

        engine = _mock_engine_with_df(year_df)
        result = get_weather_for_province(engine, "GiaLai", aggregate="recent12", year=2022)

        assert result["success"] is True
        assert result["count"] == 6
        # All records should be for year 2022
        for record in result["data"]:
            assert record["year"] == 2022

        # Verify the query contains year parameter
        call_args = mock_read_sql.call_args
        query_text = str(call_args[0][0])
        assert "year = :year" in query_text

    @patch("pandas.read_sql")
    def test_specific_year_overrides_aggregate(self, mock_read_sql):
        """When year is provided, it takes precedence over aggregate parameter."""
        year_df = pd.DataFrame({
            "year": [2021] * 3,
            "month": [10, 11, 12],
            "temperature_mean": [24.0, 23.5, 22.0],
            "precipitation_sum": [180.0, 100.0, 60.0],
            "humidity_mean": [74.0, 72.0, 70.0],
        })
        mock_read_sql.return_value = year_df

        engine = _mock_engine_with_df(year_df)
        result = get_weather_for_province(engine, "DakNong", aggregate="yearly", year=2021)

        assert result["success"] is True
        # Should use the year-specific query, not the yearly aggregation
        call_args = mock_read_sql.call_args
        query_text = str(call_args[0][0])
        assert "year = :year" in query_text
        assert "GROUP BY year" not in query_text


# ---------------------------------------------------------------------------
# Tests: Recent12 aggregate
# ---------------------------------------------------------------------------


class TestRecent12Aggregate:
    """Requirement 6.4: aggregate='recent12' returns at most 12 monthly records."""

    @patch("pandas.read_sql")
    def test_recent12_returns_at_most_12_records(self, mock_read_sql):
        """The recent12 query limits results to 12 records."""
        df_12 = make_weather_df(months=12)
        mock_read_sql.return_value = df_12

        engine = _mock_engine_with_df(df_12)
        result = get_weather_for_province(engine, "LamDong", aggregate="recent12", year=None)

        assert result["success"] is True
        assert result["count"] <= 12

        # Verify the query contains LIMIT 12
        call_args = mock_read_sql.call_args
        query_text = str(call_args[0][0])
        assert "LIMIT 12" in query_text

    @patch("pandas.read_sql")
    def test_recent12_with_fewer_records(self, mock_read_sql):
        """When fewer than 12 records exist, all are returned."""
        df_6 = make_weather_df(months=6)
        mock_read_sql.return_value = df_6

        engine = _mock_engine_with_df(df_6)
        result = get_weather_for_province(engine, "DakLak", aggregate="recent12", year=None)

        assert result["success"] is True
        assert result["count"] == 6


# ---------------------------------------------------------------------------
# Tests: Statistics computation
# ---------------------------------------------------------------------------


class TestStatisticsComputation:
    """Requirement 6.5: Non-empty DataFrame computes stats."""

    @patch("pandas.read_sql")
    def test_nonempty_df_computes_stats(self, mock_read_sql):
        """Stats contain temperature, precipitation, humidity keys with current/avg/min/max."""
        df = make_weather_df(months=12)
        mock_read_sql.return_value = df

        engine = _mock_engine_with_df(df)
        result = get_weather_for_province(engine, "DakLak", aggregate="recent12")

        assert result["success"] is True
        stats = result["stats"]

        # Verify all three stat keys exist
        assert "temperature" in stats
        assert "precipitation" in stats
        assert "humidity" in stats

        # Verify each stat has the expected sub-keys
        for key in ("temperature", "precipitation", "humidity"):
            assert "current" in stats[key]
            assert "avg" in stats[key]
            assert "min" in stats[key]
            assert "max" in stats[key]

    @patch("pandas.read_sql")
    def test_stats_values_are_rounded_to_2dp(self, mock_read_sql):
        """All stat values are rounded to 2 decimal places."""
        df = pd.DataFrame({
            "year": [2023] * 4,
            "month": [1, 2, 3, 4],
            "temperature_mean": [22.123, 23.456, 24.789, 25.012],
            "precipitation_sum": [100.111, 200.222, 300.333, 400.444],
            "humidity_mean": [70.567, 71.891, 72.345, 73.678],
        })
        mock_read_sql.return_value = df

        engine = _mock_engine_with_df(df)
        result = get_weather_for_province(engine, "GiaLai", aggregate="recent12")

        stats = result["stats"]

        # current should be the last value rounded to 2dp
        assert stats["temperature"]["current"] == round(25.012, 2)
        assert stats["precipitation"]["current"] == round(400.444, 2)
        assert stats["humidity"]["current"] == round(73.678, 2)

        # avg should be mean rounded to 2dp
        expected_temp_avg = round((22.123 + 23.456 + 24.789 + 25.012) / 4, 2)
        assert stats["temperature"]["avg"] == expected_temp_avg

        # min/max
        assert stats["temperature"]["min"] == round(22.123, 2)
        assert stats["temperature"]["max"] == round(25.012, 2)

    @patch("pandas.read_sql")
    def test_stats_current_is_last_value(self, mock_read_sql):
        """The 'current' stat is the last value in the series."""
        df = pd.DataFrame({
            "year": [2023, 2023, 2023],
            "month": [1, 2, 3],
            "temperature_mean": [20.0, 22.0, 25.0],
            "precipitation_sum": [100.0, 150.0, 200.0],
            "humidity_mean": [70.0, 72.0, 75.0],
        })
        mock_read_sql.return_value = df

        engine = _mock_engine_with_df(df)
        result = get_weather_for_province(engine, "DakLak", aggregate="recent12")

        stats = result["stats"]
        assert stats["temperature"]["current"] == 25.0
        assert stats["precipitation"]["current"] == 200.0
        assert stats["humidity"]["current"] == 75.0


# ---------------------------------------------------------------------------
# Tests: Empty DataFrame
# ---------------------------------------------------------------------------


class TestEmptyDataFrame:
    """Requirement 6.6: Empty DataFrame returns success with empty data."""

    @patch("pandas.read_sql")
    def test_empty_df_returns_success_with_empty_data(self, mock_read_sql):
        """Empty query result returns success=True, empty data, count=0, empty stats."""
        empty_df = pd.DataFrame(columns=[
            "year", "month", "temperature_mean", "precipitation_sum", "humidity_mean"
        ])
        mock_read_sql.return_value = empty_df

        engine = _mock_engine_with_df(empty_df)
        result = get_weather_for_province(engine, "DakLak", aggregate="recent12")

        assert result["success"] is True
        assert result["data"] == []
        assert result["count"] == 0
        assert result["stats"] == {}

    @patch("pandas.read_sql")
    def test_empty_df_still_has_province_info(self, mock_read_sql):
        """Even with empty data, province and province_display are returned."""
        empty_df = pd.DataFrame(columns=[
            "year", "month", "temperature_mean", "precipitation_sum", "humidity_mean"
        ])
        mock_read_sql.return_value = empty_df

        engine = _mock_engine_with_df(empty_df)
        result = get_weather_for_province(engine, "LamDong", aggregate="yearly")

        assert result["success"] is True
        assert result["province"] == "LamDong"
        assert result["province_display"] == "Lam Dong"


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st


class TestWeatherStatsProperty:
    """Property 9: Weather statistics computation.

    For any non-empty DataFrame with numeric temperature_mean, precipitation_sum,
    and humidity_mean columns, the weather service statistics SHALL contain keys
    "temperature", "precipitation", and "humidity", each with current (last value),
    avg (mean), min, and max — all rounded to 2 decimal places.

    **Validates: Requirements 6.5**
    """

    # Feature: unit-tests, Property 9: Weather statistics computation

    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        temps=st.lists(
            st.floats(min_value=-50.0, max_value=60.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=24,
        ),
        precips=st.lists(
            st.floats(min_value=0.0, max_value=5000.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=24,
        ),
        humids=st.lists(
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=24,
        ),
    )
    @patch("pandas.read_sql")
    def test_stats_computation_property(self, mock_read_sql, temps, precips, humids):
        """Stats contain correct current/avg/min/max for any non-empty numeric data."""
        # Align all lists to the same length (minimum of the three)
        n = min(len(temps), len(precips), len(humids))
        temps = temps[:n]
        precips = precips[:n]
        humids = humids[:n]

        df = pd.DataFrame({
            "year": [2023] * n,
            "month": list(range(1, n + 1)),
            "temperature_mean": temps,
            "precipitation_sum": precips,
            "humidity_mean": humids,
        })
        mock_read_sql.return_value = df

        engine = _mock_engine_with_df(df)
        result = get_weather_for_province(engine, "DakLak", aggregate="recent12")

        assert result["success"] is True
        stats = result["stats"]

        # Verify all three stat keys exist
        assert "temperature" in stats
        assert "precipitation" in stats
        assert "humidity" in stats

        # Verify each stat has the expected sub-keys
        for key in ("temperature", "precipitation", "humidity"):
            assert "current" in stats[key]
            assert "avg" in stats[key]
            assert "min" in stats[key]
            assert "max" in stats[key]

        # Verify temperature stats match expected computation
        assert stats["temperature"]["current"] == round(float(temps[-1]), 2)
        assert stats["temperature"]["avg"] == round(float(sum(temps) / len(temps)), 2)
        assert stats["temperature"]["min"] == round(float(min(temps)), 2)
        assert stats["temperature"]["max"] == round(float(max(temps)), 2)

        # Verify precipitation stats match expected computation
        assert stats["precipitation"]["current"] == round(float(precips[-1]), 2)
        assert stats["precipitation"]["avg"] == round(float(sum(precips) / len(precips)), 2)
        assert stats["precipitation"]["min"] == round(float(min(precips)), 2)
        assert stats["precipitation"]["max"] == round(float(max(precips)), 2)

        # Verify humidity stats match expected computation
        assert stats["humidity"]["current"] == round(float(humids[-1]), 2)
        assert stats["humidity"]["avg"] == round(float(sum(humids) / len(humids)), 2)
        assert stats["humidity"]["min"] == round(float(min(humids)), 2)
        assert stats["humidity"]["max"] == round(float(max(humids)), 2)

        # Verify all values are rounded to 2 decimal places
        for key in ("temperature", "precipitation", "humidity"):
            for sub_key in ("current", "avg", "min", "max"):
                val = stats[key][sub_key]
                assert val == round(val, 2), f"{key}.{sub_key} not rounded to 2dp"


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st, assume
from unittest.mock import MagicMock
from sqlalchemy import Engine as _Engine


VALID_PROVINCES = {"DakLak", "GiaLai", "DakNong", "LamDong"}


class TestPropertyInvalidProvinceRejection:
    """Property 8: Invalid province rejection (weather service).

    **Validates: Requirements 6.1**

    For any string not in {"DakLak", "GiaLai", "DakNong", "LamDong"},
    get_weather_for_province SHALL return success=False, error="Invalid province",
    and status_code=400.
    """

    @pytest.mark.property
    @given(province=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_invalid_province_returns_400(self, province: str):
        """Any province string not in the valid set is rejected with 400."""
        # Feature: unit-tests, Property 8: Invalid province rejection (weather service)
        assume(province not in VALID_PROVINCES)

        engine = MagicMock(spec=_Engine)
        result = get_weather_for_province(engine, province)

        assert result["success"] is False
        assert result["error"] == "Invalid province"
        assert result["status_code"] == 400
