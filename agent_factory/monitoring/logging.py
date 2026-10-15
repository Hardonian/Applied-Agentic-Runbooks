"""Structured logging with JSON output."""

import logging
import sys
from datetime import datetime
from typing import Any

from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Structured logger with JSON output."""
    
    def __init__(self, name: str, level: str = "INFO"):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Log level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal log method."""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log("ERROR", message, **kwargs)
    
    def exception(self, message: str, exc_info: Any = None, **kwargs):
        """Log exception."""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.error(message, exc_info=exc_info, extra=extra)


def setup_structured_logging(level: str = "INFO") -> StructuredLogger:
    """
    Setup structured logging.
    
    Args:
        level: Log level
        
    Returns:
        Configured logger
    """
    return StructuredLogger("agent_factory", level=level)
