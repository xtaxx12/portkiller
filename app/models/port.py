"""
Port and Process data models for PortKiller.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class PortInfo(BaseModel):
    """Model representing an open port and its associated process."""
    
    port: int = Field(..., description="Port number", ge=0, le=65535)
    protocol: Literal["TCP", "UDP"] = Field(..., description="Protocol type")
    state: str = Field(..., description="Connection state (LISTEN, ESTABLISHED, etc.)")
    pid: Optional[int] = Field(None, description="Process ID using this port")
    process_name: Optional[str] = Field(None, description="Name of the process")
    local_address: str = Field(..., description="Local address binding")
    remote_address: Optional[str] = Field(None, description="Remote address if connected")
    is_critical: bool = Field(False, description="Whether this process is critical")
    
    class Config:
        json_schema_extra = {
            "example": {
                "port": 8080,
                "protocol": "TCP",
                "state": "LISTEN",
                "pid": 1234,
                "process_name": "python.exe",
                "local_address": "0.0.0.0:8080",
                "remote_address": None,
                "is_critical": False
            }
        }


class ProcessKillRequest(BaseModel):
    """Request to terminate a process."""
    
    pid: int = Field(..., description="Process ID to terminate", gt=0)
    force: bool = Field(False, description="Force terminate (SIGKILL) if normal terminate fails")


class ProcessKillResponse(BaseModel):
    """Response after attempting to kill a process."""
    
    success: bool
    message: str
    pid: int
    process_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SystemStats(BaseModel):
    """System statistics for the dashboard."""
    
    total_tcp_ports: int
    total_udp_ports: int
    listening_ports: int
    established_connections: int
    unique_processes: int


class ActionLog(BaseModel):
    """Log entry for actions performed."""
    
    timestamp: datetime
    action: str
    target_pid: Optional[int]
    target_process: Optional[str]
    target_port: Optional[int]
    result: str
    user: Optional[str] = None
