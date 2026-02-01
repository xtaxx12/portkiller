"""
Dependency Injection Container for PortKiller.

Provides centralized dependency management for better testability and decoupling.
"""

from typing import TypeVar

from fastapi import Depends

from .config import Settings, get_settings
from .services.port_scanner import PortScanner
from .services.process_manager import ProcessManager

T = TypeVar("T")


class Container:
    """
    Dependency Injection Container.

    Provides factory methods for creating service instances with proper dependencies.
    Supports both singleton and transient lifecycles.
    """

    _instances: dict[type, object] = {}

    @classmethod
    def get_settings(cls) -> Settings:
        """Get application settings instance."""
        return get_settings()

    @classmethod
    def get_port_scanner(cls, settings: Settings = None) -> PortScanner:
        """
        Get PortScanner instance.

        Uses singleton pattern for efficiency.
        """
        if PortScanner not in cls._instances:
            settings = settings or cls.get_settings()
            cls._instances[PortScanner] = PortScanner(settings)
        return cls._instances[PortScanner]

    @classmethod
    def get_process_manager(cls, settings: Settings = None) -> ProcessManager:
        """
        Get ProcessManager instance.

        Uses singleton pattern for efficiency.
        """
        if ProcessManager not in cls._instances:
            settings = settings or cls.get_settings()
            cls._instances[ProcessManager] = ProcessManager(settings)
        return cls._instances[ProcessManager]

    @classmethod
    def reset(cls) -> None:
        """Reset all cached instances. Useful for testing."""
        cls._instances.clear()
        get_settings.cache_clear()


# FastAPI Dependency Functions
def get_settings_dep() -> Settings:
    """FastAPI dependency for settings."""
    return Container.get_settings()


def get_port_scanner(settings: Settings = Depends(get_settings_dep)) -> PortScanner:
    """FastAPI dependency for PortScanner."""
    return Container.get_port_scanner(settings)


def get_process_manager(settings: Settings = Depends(get_settings_dep)) -> ProcessManager:
    """FastAPI dependency for ProcessManager."""
    return Container.get_process_manager(settings)
