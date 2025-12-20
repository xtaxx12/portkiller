"""
End-to-End Integration Tests for PortKiller.
These tests verify the complete flow from API to services.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestE2EPortsFlow:
    """E2E tests for the ports listing flow."""

    def test_full_ports_listing_flow(self, client):
        """Test complete flow: get ports -> filter -> get stats."""
        # Step 1: Get all ports
        response = client.get("/api/ports")
        assert response.status_code == 200
        all_ports = response.json()
        assert isinstance(all_ports, list)

        # Step 2: Get stats
        response = client.get("/api/stats")
        assert response.status_code == 200
        stats = response.json()

        # Verify stats are reasonable (ports can change dynamically)
        assert stats["total_tcp_ports"] >= 0
        assert stats["total_udp_ports"] >= 0
        assert stats["listening_ports"] >= 0
        assert stats["established_connections"] >= 0
        assert stats["unique_processes"] >= 0

    def test_filter_chain_flow(self, client):
        """Test filtering with multiple criteria."""
        # Get TCP LISTEN ports
        response = client.get("/api/ports?protocol=TCP&state=LISTEN")
        assert response.status_code == 200
        filtered = response.json()

        # Verify all results match criteria
        for port in filtered:
            assert port["protocol"] == "TCP"
            assert port["state"] == "LISTEN"

    def test_search_by_process_flow(self, client):
        """Test searching ports by process name."""
        # First get all ports to find a process name
        response = client.get("/api/ports")
        all_ports = response.json()

        if all_ports:
            # Find a port with a process name
            port_with_process = next(
                (p for p in all_ports if p.get("process_name")), None
            )
            if port_with_process:
                process_name = port_with_process["process_name"][:4]  # Partial match

                # Search by that process
                response = client.get(f"/api/ports?process={process_name}")
                assert response.status_code == 200


class TestE2EProcessFlow:
    """E2E tests for process management flow."""

    def test_process_info_flow(self, client):
        """Test getting process information."""
        # Get ports to find a valid PID
        response = client.get("/api/ports")
        ports = response.json()

        valid_port = next((p for p in ports if p.get("pid")), None)
        if valid_port:
            pid = valid_port["pid"]

            # Get process details
            response = client.get(f"/api/process/{pid}")
            # Should be 200 or 403 (access denied) - both are valid
            assert response.status_code in [200, 403]

    def test_kill_critical_process_blocked(self, client):
        """Test that critical processes cannot be killed."""
        # Try to kill a known critical process (PID 4 is System on Windows)
        response = client.post("/api/kill/4?force=false")
        assert response.status_code == 200

        data = response.json()
        # Should either be blocked (critical) or not found
        if data.get("process_name"):
            assert data["success"] is False

    def test_kill_nonexistent_process(self, client):
        """Test killing a process that doesn't exist."""
        # Use a very high PID that likely doesn't exist
        response = client.post("/api/kill/999999?force=false")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert "no longer exists" in data["message"] or "not found" in data["message"].lower()


class TestE2ELogsFlow:
    """E2E tests for action logging flow."""

    def test_logs_after_actions(self, client):
        """Test that actions are logged."""
        # Perform an action (try to kill non-existent process)
        client.post("/api/kill/999998?force=false&port=9999")

        # Get logs
        response = client.get("/api/logs?limit=10")
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)

    def test_logs_contain_expected_fields(self, client):
        """Test that logs have expected structure."""
        response = client.get("/api/logs")
        logs = response.json()

        if logs:
            log = logs[0]
            assert "timestamp" in log
            assert "action" in log
            assert "result" in log


class TestE2EHealthCheck:
    """E2E tests for health monitoring."""

    def test_health_endpoint_always_available(self, client):
        """Test that health endpoint is always accessible."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_api_docs_available(self, client):
        """Test that API documentation is accessible."""
        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

        # OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/ports" in schema["paths"]


class TestE2EErrorHandling:
    """E2E tests for error handling."""

    def test_invalid_port_filter(self, client):
        """Test handling of invalid port filter."""
        response = client.get("/api/ports?port=invalid")
        assert response.status_code == 422

    def test_invalid_log_limit(self, client):
        """Test handling of invalid log limit."""
        response = client.get("/api/logs?limit=0")
        assert response.status_code == 422

        response = client.get("/api/logs?limit=10000")
        assert response.status_code == 422

    def test_kill_invalid_pid(self, client):
        """Test handling of invalid PID in kill request."""
        response = client.post("/api/kill", json={"pid": -1, "force": False})
        assert response.status_code == 422


class TestE2EConcurrency:
    """E2E tests for concurrent access."""

    def test_concurrent_port_requests(self, client):
        """Test multiple concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/api/ports")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
