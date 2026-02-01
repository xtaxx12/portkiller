"""
Rate Limiting Middleware for PortKiller API.

Protects the API against abuse by limiting request rates per client.
Uses slowapi with in-memory storage for simplicity.
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse


def get_client_identifier(request: Request) -> str:
    """
    Get a unique identifier for the client making the request.

    Uses the remote address, falling back to a default for local/internal requests.
    """
    # For local requests (desktop app), use a fixed identifier
    remote_addr = get_remote_address(request)
    if remote_addr in ("127.0.0.1", "localhost", "::1"):
        return "local-client"
    return remote_addr


# Create the rate limiter instance
# Using in-memory storage (default) - suitable for single-instance deployment
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["200/minute"],  # Default: 200 requests per minute
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a user-friendly JSON response with retry information.
    """
    # Extract retry-after from the exception if available
    retry_after = getattr(exc, "retry_after", 60)

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "rate_limit_exceeded",
            "message": f"Too many requests. Please try again in {retry_after} seconds.",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


# Rate limit configurations for different endpoint types
class RateLimits:
    """
    Centralized rate limit configurations.

    Different limits for different types of operations:
    - READ operations (GET): More permissive
    - WRITE/DANGEROUS operations (POST kill): More restrictive
    """

    # Read operations - data fetching
    PORTS_LIST = "60/minute"          # List all ports
    STATS = "60/minute"               # Get statistics
    LOGS = "30/minute"                # Get action logs
    PROCESS_INFO = "60/minute"        # Get process details

    # Write/dangerous operations - process termination
    KILL_PROCESS = "10/minute"        # Terminate process (strict limit)

    # Health check - very permissive for monitoring
    HEALTH = "120/minute"
