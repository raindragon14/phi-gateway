"""Structured JSON logging configuration for PhiGateway.

Provides a JSON log formatter that outputs structured logs with
timestamp, level, logger, message, and extra fields. Overrides
the uvicorn access logger to emit JSON instead of plain text.
"""

import json
import logging
import logging.config
import sys
from typing import Any


class JSONLogFormatter(logging.Formatter):
    """Custom formatter that outputs log records as structured JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a structured JSON line.

        Args:
            record: The log record to format.

        Returns:
            A JSON string with timestamp, level, logger, message,
            and any extra fields.
        """
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields passed via the `extra` parameter
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "id", "levelname", "levelno",
                "lineno", "module", "msecs", "message", "msg", "name",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONLogFormatter,
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stdout,
        },
        "console_std": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        # Application logger — JSON output
        "phi_gateway": {
            "handlers": ["console_json"],
            "level": "INFO",
            "propagate": False,
        },
        # Uvicorn access log — JSON output with request context fields
        "uvicorn.access": {
            "handlers": ["console_json"],
            "level": "INFO",
            "propagate": False,
        },
        # Uvicorn error log — JSON output
        "uvicorn": {
            "handlers": ["console_json"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console_std"],
        "level": "WARNING",
    },
}


def setup_logging() -> None:
    """Apply the structured JSON logging configuration.

    Call this once at application startup before any logging occurs.
    """
    logging.config.dictConfig(LOGGING_CONFIG)
