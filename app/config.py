"""
Configuration settings for PortKiller.
"""
import os


class Settings:
    """Application settings and constants."""

    # Application info
    APP_NAME: str = "PortKiller"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Port Management & Process Control Tool"

    # Server settings
    HOST: str = os.getenv("PORTKILLER_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORTKILLER_PORT", "8787"))
    DEBUG: bool = os.getenv("PORTKILLER_DEBUG", "false").lower() == "true"

    # Auto-refresh interval (seconds)
    REFRESH_INTERVAL: int = 5

    # Critical processes that should NOT be terminated
    # These are protected by default
    CRITICAL_PROCESSES: set[str] = {
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

    # Critical ports (system ports that typically shouldn't be killed)
    CRITICAL_PORTS: set[int] = {
        22,    # SSH
        53,    # DNS
        67,    # DHCP
        68,    # DHCP
        123,   # NTP
        135,   # RPC
        137,   # NetBIOS
        138,   # NetBIOS
        139,   # NetBIOS
        445,   # SMB
    }

    # Logging
    LOG_FILE: str = "logs/portkiller.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5


settings = Settings()
