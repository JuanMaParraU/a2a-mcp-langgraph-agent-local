"""Tests for the /metrics GET endpoint in o1_server.py."""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Ensure the orchestrator module is importable
sys.path.insert(0, os.path.dirname(__file__))

# Mock heavy dependencies before importing o1_server
sys.modules["a2a"] = MagicMock()
sys.modules["a2a.server"] = MagicMock()
sys.modules["a2a.server.apps"] = MagicMock()
sys.modules["a2a.server.request_handlers"] = MagicMock()
sys.modules["a2a.server.tasks"] = MagicMock()
sys.modules["a2a.types"] = MagicMock()
sys.modules["o2_executor"] = MagicMock()
sys.modules["metrics_middleware"] = MagicMock()

from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route

from o1_server import metrics_endpoint, _cors_headers, CORS_ORIGIN


@pytest.fixture
def app():
    """Create a minimal Starlette app with the /metrics route."""
    return Starlette(
        routes=[Route("/metrics", endpoint=metrics_endpoint, methods=["GET", "OPTIONS"])]
    )


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestMetricsEndpointSuccess:
    """Tests for successful /metrics GET responses."""

    def test_returns_200_with_metrics_summary(self, client):
        """GET /metrics returns 200 with MetricsCollector summary data."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        # Should contain standard MetricsCollector fields
        assert "requests_total" in data
        assert "errors_total" in data
        assert "tokens_total" in data
        assert "tool_calls" in data
        assert "avg_latency" in data

    def test_response_includes_timestamp_field(self, client):
        """GET /metrics response includes an ISO 8601 timestamp field."""
        response = client.get("/metrics")
        data = response.json()
        assert "timestamp" in data
        # Verify ISO 8601 format ending with Z
        ts = data["timestamp"]
        assert ts.endswith("Z")
        # Should be parseable as a datetime
        # Format: 2024-01-15T10:30:00.000Z
        ts_without_z = ts[:-1]
        parsed = datetime.fromisoformat(ts_without_z)
        assert parsed is not None

    def test_response_content_type_is_json(self, client):
        """GET /metrics returns application/json content type."""
        response = client.get("/metrics")
        assert "application/json" in response.headers["content-type"]


class TestMetricsEndpointCORS:
    """Tests for CORS headers on /metrics."""

    def test_get_includes_cors_headers(self, client):
        """GET /metrics response includes CORS headers."""
        response = client.get("/metrics")
        assert response.headers["access-control-allow-origin"] == CORS_ORIGIN
        assert "GET" in response.headers["access-control-allow-methods"]
        assert "Content-Type" in response.headers["access-control-allow-headers"]

    def test_options_preflight_returns_200(self, client):
        """OPTIONS /metrics returns 200 for CORS preflight."""
        response = client.options("/metrics")
        assert response.status_code == 200

    def test_options_preflight_includes_cors_headers(self, client):
        """OPTIONS /metrics includes proper CORS headers."""
        response = client.options("/metrics")
        assert response.headers["access-control-allow-origin"] == CORS_ORIGIN
        assert "GET" in response.headers["access-control-allow-methods"]
        assert "OPTIONS" in response.headers["access-control-allow-methods"]
        assert "Content-Type" in response.headers["access-control-allow-headers"]

    def test_cors_origin_defaults_to_localhost_3000(self):
        """CORS_ORIGIN defaults to http://localhost:3000."""
        # The default is set at module level
        assert CORS_ORIGIN == os.environ.get("CORS_ORIGIN", "http://localhost:3000")


class TestMetricsEndpointError:
    """Tests for error handling when MetricsCollector is unreachable."""

    def test_returns_503_when_metrics_collector_raises(self, client):
        """GET /metrics returns 503 when MetricsCollector raises an exception."""
        with patch("o1_server.MetricsCollector") as mock_collector:
            mock_instance = MagicMock()
            mock_instance.summary.side_effect = RuntimeError("Connection failed")
            mock_collector.get_instance.return_value = mock_instance

            response = client.get("/metrics")
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert data["error"] == "Metrics service temporarily unavailable"

    def test_503_response_includes_cors_headers(self, client):
        """503 error response still includes CORS headers."""
        with patch("o1_server.MetricsCollector") as mock_collector:
            mock_instance = MagicMock()
            mock_instance.summary.side_effect = RuntimeError("Connection failed")
            mock_collector.get_instance.return_value = mock_instance

            response = client.get("/metrics")
            assert response.headers["access-control-allow-origin"] == CORS_ORIGIN
