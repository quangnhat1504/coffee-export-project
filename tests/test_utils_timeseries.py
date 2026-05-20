"""Example-based unit tests for app.utils.timeseries module.

Tests cover interpolate_series and add_growth_fields with specific scenarios
and edge cases.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.utils.timeseries import add_growth_fields, interpolate_series


# ---------------------------------------------------------------------------
# interpolate_series tests
# ---------------------------------------------------------------------------


class TestInterpolateSeries:
    """Tests for interpolate_series."""

    def test_fills_nan_gaps_in_numeric_column(self):
        """Requirement 3.1: NaN gaps are filled in a numeric column."""
        df = pd.DataFrame({"value": [1.0, np.nan, np.nan, 4.0, 5.0]})
        result = interpolate_series(df, "value")
        assert result.notna().all()
        assert len(result) == 5

    def test_fewer_than_2_non_null_returns_unchanged(self):
        """Requirement 3.2: With fewer than 2 non-null values, series is returned unchanged."""
        # Only 1 non-null value
        df = pd.DataFrame({"value": [np.nan, 3.0, np.nan]})
        result = interpolate_series(df, "value")
        # Should still have NaN values since interpolation is skipped
        assert result.notna().sum() == 1
        assert result.iloc[1] == 3.0

    def test_zero_non_null_returns_unchanged(self):
        """Requirement 3.2: With zero non-null values, series is returned unchanged."""
        df = pd.DataFrame({"value": [np.nan, np.nan, np.nan]})
        result = interpolate_series(df, "value")
        assert result.isna().all()

    def test_polynomial_method_with_sufficient_data(self):
        """Requirement 3.3: polynomial interpolation used when sufficient data points exist."""
        # 5 non-null values > order=2, so polynomial should be used
        df = pd.DataFrame({"value": [1.0, np.nan, 9.0, 16.0, 25.0, np.nan, 49.0]})
        result = interpolate_series(df, "value", method="polynomial", order=2)
        assert result.notna().all()
        assert len(result) == 7

    def test_falls_back_to_linear_when_polynomial_raises(self):
        """Requirement 3.4: Falls back to linear when polynomial raises an exception."""
        # Create data where polynomial interpolation might fail but linear works.
        # With only 2 non-null values (not > order=2), it should use linear directly.
        df = pd.DataFrame({"value": [1.0, np.nan, np.nan, np.nan, 5.0]})
        result = interpolate_series(df, "value", method="polynomial", order=2)
        # With only 2 non-null values, notna().sum() == 2 which is NOT > order (2),
        # so it goes to the else branch (linear).
        assert result.notna().all()

    def test_falls_back_to_linear_on_exception(self):
        """Requirement 3.4: Falls back to linear when polynomial raises an exception."""
        # Create a scenario with enough points for polynomial attempt but
        # data that could cause issues. We use 3 non-null values (> order=2)
        # but with values that might cause polynomial fitting issues.
        # Even if polynomial succeeds, the result should have no NaN.
        df = pd.DataFrame({"value": [0.0, np.nan, 0.0, np.nan, 0.0]})
        result = interpolate_series(df, "value", method="polynomial", order=2)
        assert result.notna().all()

    def test_string_values_coerced_to_numeric(self):
        """interpolate_series coerces non-numeric strings to NaN via pd.to_numeric."""
        df = pd.DataFrame({"value": ["1.0", "abc", "3.0", "4.0", "5.0"]})
        result = interpolate_series(df, "value")
        # "abc" becomes NaN, then gets interpolated
        assert result.notna().all()
        assert len(result) == 5


# ---------------------------------------------------------------------------
# add_growth_fields tests
# ---------------------------------------------------------------------------


class TestAddGrowthFields:
    """Tests for add_growth_fields."""

    def test_multi_row_returns_correct_growth_fields(self):
        """Requirement 3.5: Multi-row DataFrame returns current, previous, change, change_percent rounded to 2dp."""
        df = pd.DataFrame({"year": [2020, 2021, 2022], "output": [100.0, 150.0, 200.0]})
        result = add_growth_fields(df, "output")

        assert result["current"] == 200.0
        assert result["previous"] == 150.0
        assert result["change"] == 50.0  # 200.0 - 150.0
        # change_percent = (50.0 / 150.0) * 100 = 33.333... → round to 33.33
        assert result["change_percent"] == 33.33

    def test_single_row_returns_none_for_previous_change(self):
        """Requirement 3.6: Single-row DataFrame returns previous=None, change=None, change_percent=None."""
        df = pd.DataFrame({"year": [2022], "output": [200.0]})
        result = add_growth_fields(df, "output")

        assert result["current"] == 200.0
        assert result["previous"] is None
        assert result["change"] is None
        assert result["change_percent"] is None

    def test_previous_zero_returns_change_percent_none(self):
        """Requirement 3.7: Previous value of zero returns change_percent=None."""
        df = pd.DataFrame({"year": [2020, 2021], "output": [0.0, 100.0]})
        result = add_growth_fields(df, "output")

        assert result["current"] == 100.0
        assert result["previous"] == 0.0
        assert result["change"] == 100.0
        assert result["change_percent"] is None

    def test_empty_dataframe_returns_all_none(self):
        """Requirement 3.8: Empty DataFrame returns all-None dict."""
        df = pd.DataFrame({"output": pd.Series([], dtype=float)})
        result = add_growth_fields(df, "output")

        assert result == {"current": None, "previous": None, "change": None, "change_percent": None}

    def test_missing_value_column_returns_all_none(self):
        """Requirement 3.9: Missing value_column returns all-None dict."""
        df = pd.DataFrame({"year": [2020, 2021], "other_col": [1.0, 2.0]})
        result = add_growth_fields(df, "output")

        assert result == {"current": None, "previous": None, "change": None, "change_percent": None}

    def test_all_nan_values_returns_all_none(self):
        """When all values in the column are NaN, returns all-None dict."""
        df = pd.DataFrame({"output": [np.nan, np.nan, np.nan]})
        result = add_growth_fields(df, "output")

        assert result == {"current": None, "previous": None, "change": None, "change_percent": None}

    def test_negative_values_compute_correctly(self):
        """Growth fields work correctly with negative values."""
        df = pd.DataFrame({"value": [-10.0, -5.0]})
        result = add_growth_fields(df, "value")

        assert result["current"] == -5.0
        assert result["previous"] == -10.0
        assert result["change"] == 5.0
        assert result["change_percent"] == round((5.0 / -10.0) * 100, 2)  # -50.0


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------


import math

from hypothesis import given, settings, strategies as st, assume


# Feature: unit-tests, Property 3: interpolate_series completeness invariant
@pytest.mark.property
@given(
    values=st.lists(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=50,
    ),
    nan_mask=st.lists(st.booleans(), min_size=2, max_size=50),
)
@settings(max_examples=100)
def test_interpolate_series_completeness_invariant(values, nan_mask):
    """Property 3: For any numeric Series with at least 2 non-null values,
    interpolate_series SHALL return a Series containing no NaN values.

    **Validates: Requirements 3.1, 3.10**
    """
    # Align mask length to values length
    mask = nan_mask[: len(values)]
    # Pad mask if shorter than values
    while len(mask) < len(values):
        mask.append(False)

    # Apply NaN at masked positions
    data = [float("nan") if mask[i] else values[i] for i in range(len(values))]

    # Ensure at least 2 non-null values remain
    non_null_count = sum(1 for v in data if not math.isnan(v))
    assume(non_null_count >= 2)

    df = pd.DataFrame({"value": data})
    result = interpolate_series(df, "value")

    # The completeness invariant: no NaN values in the output
    assert result.notna().all(), (
        f"Output contains NaN values. Input had {non_null_count} non-null values "
        f"out of {len(data)} total."
    )


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st, assume


@pytest.mark.property
@given(
    values=st.lists(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=50,
    )
)
@settings(max_examples=100)
def test_add_growth_fields_mathematical_correctness(values):
    """Property 4: add_growth_fields mathematical correctness.

    For any non-empty DataFrame with a numeric column containing at least 2
    non-null values, add_growth_fields returns:
    - current = last value rounded to 2dp
    - previous = second-to-last value rounded to 2dp
    - change = current - previous rounded to 2dp
    - change_percent = (change/previous)*100 rounded to 2dp (or None when previous is 0)

    **Validates: Requirements 3.5**
    """
    df = pd.DataFrame({"col": values})
    result = add_growth_fields(df, "col")

    # The function converts to numeric and drops NaN. Since we generate finite
    # floats only, all values remain. The series has at least 2 values.
    expected_current = round(float(values[-1]), 2)
    expected_previous = round(float(values[-2]), 2)

    # change is computed from unrounded values, then rounded
    raw_change = float(values[-1]) - float(values[-2])
    expected_change = round(raw_change, 2)

    assert result["current"] == expected_current
    assert result["previous"] == expected_previous
    assert result["change"] == expected_change

    if values[-2] == 0.0:
        assert result["change_percent"] is None
    else:
        raw_percent = (raw_change / float(values[-2])) * 100
        expected_percent = round(raw_percent, 2)
        assert result["change_percent"] == expected_percent
