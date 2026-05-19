"""Tests for app/db.py — check_database, db_connection, table_exists.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Engine

from app.db import check_database, db_connection, table_exists


# ---------------------------------------------------------------------------
# check_database tests
# ---------------------------------------------------------------------------


class TestCheckDatabase:
    """Tests for the check_database function."""

    def test_engine_none_returns_false_with_message(self):
        """Requirement 11.1: engine=None → (False, 'Database engine is not configured')."""
        ok, msg = check_database(None)
        assert ok is False
        assert msg == "Database engine is not configured"

    def test_valid_engine_returns_true(self):
        """Requirement 11.2: valid engine responding to SELECT 1 → (True, 'Database connected')."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=conn)
        ctx.__exit__ = MagicMock(return_value=False)
        engine.connect.return_value = ctx

        ok, msg = check_database(engine)
        assert ok is True
        assert msg == "Database connected"
        conn.execute.assert_called_once()

    def test_engine_raising_exception_returns_false(self):
        """Requirement 11.3: engine raises exception → (False, str(exception))."""
        engine = MagicMock(spec=Engine)
        error = RuntimeError("Connection refused")
        engine.connect.side_effect = error

        ok, msg = check_database(engine)
        assert ok is False
        assert msg == str(error)


# ---------------------------------------------------------------------------
# db_connection tests
# ---------------------------------------------------------------------------


class TestDbConnection:
    """Tests for the db_connection context manager."""

    def test_commits_on_success(self):
        """Requirement 11.4: commits the transaction and closes connection on success."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        engine.connect.return_value = conn

        with db_connection(engine) as c:
            assert c is conn

        conn.commit.assert_called_once()
        conn.close.assert_called_once()

    def test_rollback_on_exception(self):
        """Requirement 11.5: rolls back on exception, closes connection, re-raises."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        engine.connect.return_value = conn

        with pytest.raises(ValueError, match="something went wrong"):
            with db_connection(engine) as c:
                raise ValueError("something went wrong")

        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
        conn.close.assert_called_once()

    def test_closes_connection_on_success(self):
        """Requirement 11.8: connection is closed regardless of success."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        engine.connect.return_value = conn

        with db_connection(engine):
            pass

        conn.close.assert_called_once()

    def test_closes_connection_on_failure(self):
        """Requirement 11.8: connection is closed regardless of failure."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        engine.connect.return_value = conn

        with pytest.raises(RuntimeError):
            with db_connection(engine):
                raise RuntimeError("oops")

        conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# table_exists tests
# ---------------------------------------------------------------------------


class TestTableExists:
    """Tests for the table_exists function."""

    def test_existing_table_returns_true(self):
        """Requirement 11.6: existing table → True."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=conn)
        ctx.__exit__ = MagicMock(return_value=False)
        engine.connect.return_value = ctx

        # Simulate a row being returned (table exists)
        result = MagicMock()
        result.first.return_value = ("my_table",)
        conn.execute.return_value = result

        assert table_exists(engine, "my_table") is True

    def test_non_existing_table_returns_false(self):
        """Requirement 11.7: non-existing table → False."""
        engine = MagicMock(spec=Engine)
        conn = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=conn)
        ctx.__exit__ = MagicMock(return_value=False)
        engine.connect.return_value = ctx

        # Simulate no row returned (table does not exist)
        result = MagicMock()
        result.first.return_value = None
        conn.execute.return_value = result

        assert table_exists(engine, "nonexistent_table") is False
