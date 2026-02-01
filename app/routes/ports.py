"""
API Routes for port management.

All endpoints are protected by rate limiting to prevent abuse.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from ..middleware.rate_limit import RateLimits, limiter
from ..models.port import ActionLog, PortInfo, ProcessKillRequest, ProcessKillResponse, SystemStats
from ..services.port_scanner import port_scanner
from ..services.process_manager import process_manager

router = APIRouter(prefix="/api", tags=["ports"])


@router.get(
    "/ports",
    response_model=list[PortInfo],
    responses={429: {"description": "Rate limit exceeded"}},
)
@limiter.limit(RateLimits.PORTS_LIST)
async def get_ports(
    request: Request,
    port: Optional[int] = Query(None, description="Filter by specific port number"),
    protocol: Optional[str] = Query(None, description="Filter by protocol (TCP/UDP)"),
    process: Optional[str] = Query(None, description="Filter by process name (partial match)"),
    state: Optional[str] = Query(None, description="Filter by connection state"),
):
    """
    Get list of all open ports with filtering options.

    **Rate Limit:** 60 requests per minute

    Returns a list of port information including:
    - Port number
    - Protocol (TCP/UDP)
    - Connection state
    - Associated process ID and name
    - Whether the process is critical
    """
    connections = port_scanner.get_all_connections()

    if any([port, protocol, process, state]):
        connections = port_scanner.filter_connections(
            connections,
            port_filter=port,
            protocol_filter=protocol,
            process_filter=process,
            state_filter=state,
        )

    return connections


@router.get(
    "/stats",
    response_model=SystemStats,
    responses={429: {"description": "Rate limit exceeded"}},
)
@limiter.limit(RateLimits.STATS)
async def get_stats(request: Request):
    """
    Get aggregated system statistics about ports and processes.

    **Rate Limit:** 60 requests per minute

    Returns:
    - Total TCP ports
    - Total UDP ports
    - Listening ports
    - Established connections
    - Unique processes
    """
    connections = port_scanner.get_all_connections()
    return port_scanner.get_system_stats(connections)


@router.post(
    "/kill",
    response_model=ProcessKillResponse,
    responses={429: {"description": "Rate limit exceeded - too many kill requests"}},
)
@limiter.limit(RateLimits.KILL_PROCESS)
async def kill_process(request: Request, body: ProcessKillRequest):
    """
    Terminate a process by its PID.

    **Rate Limit:** 10 requests per minute (strict limit for dangerous operations)

    **Safety features:**
    - Critical system processes are protected
    - Requires confirmation in the UI
    - All actions are logged

    Args:
        pid: Process ID to terminate
        force: Force terminate if normal termination fails

    Returns:
        Result of the termination attempt
    """
    return process_manager.kill_process(body.pid, body.force)


@router.post(
    "/kill/{pid}",
    response_model=ProcessKillResponse,
    responses={429: {"description": "Rate limit exceeded - too many kill requests"}},
)
@limiter.limit(RateLimits.KILL_PROCESS)
async def kill_process_by_id(
    request: Request,
    pid: int,
    force: bool = Query(False, description="Force terminate if normal termination fails"),
    port: Optional[int] = Query(None, description="Port number for logging purposes"),
):
    """
    Terminate a process by its PID (path parameter version).

    **Rate Limit:** 10 requests per minute (strict limit for dangerous operations)
    """
    return process_manager.kill_process(pid, force, port)


@router.get(
    "/logs",
    response_model=list[ActionLog],
    responses={429: {"description": "Rate limit exceeded"}},
)
@limiter.limit(RateLimits.LOGS)
async def get_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Number of log entries to return"),
):
    """
    Get recent action logs.

    **Rate Limit:** 30 requests per minute

    Returns a list of actions performed, including:
    - Timestamp
    - Action type
    - Target process/port
    - Result
    - User who performed the action
    """
    return process_manager.get_action_logs(limit)


@router.get(
    "/process/{pid}",
    responses={
        404: {"description": "Process not found"},
        403: {"description": "Access denied to process"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(RateLimits.PROCESS_INFO)
async def get_process_details(request: Request, pid: int):
    """
    Get detailed information about a specific process.

    **Rate Limit:** 60 requests per minute
    """
    exists, name, error = process_manager.get_process_info(pid)

    if not exists:
        raise HTTPException(status_code=404, detail=error)

    if error:
        raise HTTPException(status_code=403, detail=error)

    return {"pid": pid, "name": name}

