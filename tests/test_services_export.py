"""Unit tests for app.services.export_service module.

Tests cover:
- get_export_overview table fallback logic
- get_export_countries aggregation, limit, and "others" computation
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import Engine


# ---------------------------------------------------------------------------
# get_export_overview tests
# ---------------------------------------------------------------------------


class TestGetExportOverview:
    """Tests for get_export_overview function."""

    @patch("app.services.export_service.pd.read_sql")
    @patch("app.services.export_service.table_exists")
    def test_queries_export_performance_when_table_exists(
        self, mock_table_exists, mock_read_sql, mock_engine
    ):
        """When export_performance table exists, queries that table."""
        engine, conn = mock_engine
        mock_table_exists.return_value = True
        mock_read_sql.return_value = pd.DataFrame(
            {
                "year": [2020, 2021],
                "area_thousand_ha": [700.0, 710.0],
                "production_tons": [1_800_000.0, 1_900_000.0],
                "export_tons": [1_500_000.0, 1_600_000.0],
                "export_value_million_usd": [3000.0, 3200.0],
                "price_world_usd_per_ton": [1500.0, 1600.0],
                "price_vn_usd_per_ton": [1400.0, 1500.0],
            }
        )

        from app.services.export_service import get_export_overview

        result = get_export_overview(engine)

        mock_table_exists.assert_called_once_with(engine, "export_performance")
        assert result["success"] is True
        assert result["count"] == 2
        assert result["years"] == [2020, 2021]
        assert "export_value" in result["stats"]
        assert "world_price" in result["stats"]
        assert "vn_price" in result["stats"]
        assert "export_volume" in result["stats"]
        assert result["metadata"]["interpolated"] is True

        # Verify the SQL query references export_performance
        call_args = mock_read_sql.call_args
        query_text = str(call_args[0][0])
        assert "export_performance" in query_text

    @patch("app.services.export_service.pd.read_sql")
    @patch("app.services.export_service.table_exists")
    def test_falls_back_to_join_when_table_missing(
        self, mock_table_exists, mock_read_sql, mock_engine
    ):
        """When export_performance table doesn't exist, falls back to JOIN query."""
        engine, conn = mock_engine
        mock_table_exists.return_value = False
        mock_read_sql.return_value = pd.DataFrame(
            {
                "year": [2020, 2021],
                "area_thousand_ha": [700.0, 710.0],
                "production_tons": [1_800_000.0, 1_900_000.0],
                "export_tons": [1_500_000.0, 1_600_000.0],
                "export_value_million_usd": [3000.0, 3200.0],
                "price_world_usd_per_ton": [1500.0, 1600.0],
                "price_vn_usd_per_ton": [1400.0, 1500.0],
            }
        )

        from app.services.export_service import get_export_overview

        result = get_export_overview(engine)

        mock_table_exists.assert_called_once_with(engine, "export_performance")
        assert result["success"] is True
        assert result["count"] == 2

        # Verify the SQL query uses JOIN
        call_args = mock_read_sql.call_args
        query_text = str(call_args[0][0])
        assert "coffee_export" in query_text
        assert "JOIN" in query_text.upper()


# ---------------------------------------------------------------------------
# get_export_countries tests
# ---------------------------------------------------------------------------


class TestGetExportCountries:
    """Tests for get_export_countries function."""

    def _make_countries_df(self, n: int = 12) -> pd.DataFrame:
        """Helper to create a sample countries DataFrame."""
        countries = [f"Country_{i}" for i in range(1, n + 1)]
        volumes = [1000.0 * (n - i + 1) for i in range(1, n + 1)]  # descending
        values = [v * 0.5 for v in volumes]
        return pd.DataFrame(
            {
                "country": countries,
                "export_volume": volumes,
                "export_value_1000usd": values,
            }
        )

    @patch("app.services.export_service.pd.read_sql")
    def test_without_year_uses_max_available_year(self, mock_read_sql, mock_engine):
        """When year is not provided, uses max available year from DB."""
        engine, conn = mock_engine

        # Mock the scalar call for max year
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2023
        conn.execute.return_value = mock_result

        mock_read_sql.return_value = self._make_countries_df(5)

        from app.services.export_service import get_export_countries

        result = get_export_countries(engine, year=None, limit=9)

        assert result["success"] is True
        assert result["year"] == 2023
        assert result["metadata"]["max_available_year"] == 2023

    @patch("app.services.export_service.pd.read_sql")
    def test_with_limit_returns_at_most_n_countries_ordered_by_volume(
        self, mock_read_sql, mock_engine
    ):
        """With limit, returns at most N countries ordered by volume desc with percentage."""
        engine, conn = mock_engine

        mock_result = MagicMock()
        mock_result.scalar.return_value = 2022
        conn.execute.return_value = mock_result

        df = self._make_countries_df(12)
        mock_read_sql.return_value = df

        from app.services.export_service import get_export_countries

        result = get_export_countries(engine, year=2022, limit=5)

        assert result["success"] is True
        assert len(result["countries"]) == 5
        assert result["count"] == 5

        # Verify ordering by volume descending
        volumes = [c["volume"] for c in result["countries"]]
        assert volumes == sorted(volumes, reverse=True)

        # Verify each country has a percentage
        for country in result["countries"]:
            assert "percentage" in country
            assert isinstance(country["percentage"], float)

    @patch("app.services.export_service.pd.read_sql")
    def test_others_entry_computation(self, mock_read_sql, mock_engine):
        """When more countries exist beyond limit, others entry is computed correctly."""
        engine, conn = mock_engine

        mock_result = MagicMock()
        mock_result.scalar.return_value = 2022
        conn.execute.return_value = mock_result

        # 10 countries with known volumes
        df = self._make_countries_df(10)
        mock_read_sql.return_value = df

        from app.services.export_service import get_export_countries

        result = get_export_countries(engine, year=2022, limit=5)

        total_volume = float(df["export_volume"].sum())
        top_5_volume = float(df.head(5)["export_volume"].sum())
        expected_others_volume = total_volume - top_5_volume

        assert result["others"]["volume"] == expected_others_volume
        expected_others_pct = round(expected_others_volume / total_volume * 100, 1)
        assert result["others"]["percentage"] == expected_others_pct
        assert result["total"] == total_volume

    @patch("app.services.export_service.pd.read_sql")
    def test_empty_query_result(self, mock_read_sql, mock_engine):
        """Empty query result returns success=True, empty countries, others volume=0, total=0."""
        engine, conn = mock_engine

        mock_result = MagicMock()
        mock_result.scalar.return_value = 2022
        conn.execute.return_value = mock_result

        mock_read_sql.return_value = pd.DataFrame(
            columns=["country", "export_volume", "export_value_1000usd"]
        )

        from app.services.export_service import get_export_countries

        result = get_export_countries(engine, year=2022, limit=9)

        assert result["success"] is True
        assert result["countries"] == []
        assert result["others"]["volume"] == 0
        assert result["others"]["percentage"] == 0
        assert result["total"] == 0
        assert result["count"] == 0

    @patch("app.services.export_service.pd.read_sql")
    def test_limit_gte_total_countries_returns_others_zero(
        self, mock_read_sql, mock_engine
    ):
        """When limit >= total countries, others has volume=0.0 and percentage=0."""
        engine, conn = mock_engine

        mock_result = MagicMock()
        mock_result.scalar.return_value = 2022
        conn.execute.return_value = mock_result

        # Only 3 countries, limit is 5
        df = self._make_countries_df(3)
        mock_read_sql.return_value = df

        from app.services.export_service import get_export_countries

        result = get_export_countries(engine, year=2022, limit=5)

        assert result["success"] is True
        assert len(result["countries"]) == 3
        assert result["others"]["volume"] == 0.0
        assert result["others"]["percentage"] == 0


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.pandas import column, data_frames


@pytest.mark.property
class TestExportCountriesPartitioningProperty:
    """Property 12: Export countries partitioning.

    Feature: unit-tests, Property 12: Export countries partitioning
    Validates: Requirements 8.4, 8.5
    """

    @given(
        volumes=st.lists(
            st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=20,
        ),
        limit=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_partition_volumes_sum_equals_total(self, volumes, limit):
        """Sum of top-N volumes + others.volume = total volume.

        **Validates: Requirements 8.4, 8.5**
        """
        # Create mock engine inline (avoids fixture-scoped issue with Hypothesis)
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=conn)
        ctx.__exit__ = MagicMock(return_value=False)
        engine.connect.return_value = ctx

        # Build a DataFrame with generated volumes
        n = len(volumes)
        countries = [f"Country_{i}" for i in range(n)]
        values = [v * 0.5 for v in volumes]
        df = pd.DataFrame(
            {
                "country": countries,
                "export_volume": sorted(volumes, reverse=True),  # pre-sorted desc
                "export_value_1000usd": values,
            }
        )

        # Mock the scalar call for max year
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2023
        conn.execute.return_value = mock_result

        with patch("app.services.export_service.pd.read_sql", return_value=df):
            from app.services.export_service import get_export_countries

            result = get_export_countries(engine, year=2023, limit=limit)

        # --- Verify partitioning invariant ---
        total = result["total"]
        top_volumes_sum = sum(c["volume"] for c in result["countries"])
        others_volume = result["others"]["volume"]

        # Sum of top-N + others must equal total (within floating point tolerance)
        # Use relative tolerance for large numbers where absolute error grows
        abs_diff = abs((top_volumes_sum + others_volume) - total)
        rel_tol = 1e-9 * total if total > 0 else 1e-6
        assert abs_diff < max(rel_tol, 1e-6), (
            f"Partition mismatch: top={top_volumes_sum}, others={others_volume}, "
            f"total={total}, diff={abs_diff}"
        )

        # --- Verify percentage computation ---
        if total > 0:
            for country in result["countries"]:
                expected_pct = round(country["volume"] / total * 100, 1)
                assert country["percentage"] == expected_pct, (
                    f"Percentage mismatch for {country['name']}: "
                    f"got {country['percentage']}, expected {expected_pct}"
                )

            # Verify others percentage
            if others_volume > 0:
                expected_others_pct = round(others_volume / total * 100, 1)
                assert result["others"]["percentage"] == expected_others_pct, (
                    f"Others percentage mismatch: "
                    f"got {result['others']['percentage']}, expected {expected_others_pct}"
                )
