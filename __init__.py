"""
Config Module Exporter
"""

from .settings import settings
from .logger import log

# Restrict imports to the frozen settings instance and the logger
__all__ = ["settings", "log"]