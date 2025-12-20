"""
Unit tests for the API routes.
"""

from unittest.mock import patch

from app.models.port import ProcessKillResponse


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_healthy(self, test_client):
        """Test that health check returns healthy status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPortsEndpoint:
    """Tests for the /api/ports endpoint."""

    def test_get_ports_returns_list(self, test_client):
        """Test that /api/ports returns a list."""
        response = test_client.get("/api/ports")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_ports_with_filters(self, test_client, sample_port_info_list):
        """Test filtering ports."""
        with patch("app.services.port_scanner.port_scanner.get_all_connections") as mock:
            mock.return_value = sample_port_info_list
            response = test_client.get("/api/ports?protocol=TCP")
            assert response.status_code == 200


class TestStatsEndpoint:
    """Tests for the /api/stats endpoint."""

    def test_get_stats_returns_expected_fields(self, test_client):
        """Test that stats returns all expected fields."""
        response = test_client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tcp_ports" in data
        assert "total_udp_ports" in data


class TestKillEndpoint:
    """Tests for the /api/kill endpoints."""

    def test_kill_process_success(self, test_client):
        """Test the POST /api/kill endpoint."""
        mock_response = ProcessKillResponse(
            success=True, message="OK", pid=1234, process_name="test.exe"
        )
        with patch("app.services.process_manager.process_manager.kill_process") as mock:
            mock.return_value = mock_response
            response = test_client.post("/api/kill", json={"pid": 1234, "force": False})
            assert response.status_code == 200

    def test_kill_process_validation_error(self, test_client):
        """Test validation error for invalid PID."""
        response = test_client.post("/api/kill", json={"pid": -1})
        assert response.status_code == 422


class TestLogsEndpoint:
    """Tests for the /api/logs endpoint."""

    def test_get_logs_returns_list(self, test_client):
        """Test that /api/logs returns a list."""
        response = test_client.get("/api/logs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
