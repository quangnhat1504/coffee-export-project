"""Unit tests for app.services.production_service module.

Tests cover:
- get_production_overview with valid rows, empty result, and missing numeric values
- get_province_production with valid/invalid/empty province scenarios
- Derived field computation (output_million_tons, export_million_tons, yield_tons_per_ha)

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import Engine

from app.services.production_service import get_production_overview, get_province_production


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_engine():
    """Create a mock engine with connect() as a context manager."""
    engine = MagicMock(spec=Engine)
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    engine.connect.return_value = ctx
    return engine, conn


def _sample_production_df(rows: int = 5) -> pd.DataFrame:
    """Create a sample production DataFrame with valid data."""
    return pd.DataFrame({
        "year": list(range(2018, 2018 + rows)),
        "area_thousand_ha": [600.0 + i * 10 for i in range(rows)],
        "output_tons": [1_500_000.0 + i * 100_000 for i in range(rows)],
        "export_tons": [1_200_000.0 + i * 80_000 for i in range(rows)],
    })


def _sample_production_df_with_nulls(rows: int = 5) -> pd.DataFrame:
    """Create a sample production DataFrame with missing numeric values."""
    data = {
        "year": list(range(2018, 2018 + rows)),
        "area_thousand_ha": [600.0 + i * 10 for i in range(rows)],
        "output_tons": [1_500_000.0 + i * 100_000 for i in range(rows)],
        "export_tons": [1_200_000.0 + i * 80_000 for i in range(rows)],
    }
    # Introduce NaN in the middle
    if rows > 2:
        data["output_tons"][2] = None
        data["export_tons"][1] = None
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Tests: get_production_overview
# ---------------------------------------------------------------------------


class TestGetProductionOverview:
    """Tests for get_production_overview function."""

    @patch("pandas.read_sql")
    def test_valid_rows_returns_success(self, mock_read_sql):
        """Requirement 4.1: Valid rows return success=True with expected structure."""
        engine, _conn = _make_mock_engine()
        df = _sample_production_df(5)
        mock_read_sql.return_value = df

        result = get_production_overview(engine)

        assert result["success"] is True
        assert len(result["data"]) > 0
        assert result["count"] == 5
        assert result["years"] == [2018, 2019, 2020, 2021, 2022]
        # Stats keys
        assert "production" in result["stats"]
        assert "area" in result["stats"]
        assert "export" in result["stats"]
        assert "yield" in result["stats"]
        # Each stat has growth fields
        for key in ("production", "area", "export", "yield"):
            stat = result["stats"][key]
            assert "current" in stat
            assert "previous" in stat
            assert "change" in stat
            assert "change_percent" in stat
        # Metadata
        assert result["metadata"]["interpolated"] is True

    @patch("pandas.read_sql")
    def test_empty_result_returns_success_with_empty_data(self, mock_read_sql):
        """Requirement 4.2: Empty result returns success=True, empty data, count=0."""
        engine, _conn = _make_mock_engine()
        mock_read_sql.return_value = pd.DataFrame(
            columns=["year", "area_thousand_ha", "output_tons", "export_tons"]
        )

        result = get_production_overview(engine)

        assert result["success"] is True
        assert result["data"] == []
        assert result["count"] == 0
        assert result["stats"] == {}

    @patch("pandas.read_sql")
    def test_missing_numeric_values_applies_interpolation(self, mock_read_sql):
        """Requirement 4.7: Missing numeric values are interpolated before computing derived fields."""
        engine, _conn = _make_mock_engine()
        df = _sample_production_df_with_nulls(5)
        mock_read_sql.return_value = df

        result = get_production_overview(engine)

        assert result["success"] is True
        assert result["count"] == 5
        # All data rows should have non-None derived fields after interpolation
        for row in result["data"]:
            assert row["output_million_tons"] is not None
            assert row["export_million_tons"] is not None
            assert row["yield_tons_per_ha"] is not None


# ---------------------------------------------------------------------------
# Tests: get_province_production
# ---------------------------------------------------------------------------


class TestGetProvinceProduction:
    """Tests for get_province_production function."""

    @patch("pandas.read_sql")
    def test_valid_province_returns_success(self, mock_read_sql):
        """Requirement 4.3: Valid province returns success=True with correct province_display."""
        engine, _conn = _make_mock_engine()
        df = _sample_production_df(3)
        mock_read_sql.return_value = df

        result = get_province_production(engine, "DakLak")

        assert result["success"] is True
        assert result["province"] == "DakLak"
        assert result["province_display"] == "Dak Lak"
        assert result["count"] == 3
        assert len(result["data"]) == 3
        assert result["metadata"]["interpolated"] is True

    def test_invalid_province_returns_error(self):
        """Requirement 4.4: Invalid province returns success=False, status_code=400."""
        engine, _conn = _make_mock_engine()

        result = get_province_production(engine, "InvalidProvince")

        assert result["success"] is False
        assert result["status_code"] == 400
        assert "error" in result

    @patch("pandas.read_sql")
    def test_empty_query_result_returns_not_found(self, mock_read_sql):
        """Requirement 4.5: Empty query result returns success=False, status_code=404."""
        engine, _conn = _make_mock_engine()
        mock_read_sql.return_value = pd.DataFrame(
            columns=["year", "area_thousand_ha", "output_tons", "export_tons"]
        )

        result = get_province_production(engine, "DakLak")

        assert result["success"] is False
        assert result["status_code"] == 404
        assert "error" in result


# ---------------------------------------------------------------------------
# Tests: Derived field computation
# ---------------------------------------------------------------------------


class TestDerivedFieldComputation:
    """Tests for derived field computation (Requirement 4.6)."""

    @patch("pandas.read_sql")
    def test_output_million_tons(self, mock_read_sql):
        """output_million_tons = output_tons / 1_000_000 rounded to 2dp."""
        engine, _conn = _make_mock_engine()
        df = pd.DataFrame({
            "year": [2020],
            "area_thousand_ha": [700.0],
            "output_tons": [1_850_000.0],
            "export_tons": [1_400_000.0],
        })
        mock_read_sql.return_value = df

        result = get_production_overview(engine)

        row = result["data"][0]
        expected = round(1_850_000.0 / 1_000_000, 2)
        assert row["output_million_tons"] == expected

    @patch("pandas.read_sql")
    def test_export_million_tons(self, mock_read_sql):
        """export_million_tons = export_tons / 1_000_000 rounded to 2dp."""
        engine, _conn = _make_mock_engine()
        df = pd.DataFrame({
            "year": [2020],
            "area_thousand_ha": [700.0],
            "output_tons": [1_850_000.0],
            "export_tons": [1_400_000.0],
        })
        mock_read_sql.return_value = df

        result = get_production_overview(engine)

        row = result["data"][0]
        expected = round(1_400_000.0 / 1_000_000, 2)
        assert row["export_million_tons"] == expected

    @patch("pandas.read_sql")
    def test_yield_tons_per_ha(self, mock_read_sql):
        """yield_tons_per_ha = output_tons / (area_thousand_ha * 1000) rounded to 2dp."""
        engine, _conn = _make_mock_engine()
        df = pd.DataFrame({
            "year": [2020],
            "area_thousand_ha": [700.0],
            "output_tons": [1_850_000.0],
            "export_tons": [1_400_000.0],
        })
        mock_read_sql.return_value = df

        result = get_production_overview(engine)

        row = result["data"][0]
        expected = round(1_850_000.0 / (700.0 * 1000), 2)
        assert row["yield_tons_per_ha"] == expected

    @patch("pandas.read_sql")
    def test_derived_fields_in_province_production(self, mock_read_sql):
        """Derived fields are also computed in get_province_production."""
        engine, _conn = _make_mock_engine()
        df = pd.DataFrame({
            "year": [2020, 2021],
            "area_thousand_ha": [650.0, 680.0],
            "output_tons": [1_700_000.0, 1_800_000.0],
            "export_tons": [1_300_000.0, 1_350_000.0],
        })
        mock_read_sql.return_value = df

        result = get_province_production(engine, "GiaLai")

        assert result["success"] is True
        for row in result["data"]:
            assert "output_million_tons" in row
            assert "export_million_tons" in row
            assert "yield_tons_per_ha" in row
            # Verify computation for each row
            assert row["output_million_tons"] == round(row["output_tons"] / 1_000_000, 2)
            assert row["export_million_tons"] == round(row["export_tons"] / 1_000_000, 2)
            assert row["yield_tons_per_ha"] == round(
                row["output_tons"] / (row["area_thousand_ha"] * 1000), 2
            )


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st, assume
from unittest.mock import MagicMock
from sqlalchemy import Engine as _Engine


VALID_PROVINCES = {"DakLak", "GiaLai", "DakNong", "LamDong"}


class TestPropertyInvalidProvinceRejection:
    """Property 7: Invalid province rejection (production service).

    **Validates: Requirements 4.4**

    For any string not in {"DakLak", "GiaLai", "DakNong", "LamDong"},
    get_province_production SHALL return success=False and status_code=400.
    """

    @pytest.mark.property
    @given(province=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_invalid_province_returns_400(self, province: str):
        """Any province string not in the valid set is rejected with 400."""
        # Feature: unit-tests, Property 7: Invalid province rejection (production service)
        assume(province not in VALID_PROVINCES)

        engine = MagicMock(spec=_Engine)
        result = get_province_production(engine, province)

        assert result["success"] is False
        assert result["status_code"] == 400
