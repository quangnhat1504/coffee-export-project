"""Example-based unit tests for app.utils.serialization module.

Tests cover clean_value and records_from_frame with specific inputs and edge cases.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import pytest

from app.utils.serialization import clean_value, records_from_frame


# ---------------------------------------------------------------------------
# clean_value tests
# ---------------------------------------------------------------------------


class TestCleanValueNoneAndNaN:
    """Tests for None, NaN, and NaT handling."""

    def test_none_returns_none(self):
        assert clean_value(None) is None

    def test_float_nan_returns_none(self):
        assert clean_value(float("nan")) is None

    def test_pd_nat_returns_none(self):
        assert clean_value(pd.NaT) is None


class TestCleanValueDecimal:
    """Tests for Decimal conversion."""

    def test_decimal_returns_float(self):
        result = clean_value(Decimal("10.5"))
        assert result == 10.5
        assert isinstance(result, float)

    def test_decimal_zero_returns_float_zero(self):
        result = clean_value(Decimal("0"))
        assert result == 0.0
        assert isinstance(result, float)


class TestCleanValueDatetime:
    """Tests for datetime and date conversion."""

    def test_datetime_returns_iso_string_with_time(self):
        dt = datetime(2024, 3, 15, 10, 30, 45)
        result = clean_value(dt)
        assert result == "2024-03-15T10:30:45"
        assert isinstance(result, str)

    def test_date_returns_iso_date_only_string(self):
        d = date(2024, 3, 15)
        result = clean_value(d)
        assert result == "2024-03-15"
        assert isinstance(result, str)


class TestCleanValuePassthrough:
    """Tests for values that should pass through unchanged."""

    def test_int_returns_unchanged(self):
        assert clean_value(42) == 42
        assert isinstance(clean_value(42), int)

    def test_str_returns_unchanged(self):
        assert clean_value("hello") == "hello"
        assert isinstance(clean_value("hello"), str)

    def test_non_nan_float_returns_unchanged(self):
        assert clean_value(3.14) == 3.14
        assert isinstance(clean_value(3.14), float)


# ---------------------------------------------------------------------------
# records_from_frame tests
# ---------------------------------------------------------------------------


class TestRecordsFromFrame:
    """Tests for records_from_frame function."""

    def test_multi_row_dataframe_returns_list_of_dicts(self):
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob"],
                "score": [Decimal("95.5"), Decimal("87.0")],
                "date": [date(2024, 1, 1), date(2024, 1, 2)],
            }
        )
        result = records_from_frame(df)

        assert len(result) == 2
        assert result[0] == {"name": "Alice", "score": 95.5, "date": "2024-01-01"}
        assert result[1] == {"name": "Bob", "score": 87.0, "date": "2024-01-02"}

    def test_empty_dataframe_returns_empty_list(self):
        df = pd.DataFrame({"a": [], "b": []})
        result = records_from_frame(df)
        assert result == []

    def test_dataframe_with_nan_values_cleaned(self):
        df = pd.DataFrame(
            {
                "value": [1.0, float("nan"), 3.0],
                "label": ["x", "y", "z"],
            }
        )
        result = records_from_frame(df)

        assert len(result) == 3
        assert result[0] == {"value": 1.0, "label": "x"}
        assert result[1] == {"value": None, "label": "y"}
        assert result[2] == {"value": 3.0, "label": "z"}


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st


# Feature: unit-tests, Property 1: clean_value type conversion preserves semantic value
# **Validates: Requirements 2.4, 2.5, 2.6, 2.7**
class TestCleanValuePropertyTypeConversion:
    """Property: clean_value type conversion preserves semantic value.

    For any value of a supported type (Decimal, datetime, date, int, str,
    non-NaN float), clean_value SHALL return a JSON-safe equivalent that
    preserves the semantic meaning.
    """

    @pytest.mark.property
    @settings(max_examples=100)
    @given(value=st.decimals(allow_nan=False, allow_infinity=False))
    def test_decimal_converts_to_equivalent_float(self, value: Decimal):
        """Decimal → float with equivalent numeric value."""
        result = clean_value(value)
        assert isinstance(result, float)
        assert result == float(value)

    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        value=st.datetimes(
            min_value=datetime(1970, 1, 1), max_value=datetime(2100, 1, 1)
        )
    )
    def test_datetime_converts_to_isoformat_string(self, value: datetime):
        """datetime → isoformat string preserving date and time."""
        result = clean_value(value)
        assert isinstance(result, str)
        assert result == value.isoformat()

    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        value=st.dates(min_value=date(1970, 1, 1), max_value=date(2100, 1, 1))
    )
    def test_date_converts_to_isoformat_string(self, value: date):
        """date → isoformat string preserving date only."""
        result = clean_value(value)
        assert isinstance(result, str)
        assert result == value.isoformat()

    @pytest.mark.property
    @settings(max_examples=100)
    @given(value=st.integers(min_value=-1_000_000, max_value=1_000_000))
    def test_integer_passes_through_unchanged(self, value: int):
        """int → same int unchanged."""
        result = clean_value(value)
        assert result == value
        assert isinstance(result, int)

    @pytest.mark.property
    @settings(max_examples=100)
    @given(value=st.text(min_size=0, max_size=100))
    def test_string_passes_through_unchanged(self, value: str):
        """str → same str unchanged."""
        result = clean_value(value)
        assert result == value
        assert isinstance(result, str)

    @pytest.mark.property
    @settings(max_examples=100)
    @given(value=st.floats(allow_nan=False, allow_infinity=False))
    def test_non_nan_float_passes_through_unchanged(self, value: float):
        """non-NaN float → same float unchanged."""
        result = clean_value(value)
        assert result == value
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------

from hypothesis import given, settings, strategies as st

import numpy as np
import string


# Strategy: generate valid Python identifier column names
_column_names = st.text(
    alphabet=string.ascii_lowercase,
    min_size=1,
    max_size=8,
).map(lambda s: "c_" + s)  # prefix ensures valid identifier


# Strategy: generate cell values (numeric and string)
_cell_values = st.one_of(
    st.integers(min_value=-1_000_000, max_value=1_000_000),
    st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=20, alphabet=string.ascii_letters + string.digits),
)


@st.composite
def random_dataframes(draw):
    """Generate a random DataFrame with N rows and M columns."""
    n_rows = draw(st.integers(min_value=0, max_value=20))
    n_cols = draw(st.integers(min_value=1, max_value=6))

    # Generate unique column names
    cols = draw(
        st.lists(_column_names, min_size=n_cols, max_size=n_cols, unique=True)
    )

    # Generate data for each column
    data = {}
    for col in cols:
        data[col] = draw(st.lists(_cell_values, min_size=n_rows, max_size=n_rows))

    return pd.DataFrame(data)


# Feature: unit-tests, Property 2: records_from_frame preserves DataFrame structure
@pytest.mark.property
@given(df=random_dataframes())
@settings(max_examples=100)
def test_records_from_frame_preserves_structure(df: pd.DataFrame):
    """**Validates: Requirements 2.8, 2.10**

    For any valid DataFrame with N rows and M columns, records_from_frame
    returns a list of exactly N dictionaries, each containing exactly M keys
    matching the column names.
    """
    result = records_from_frame(df)

    n_rows = len(df)
    n_cols = len(df.columns)
    col_names = set(df.columns)

    # Output list length equals N (number of rows)
    assert len(result) == n_rows

    # Each dict has exactly M keys matching the column names
    for record in result:
        assert isinstance(record, dict)
        assert len(record) == n_cols
        assert set(record.keys()) == col_names
