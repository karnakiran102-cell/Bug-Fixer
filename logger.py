"""
Centralized Logger Configuration
================================
Provides a standardized application logger that respects the environment level
and automatically masks sensitive secrets from stdout.
"""

import logging
import re
import sys
from .settings import settings

class RedactingFormatter(logging.Formatter):
    """
    A custom logging formatter that intercepts log messages and obfuscates 
    sensitive key-value pairs before they hit the console or log files.
    """
    
    # Regex to catch common secret patterns in dicts, JSON, or strings:
    # e.g., 'password': 'my-secret', api_key="sk-1234", token=xyz
    SECRET_PATTERN = re.compile(
        r"(?i)(password|secret|token|api_key|authorization|jwt|access_key)[\"\'\s:=]+([^\s\"\'\,]+)"
    )
    
    def __init__(self, fmt: str = None):
        super().__init__(fmt=fmt)
        self._redacted_string = r"\1=***REDACTED***"

    def format(self, record: logging.LogRecord) -> str:
        # Format the original message
        original_message = super().format(record)
        
        # Apply regex redaction
        redacted_message = self.SECRET_PATTERN.sub(self._redacted_string, original_message)
        return redacted_message


def setup_logger() -> logging.Logger:
    """
    Initializes and returns the globally configured logger instance.
    """
    # Set log level based on strict AppSettings
    log_level = logging.DEBUG if settings.debug_mode else logging.INFO
    
    logger = logging.getLogger(settings.app_name)
    logger.setLevel(log_level)
    
    # Prevent duplicate logs if initialized multiple times
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Standardized log formatting
        log_format = "%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
        formatter = RedactingFormatter(fmt=log_format)
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

log = setup_logger()