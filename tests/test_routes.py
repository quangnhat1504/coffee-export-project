"""HTTP-level route handler tests.

Tests Flask route responses including status codes, JSON structure,
error handling, and Content-Type headers using the test client fixture.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""

from __future__ import annotations

from unittest.mock import patch


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_connected_db_returns_200(self, client, mock_engine):
        """Req 9.1: Connected DB returns 200, success=True, status=healthy, database.connected=True."""
        engine, conn = mock_engine

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["status"] == "healthy"
        assert data["api"] == "running"
        assert data["database"]["connected"] is True
        assert "timestamp" in data

    def test_health_unavailable_db_returns_503(self, app, client):
        """Req 9.2: Unavailable DB returns 503, status=degraded, database.connected=False."""
        # Set DB_ENGINE to None to simulate unavailable database
        app.config["DB_ENGINE"] = None

        response = client.get("/api/health")

        assert response.status_code == 503
        data = response.get_json()
        assert data["success"] is True
        assert data["status"] == "degraded"
        assert data["api"] == "running"
        assert data["database"]["connected"] is False
        assert "message" in data["database"]

    def test_health_content_type_json(self, client):
        """Req 9.7: Health endpoint returns Content-Type: application/json."""
        response = client.get("/api/health")

        assert "application/json" in response.content_type


class TestRequireEngine:
    """Tests for require_engine() returning 503 when DB_ENGINE is None."""

    def test_require_engine_none_returns_503(self, app, client):
        """Req 9.3: require_engine() with DB_ENGINE=None returns 503 with error."""
        app.config["DB_ENGINE"] = None

        # Use a route that calls require_engine (e.g., /api/production)
        response = client.get("/api/production")

        assert response.status_code == 503
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Database is not configured"


class TestValidRoute:
    """Tests for valid routes with successful service responses."""

    def test_valid_route_success_returns_200(self, client):
        """Req 9.4: Valid route with successful service returns 200, success=True, application/json."""
        with patch(
            "app.routes.production.get_production_overview"
        ) as mock_service:
            mock_service.return_value = {
                "success": True,
                "data": [],
                "count": 0,
                "years": [],
                "stats": {},
                "metadata": {"interpolated": True},
            }

            response = client.get("/api/production")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "application/json" in response.content_type


class TestNotFound:
    """Tests for non-existent API paths."""

    def test_nonexistent_api_path_returns_404(self, client):
        """Req 9.5: Non-existent /api/* path returns 404 with success=False."""
        response = client.get("/api/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_nonexistent_api_nested_path_returns_404(self, client):
        """Req 9.5: Non-existent nested /api/* path returns 404."""
        response = client.get("/api/some/deep/path")

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False


class TestUnhandledException:
    """Tests for unhandled exceptions in route handlers."""

    def test_unhandled_exception_returns_500(self, client):
        """Req 9.6: Unhandled exception in route returns 500 with success=False."""
        with patch(
            "app.routes.production.get_production_overview"
        ) as mock_service:
            mock_service.side_effect = RuntimeError("Unexpected failure")

            response = client.get("/api/production")

        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_unhandled_exception_content_type_json(self, client):
        """Req 9.7: Error responses also have Content-Type: application/json."""
        with patch(
            "app.routes.production.get_production_overview"
        ) as mock_service:
            mock_service.side_effect = ValueError("Something broke")

            response = client.get("/api/production")

        assert response.status_code == 500
        assert "application/json" in response.content_type


class TestContentTypeJson:
    """Tests that all /api/* responses have Content-Type: application/json."""

    def test_health_endpoint_json_content_type(self, client):
        """Req 9.7: /api/health returns application/json."""
        response = client.get("/api/health")
        assert "application/json" in response.content_type

    def test_404_endpoint_json_content_type(self, client):
        """Req 9.7: 404 /api/* returns application/json."""
        response = client.get("/api/does-not-exist")
        assert "application/json" in response.content_type

    def test_503_endpoint_json_content_type(self, app, client):
        """Req 9.7: 503 /api/* returns application/json."""
        app.config["DB_ENGINE"] = None
        response = client.get("/api/production")
        assert "application/json" in response.content_type

    def test_500_endpoint_json_content_type(self, client):
        """Req 9.7: 500 /api/* returns application/json."""
        with patch(
            "app.routes.production.get_production_overview"
        ) as mock_service:
            mock_service.side_effect = Exception("Boom")
            response = client.get("/api/production")
        assert "application/json" in response.content_type
