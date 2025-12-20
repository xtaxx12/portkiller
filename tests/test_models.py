"""
Unit tests for Pydantic data models.
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.port import (
    ActionLog,
    PortInfo,
    ProcessKillRequest,
    ProcessKillResponse,
    SystemStats,
)


class TestPortInfo:
    """Tests for the PortInfo model."""

    def test_valid_port_info(self):
        """Test creating a valid PortInfo."""
        port = PortInfo(
            port=8080, protocol="TCP", state="LISTEN",
            pid=1234, process_name="python.exe",
            local_address="0.0.0.0:8080", is_critical=False
        )
        assert port.port == 8080
        assert port.protocol == "TCP"

    def test_port_range_validation(self):
        """Test port number validation (0-65535)."""
        with pytest.raises(ValidationError):
            PortInfo(port=70000, protocol="TCP", state="LISTEN", local_address="0.0.0.0:70000")

    def test_protocol_literal(self):
        """Test protocol must be TCP or UDP."""
        with pytest.raises(ValidationError):
            PortInfo(port=80, protocol="INVALID", state="LISTEN", local_address="0.0.0.0:80")


class TestProcessKillRequest:
    """Tests for the ProcessKillRequest model."""

    def test_valid_request(self):
        """Test creating a valid kill request."""
        req = ProcessKillRequest(pid=1234, force=True)
        assert req.pid == 1234
        assert req.force is True

    def test_pid_must_be_positive(self):
        """Test PID must be greater than 0."""
        with pytest.raises(ValidationError):
            ProcessKillRequest(pid=0, force=False)

    def test_force_defaults_to_false(self):
        """Test force defaults to False."""
        req = ProcessKillRequest(pid=1234)
        assert req.force is False


class TestProcessKillResponse:
    """Tests for the ProcessKillResponse model."""

    def test_valid_response(self):
        """Test creating a valid response."""
        resp = ProcessKillResponse(success=True, message="OK", pid=1234, process_name="test.exe")
        assert resp.success is True
        assert resp.pid == 1234

    def test_timestamp_auto_generated(self):
        """Test timestamp is auto-generated."""
        resp = ProcessKillResponse(success=True, message="OK", pid=1234)
        assert resp.timestamp is not None
        assert isinstance(resp.timestamp, datetime)


class TestSystemStats:
    """Tests for the SystemStats model."""

    def test_valid_stats(self):
        """Test creating valid system stats."""
        stats = SystemStats(
            total_tcp_ports=10, total_udp_ports=5,
            listening_ports=8, established_connections=7, unique_processes=12
        )
        assert stats.total_tcp_ports == 10
        assert stats.unique_processes == 12


class TestActionLog:
    """Tests for the ActionLog model."""

    def test_valid_log(self):
        """Test creating a valid action log."""
        log = ActionLog(
            timestamp=datetime.now(), action="KILL",
            target_pid=1234, target_process="test.exe",
            target_port=8080, result="SUCCESS", user="admin"
        )
        assert log.action == "KILL"
        assert log.target_pid == 1234
