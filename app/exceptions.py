"""
Centralized Exception Handling for PortKiller API.

Provides custom exceptions and global exception handlers for consistent error responses.
"""

import traceback
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ===== Custom Exceptions =====

class PortKillerException(Exception):
    """Base exception for all PortKiller custom exceptions."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ProcessNotFoundError(PortKillerException):
    """Raised when a process is not found."""

    def __init__(self, pid: int):
        super().__init__(
            message=f"Process with PID {pid} not found",
            error_code="PROCESS_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"pid": pid},
        )


class CriticalProcessError(PortKillerException):
    """Raised when attempting to terminate a critical process."""

    def __init__(self, pid: int, process_name: str):
        super().__init__(
            message=f"Cannot terminate critical system process: {process_name}",
            error_code="CRITICAL_PROCESS",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"pid": pid, "process_name": process_name},
        )


class ProcessAccessDeniedError(PortKillerException):
    """Raised when access to a process is denied."""

    def __init__(self, pid: int, reason: str = "Access denied"):
        super().__init__(
            message=f"Access denied to process {pid}: {reason}",
            error_code="ACCESS_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"pid": pid, "reason": reason},
        )


class ProcessTerminationError(PortKillerException):
    """Raised when process termination fails."""

    def __init__(self, pid: int, reason: str):
        super().__init__(
            message=f"Failed to terminate process {pid}: {reason}",
            error_code="TERMINATION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"pid": pid, "reason": reason},
        )


class ValidationError(PortKillerException):
    """Raised for input validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field} if field else {},
        )


class ExportError(PortKillerException):
    """Raised when data export fails."""

    def __init__(self, format: str, reason: str):
        super().__init__(
            message=f"Failed to export data as {format}: {reason}",
            error_code="EXPORT_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"format": format, "reason": reason},
        )


# ===== Error Response Model =====

class ErrorResponse(BaseModel):
    """Standard error response format."""

    success: bool = False
    error_code: str
    message: str
    details: dict[str, Any] = {}


# ===== Exception Handlers =====

async def portkiller_exception_handler(
    request: Request, exc: PortKillerException
) -> JSONResponse:
    """Handle all PortKiller custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions with a generic error response."""
    # Log the error (in production, you'd want proper logging here)
    traceback.print_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__},
        ).model_dump(),
    )


async def value_error_handler(
    request: Request, exc: ValueError
) -> JSONResponse:
    """Handle ValueError as validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error_code="VALIDATION_ERROR",
            message=str(exc),
            details={},
        ).model_dump(),
    )


# ===== Register Handlers =====

def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(PortKillerException, portkiller_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    # Uncomment for production to catch all unhandled exceptions:
    # app.add_exception_handler(Exception, generic_exception_handler)
