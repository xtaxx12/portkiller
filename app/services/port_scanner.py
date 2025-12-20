"""
Port Scanner Service - Interfaces with the operating system to detect open ports.
"""

from typing import Optional

import psutil

from ..config import settings
from ..models.port import PortInfo, SystemStats


class PortScannerService:
    """
    Service for scanning and retrieving information about open ports.
    Uses psutil for cross-platform compatibility.
    """

    # Connection state mapping
    STATE_MAP: dict[str, str] = {
        "LISTEN": "LISTEN",
        "ESTABLISHED": "ESTABLISHED",
        "TIME_WAIT": "TIME_WAIT",
        "CLOSE_WAIT": "CLOSE_WAIT",
        "FIN_WAIT1": "FIN_WAIT1",
        "FIN_WAIT2": "FIN_WAIT2",
        "SYN_SENT": "SYN_SENT",
        "SYN_RECV": "SYN_RECV",
        "LAST_ACK": "LAST_ACK",
        "CLOSING": "CLOSING",
        "NONE": "NONE",
    }

    def __init__(self):
        self._process_cache: dict[int, str] = {}

    def _get_process_name(self, pid: Optional[int]) -> Optional[str]:
        """Get process name from PID with caching."""
        if pid is None:
            return None

        if pid in self._process_cache:
            return self._process_cache[pid]

        try:
            process = psutil.Process(pid)
            name = process.name()
            self._process_cache[pid] = name
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def _is_critical_process(self, process_name: Optional[str], port: int) -> bool:
        """Check if a process or port is critical."""
        if process_name and process_name.lower() in {
            p.lower() for p in settings.CRITICAL_PROCESSES
        }:
            return True
        if port in settings.CRITICAL_PORTS:
            return True
        return False

    def _format_address(self, addr) -> str:
        """Format an address tuple to string."""
        if addr:
            return f"{addr.ip}:{addr.port}"
        return ""

    def get_all_connections(self) -> list[PortInfo]:
        """
        Get all network connections with port and process information.

        Returns:
            List of PortInfo objects representing all open connections.
        """
        connections: list[PortInfo] = []
        seen_ports: set = set()  # To avoid duplicates

        # Get TCP connections
        try:
            tcp_connections = psutil.net_connections(kind="tcp")
            for conn in tcp_connections:
                if conn.laddr:
                    port = conn.laddr.port
                    key = (port, "TCP", conn.status, conn.pid)

                    if key not in seen_ports:
                        seen_ports.add(key)
                        process_name = self._get_process_name(conn.pid)

                        connections.append(
                            PortInfo(
                                port=port,
                                protocol="TCP",
                                state=self.STATE_MAP.get(conn.status, conn.status),
                                pid=conn.pid,
                                process_name=process_name,
                                local_address=self._format_address(conn.laddr),
                                remote_address=(
                                    self._format_address(conn.raddr) if conn.raddr else None
                                ),
                                is_critical=self._is_critical_process(process_name, port),
                            )
                        )
        except (psutil.AccessDenied, PermissionError) as e:
            print(f"Access denied when scanning TCP ports: {e}")

        # Get UDP connections
        try:
            udp_connections = psutil.net_connections(kind="udp")
            for conn in udp_connections:
                if conn.laddr:
                    port = conn.laddr.port
                    key = (port, "UDP", conn.pid)

                    if key not in seen_ports:
                        seen_ports.add(key)
                        process_name = self._get_process_name(conn.pid)

                        connections.append(
                            PortInfo(
                                port=port,
                                protocol="UDP",
                                state="NONE",  # UDP doesn't have connection states
                                pid=conn.pid,
                                process_name=process_name,
                                local_address=self._format_address(conn.laddr),
                                remote_address=(
                                    self._format_address(conn.raddr) if conn.raddr else None
                                ),
                                is_critical=self._is_critical_process(process_name, port),
                            )
                        )
        except (psutil.AccessDenied, PermissionError) as e:
            print(f"Access denied when scanning UDP ports: {e}")

        # Sort by port number
        connections.sort(key=lambda x: (x.port, x.protocol))

        # Clear process cache to avoid stale data on next refresh
        self._process_cache.clear()

        return connections

    def get_system_stats(self, connections: Optional[list[PortInfo]] = None) -> SystemStats:
        """
        Calculate system statistics from the connections list.

        Args:
            connections: Optional pre-fetched connections list. If None, fetches new data.

        Returns:
            SystemStats object with aggregated statistics.
        """
        if connections is None:
            connections = self.get_all_connections()

        tcp_ports = [c for c in connections if c.protocol == "TCP"]
        udp_ports = [c for c in connections if c.protocol == "UDP"]
        listening = [c for c in connections if c.state == "LISTEN"]
        established = [c for c in connections if c.state == "ESTABLISHED"]
        unique_pids = {c.pid for c in connections if c.pid is not None}

        return SystemStats(
            total_tcp_ports=len(tcp_ports),
            total_udp_ports=len(udp_ports),
            listening_ports=len(listening),
            established_connections=len(established),
            unique_processes=len(unique_pids),
        )

    def filter_connections(
        self,
        connections: list[PortInfo],
        port_filter: Optional[int] = None,
        protocol_filter: Optional[str] = None,
        process_filter: Optional[str] = None,
        state_filter: Optional[str] = None,
    ) -> list[PortInfo]:
        """
        Filter connections based on criteria.

        Args:
            connections: List of connections to filter.
            port_filter: Filter by specific port number.
            protocol_filter: Filter by protocol (TCP/UDP).
            process_filter: Filter by process name (partial match).
            state_filter: Filter by connection state.

        Returns:
            Filtered list of connections.
        """
        result = connections

        if port_filter is not None:
            result = [c for c in result if c.port == port_filter]

        if protocol_filter:
            result = [c for c in result if c.protocol.upper() == protocol_filter.upper()]

        if process_filter:
            result = [
                c
                for c in result
                if c.process_name and process_filter.lower() in c.process_name.lower()
            ]

        if state_filter:
            result = [c for c in result if c.state.upper() == state_filter.upper()]

        return result


# Singleton instance
port_scanner = PortScannerService()
