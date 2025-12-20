"""
Unit tests for the PortScannerService.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import psutil

from app.services.port_scanner import PortScannerService, port_scanner
from app.models.port import PortInfo, SystemStats
from app.config import settings


class TestPortScannerService:
    """Tests for PortScannerService class."""

    def test_init_creates_empty_cache(self, port_scanner):
        """Test that initialization creates an empty process cache."""
        assert port_scanner._process_cache == {}

    def test_get_process_name_returns_none_for_none_pid(self, port_scanner):
        """Test that _get_process_name returns None when pid is None."""
        result = port_scanner._get_process_name(None)
        assert result is None

    def test_get_process_name_caches_result(self, port_scanner):
        """Test that process names are cached."""
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "test_process.exe"
            mock_process_class.return_value = mock_process

            # First call should create cache entry
            result1 = port_scanner._get_process_name(1234)
            assert result1 == "test_process.exe"
            assert 1234 in port_scanner._process_cache

            # Second call should use cache
            result2 = port_scanner._get_process_name(1234)
            assert result2 == "test_process.exe"
            
            # Process should only be called once
            mock_process_class.assert_called_once_with(1234)

    def test_get_process_name_handles_no_such_process(self, port_scanner):
        """Test handling of NoSuchProcess exception."""
        with patch('psutil.Process') as mock_process_class:
            mock_process_class.side_effect = psutil.NoSuchProcess(1234)
            
            result = port_scanner._get_process_name(1234)
            assert result is None

    def test_get_process_name_handles_access_denied(self, port_scanner):
        """Test handling of AccessDenied exception."""
        with patch('psutil.Process') as mock_process_class:
            mock_process_class.side_effect = psutil.AccessDenied(1234)
            
            result = port_scanner._get_process_name(1234)
            assert result is None

    def test_get_process_name_handles_zombie_process(self, port_scanner):
        """Test handling of ZombieProcess exception."""
        with patch('psutil.Process') as mock_process_class:
            mock_process_class.side_effect = psutil.ZombieProcess(1234)
            
            result = port_scanner._get_process_name(1234)
            assert result is None


class TestCriticalProcessDetection:
    """Tests for critical process detection logic."""

    def test_is_critical_process_detects_critical_by_name(self, port_scanner):
        """Test detection of critical processes by name."""
        # Test Windows critical processes
        assert port_scanner._is_critical_process("svchost.exe", 8080) is True
        assert port_scanner._is_critical_process("csrss.exe", 8080) is True
        assert port_scanner._is_critical_process("lsass.exe", 8080) is True
        
        # Test Linux critical processes
        assert port_scanner._is_critical_process("systemd", 8080) is True
        assert port_scanner._is_critical_process("init", 8080) is True

    def test_is_critical_process_detects_critical_by_port(self, port_scanner):
        """Test detection of critical connections by port."""
        assert port_scanner._is_critical_process("nginx", 22) is True   # SSH
        assert port_scanner._is_critical_process("nginx", 53) is True   # DNS
        assert port_scanner._is_critical_process("nginx", 445) is True  # SMB

    def test_is_critical_process_returns_false_for_normal(self, port_scanner):
        """Test that normal processes/ports are not marked as critical."""
        assert port_scanner._is_critical_process("python.exe", 8080) is False
        assert port_scanner._is_critical_process("nginx", 80) is False
        assert port_scanner._is_critical_process("node", 3000) is False

    def test_is_critical_process_handles_none_name(self, port_scanner):
        """Test handling of None process name."""
        assert port_scanner._is_critical_process(None, 8080) is False
        assert port_scanner._is_critical_process(None, 22) is True  # Critical port

    def test_is_critical_process_case_insensitive(self, port_scanner):
        """Test that process name matching is case-insensitive."""
        assert port_scanner._is_critical_process("SVCHOST.EXE", 8080) is True
        assert port_scanner._is_critical_process("SvcHost.Exe", 8080) is True


class TestAddressFormatting:
    """Tests for address formatting logic."""

    def test_format_address_with_valid_address(self, port_scanner):
        """Test formatting of a valid address."""
        addr = Mock()
        addr.ip = "192.168.1.1"
        addr.port = 8080
        
        result = port_scanner._format_address(addr)
        assert result == "192.168.1.1:8080"

    def test_format_address_with_none(self, port_scanner):
        """Test formatting of None address."""
        result = port_scanner._format_address(None)
        assert result == ""

    def test_format_address_with_localhost(self, port_scanner):
        """Test formatting of localhost address."""
        addr = Mock()
        addr.ip = "127.0.0.1"
        addr.port = 3000
        
        result = port_scanner._format_address(addr)
        assert result == "127.0.0.1:3000"

    def test_format_address_with_ipv6(self, port_scanner):
        """Test formatting of IPv6 address."""
        addr = Mock()
        addr.ip = "::1"
        addr.port = 8080
        
        result = port_scanner._format_address(addr)
        assert result == "::1:8080"


class TestGetAllConnections:
    """Tests for the get_all_connections method."""

    def test_get_all_connections_returns_list(self, port_scanner):
        """Test that get_all_connections returns a list."""
        with patch('psutil.net_connections') as mock_net_conn:
            mock_net_conn.return_value = []
            
            result = port_scanner.get_all_connections()
            assert isinstance(result, list)

    def test_get_all_connections_processes_tcp(self, port_scanner, mock_tcp_connection):
        """Test processing of TCP connections."""
        with patch('psutil.net_connections') as mock_net_conn:
            mock_net_conn.side_effect = lambda kind: [mock_tcp_connection] if kind == 'tcp' else []
            
            with patch.object(port_scanner, '_get_process_name', return_value="test.exe"):
                result = port_scanner.get_all_connections()
                
                assert len(result) >= 1
                tcp_conn = next((c for c in result if c.protocol == "TCP"), None)
                assert tcp_conn is not None
                assert tcp_conn.port == 8080
                assert tcp_conn.state == "LISTEN"

    def test_get_all_connections_processes_udp(self, port_scanner, mock_udp_connection):
        """Test processing of UDP connections."""
        with patch('psutil.net_connections') as mock_net_conn:
            mock_net_conn.side_effect = lambda kind: [mock_udp_connection] if kind == 'udp' else []
            
            with patch.object(port_scanner, '_get_process_name', return_value="dns.exe"):
                result = port_scanner.get_all_connections()
                
                udp_conn = next((c for c in result if c.protocol == "UDP"), None)
                assert udp_conn is not None
                assert udp_conn.port == 53
                assert udp_conn.state == "NONE"

    def test_get_all_connections_handles_access_denied(self, port_scanner):
        """Test handling of AccessDenied when scanning."""
        with patch('psutil.net_connections') as mock_net_conn:
            mock_net_conn.side_effect = psutil.AccessDenied(0)
            
            # Should not raise, just return empty list
            result = port_scanner.get_all_connections()
            assert result == []

    def test_get_all_connections_avoids_duplicates(self, port_scanner):
        """Test that duplicate connections are filtered out."""
        conn1 = Mock()
        conn1.laddr = Mock(ip="0.0.0.0", port=8080)
        conn1.raddr = None
        conn1.status = "LISTEN"
        conn1.pid = 1234

        conn2 = Mock()  # Same as conn1
        conn2.laddr = Mock(ip="0.0.0.0", port=8080)
        conn2.raddr = None
        conn2.status = "LISTEN"
        conn2.pid = 1234

        with patch('psutil.net_connections') as mock_net_conn:
            mock_net_conn.side_effect = lambda kind: [conn1, conn2] if kind == 'tcp' else []
            
            with patch.object(port_scanner, '_get_process_name', return_value="test.exe"):
                result = port_scanner.get_all_connections()
                
                # Should only have one entry despite two identical connections
                tcp_entries = [c for c in result if c.port == 8080]
                assert len(tcp_entries) == 1

    def test_get_all_connections_clears_cache(self, port_scanner):
        """Test that process cache is cleared after getting connections."""
        port_scanner._process_cache = {1234: "cached_process.exe"}
        
        with patch('psutil.net_connections', return_value=[]):
            port_scanner.get_all_connections()
            
            # Cache should be cleared
            assert port_scanner._process_cache == {}

    def test_get_all_connections_sorts_by_port(self, port_scanner):
        """Test that results are sorted by port number."""
        conn1 = Mock(laddr=Mock(ip="0.0.0.0", port=8080), raddr=None, status="LISTEN", pid=1)
        conn2 = Mock(laddr=Mock(ip="0.0.0.0", port=80), raddr=None, status="LISTEN", pid=2)
        conn3 = Mock(laddr=Mock(ip="0.0.0.0", port=443), raddr=None, status="LISTEN", pid=3)

        with patch('psutil.net_connections') as mock_net_conn:
            mock_net_conn.side_effect = lambda kind: [conn1, conn2, conn3] if kind == 'tcp' else []
            
            with patch.object(port_scanner, '_get_process_name', return_value="test.exe"):
                result = port_scanner.get_all_connections()
                
                ports = [c.port for c in result]
                assert ports == sorted(ports)


class TestGetSystemStats:
    """Tests for the get_system_stats method."""

    def test_get_system_stats_with_connections(self, port_scanner, sample_port_info_list):
        """Test statistics calculation with sample connections."""
        result = port_scanner.get_system_stats(sample_port_info_list)
        
        assert isinstance(result, SystemStats)
        assert result.total_tcp_ports == 4  # 80, 443, 22, 8080
        assert result.total_udp_ports == 1  # 53
        assert result.listening_ports == 3  # 80, 22, 8080
        assert result.established_connections == 1  # 443
        assert result.unique_processes == 4  # nginx, sshd, dnsmasq, python

    def test_get_system_stats_empty_connections(self, port_scanner):
        """Test statistics with empty connections list."""
        result = port_scanner.get_system_stats([])
        
        assert result.total_tcp_ports == 0
        assert result.total_udp_ports == 0
        assert result.listening_ports == 0
        assert result.established_connections == 0
        assert result.unique_processes == 0

    def test_get_system_stats_fetches_if_none(self, port_scanner):
        """Test that stats fetches connections if none provided."""
        with patch.object(port_scanner, 'get_all_connections', return_value=[]) as mock_get:
            port_scanner.get_system_stats(None)
            mock_get.assert_called_once()


class TestFilterConnections:
    """Tests for the filter_connections method."""

    def test_filter_by_port(self, port_scanner, sample_port_info_list):
        """Test filtering by specific port."""
        result = port_scanner.filter_connections(sample_port_info_list, port_filter=80)
        
        assert len(result) == 1
        assert result[0].port == 80

    def test_filter_by_protocol_tcp(self, port_scanner, sample_port_info_list):
        """Test filtering by TCP protocol."""
        result = port_scanner.filter_connections(sample_port_info_list, protocol_filter="TCP")
        
        assert len(result) == 4
        assert all(c.protocol == "TCP" for c in result)

    def test_filter_by_protocol_udp(self, port_scanner, sample_port_info_list):
        """Test filtering by UDP protocol."""
        result = port_scanner.filter_connections(sample_port_info_list, protocol_filter="UDP")
        
        assert len(result) == 1
        assert result[0].protocol == "UDP"

    def test_filter_by_protocol_case_insensitive(self, port_scanner, sample_port_info_list):
        """Test that protocol filtering is case-insensitive."""
        result_lower = port_scanner.filter_connections(sample_port_info_list, protocol_filter="tcp")
        result_upper = port_scanner.filter_connections(sample_port_info_list, protocol_filter="TCP")
        
        assert len(result_lower) == len(result_upper)

    def test_filter_by_process_name(self, port_scanner, sample_port_info_list):
        """Test filtering by process name (partial match)."""
        result = port_scanner.filter_connections(sample_port_info_list, process_filter="nginx")
        
        assert len(result) == 2
        assert all("nginx" in c.process_name for c in result)

    def test_filter_by_process_name_partial(self, port_scanner, sample_port_info_list):
        """Test filtering by partial process name."""
        result = port_scanner.filter_connections(sample_port_info_list, process_filter="ngi")
        
        assert len(result) == 2

    def test_filter_by_process_name_case_insensitive(self, port_scanner, sample_port_info_list):
        """Test that process filtering is case-insensitive."""
        result = port_scanner.filter_connections(sample_port_info_list, process_filter="NGINX")
        
        assert len(result) == 2

    def test_filter_by_state(self, port_scanner, sample_port_info_list):
        """Test filtering by connection state."""
        result = port_scanner.filter_connections(sample_port_info_list, state_filter="LISTEN")
        
        assert len(result) == 3
        assert all(c.state == "LISTEN" for c in result)

    def test_filter_by_state_case_insensitive(self, port_scanner, sample_port_info_list):
        """Test that state filtering is case-insensitive."""
        result = port_scanner.filter_connections(sample_port_info_list, state_filter="listen")
        
        assert len(result) == 3

    def test_multiple_filters(self, port_scanner, sample_port_info_list):
        """Test combining multiple filters."""
        result = port_scanner.filter_connections(
            sample_port_info_list,
            protocol_filter="TCP",
            state_filter="LISTEN"
        )
        
        assert len(result) == 3
        assert all(c.protocol == "TCP" and c.state == "LISTEN" for c in result)

    def test_filter_no_match(self, port_scanner, sample_port_info_list):
        """Test filtering with no matching results."""
        result = port_scanner.filter_connections(sample_port_info_list, port_filter=99999)
        
        assert len(result) == 0

    def test_filter_empty_list(self, port_scanner):
        """Test filtering an empty list."""
        result = port_scanner.filter_connections([], port_filter=80)
        
        assert result == []


class TestSingletonInstance:
    """Tests for the singleton instance."""

    def test_singleton_instance_exists(self):
        """Test that the singleton instance is created."""
        assert port_scanner is not None
        assert isinstance(port_scanner, PortScannerService)
