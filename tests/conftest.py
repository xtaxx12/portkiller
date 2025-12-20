"""
Pytest Configuration and Fixtures for PortKiller tests.
"""
# Import the app and services
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import psutil
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.port import PortInfo
from app.services.port_scanner import PortScannerService
from app.services.process_manager import ProcessManagerService
from main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def port_scanner():
    """Create a fresh PortScannerService instance for testing."""
    return PortScannerService()


@pytest.fixture
def process_manager():
    """Create a fresh ProcessManagerService instance for testing."""
    with patch.object(ProcessManagerService, '_setup_logging'):
        manager = ProcessManagerService()
        manager.logger = Mock()
        manager.action_logs = []
        return manager


@pytest.fixture
def sample_port_info():
    """Sample PortInfo object for testing."""
    return PortInfo(
        port=8080,
        protocol="TCP",
        state="LISTEN",
        pid=1234,
        process_name="python.exe",
        local_address="0.0.0.0:8080",
        remote_address=None,
        is_critical=False
    )


@pytest.fixture
def sample_port_info_list():
    """List of sample PortInfo objects for testing."""
    return [
        PortInfo(
            port=80,
            protocol="TCP",
            state="LISTEN",
            pid=100,
            process_name="nginx",
            local_address="0.0.0.0:80",
            remote_address=None,
            is_critical=False
        ),
        PortInfo(
            port=443,
            protocol="TCP",
            state="ESTABLISHED",
            pid=100,
            process_name="nginx",
            local_address="0.0.0.0:443",
            remote_address="192.168.1.100:54321",
            is_critical=False
        ),
        PortInfo(
            port=22,
            protocol="TCP",
            state="LISTEN",
            pid=200,
            process_name="sshd",
            local_address="0.0.0.0:22",
            remote_address=None,
            is_critical=True
        ),
        PortInfo(
            port=53,
            protocol="UDP",
            state="NONE",
            pid=300,
            process_name="dnsmasq",
            local_address="0.0.0.0:53",
            remote_address=None,
            is_critical=True
        ),
        PortInfo(
            port=8080,
            protocol="TCP",
            state="LISTEN",
            pid=400,
            process_name="python.exe",
            local_address="127.0.0.1:8080",
            remote_address=None,
            is_critical=False
        ),
    ]


@pytest.fixture
def mock_tcp_connection():
    """Create a mock TCP connection object."""
    conn = Mock()
    conn.laddr = Mock()
    conn.laddr.ip = "0.0.0.0"
    conn.laddr.port = 8080
    conn.raddr = None
    conn.status = "LISTEN"
    conn.pid = 1234
    return conn


@pytest.fixture
def mock_udp_connection():
    """Create a mock UDP connection object."""
    conn = Mock()
    conn.laddr = Mock()
    conn.laddr.ip = "0.0.0.0"
    conn.laddr.port = 53
    conn.raddr = None
    conn.pid = 5678
    return conn


@pytest.fixture
def mock_process():
    """Create a mock psutil.Process object."""
    process = Mock(spec=psutil.Process)
    process.name.return_value = "test_process.exe"
    process.pid = 1234
    return process


@pytest.fixture
def mock_critical_process():
    """Create a mock critical process object."""
    process = Mock(spec=psutil.Process)
    process.name.return_value = "svchost.exe"
    process.pid = 100
    return process
