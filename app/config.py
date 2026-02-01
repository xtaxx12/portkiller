"""
Configuration settings for PortKiller using Pydantic Settings.

Supports environment variables and .env file loading with validation.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.

    All settings can be overridden via environment variables with PORTKILLER_ prefix.
    Example: PORTKILLER_HOST=0.0.0.0 PORTKILLER_PORT=9000
    """

    model_config = SettingsConfigDict(
        env_prefix="PORTKILLER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application info
    APP_NAME: str = Field(default="PortKiller", description="Application name")
    APP_VERSION: str = Field(default="1.1.0", description="Application version")
    APP_DESCRIPTION: str = Field(
        default="Port Management & Process Control Tool", description="Application description"
    )

    # Server settings
    HOST: str = Field(
        default="127.0.0.1",
        description="Server host address",
        examples=["127.0.0.1", "0.0.0.0"],  # nosec B104
    )
    PORT: int = Field(default=8787, ge=1, le=65535, description="Server port number")
    DEBUG: bool = Field(default=False, description="Enable debug mode with hot reload")

    # Auto-refresh interval (seconds)
    REFRESH_INTERVAL: int = Field(
        default=5, ge=1, le=60, description="Auto-refresh interval in seconds"
    )

    # Logging
    LOG_FILE: str = Field(default="logs/portkiller.log", description="Path to log file")
    LOG_MAX_SIZE: int = Field(
        default=10 * 1024 * 1024, description="Maximum log file size in bytes"  # 10 MB
    )
    LOG_BACKUP_COUNT: int = Field(
        default=5, ge=1, le=10, description="Number of log backup files to keep"
    )

    @field_validator("HOST")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host address format."""
        if not v or v.isspace():
            raise ValueError("Host cannot be empty")
        return v.strip()

    @property
    def CRITICAL_PROCESSES(self) -> set[str]:
        """
        Critical processes that should NOT be terminated.
        These are protected by default across all platforms.
        """
        return {
            # Windows critical processes
            "system",
            "smss.exe",
            "csrss.exe",
            "wininit.exe",
            "services.exe",
            "lsass.exe",
            "svchost.exe",
            "winlogon.exe",
            "explorer.exe",
            "dwm.exe",
            # Linux critical processes
            "init",
            "systemd",
            "kthreadd",
            "ksoftirqd",
            "kworker",
            # macOS critical processes
            "launchd",
            "kernel_task",
            "WindowServer",
        }

    @property
    def CRITICAL_PORTS(self) -> set[int]:
        """
        Critical ports (system ports that typically shouldn't be killed).
        """
        return {
            22,  # SSH
            53,  # DNS
            67,  # DHCP
            68,  # DHCP
            123,  # NTP
            135,  # RPC
            137,  # NetBIOS
            138,  # NetBIOS
            139,  # NetBIOS
            445,  # SMB
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Default settings instance for backwards compatibility
settings = get_settings()
