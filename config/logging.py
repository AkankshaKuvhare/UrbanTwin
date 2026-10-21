"""Structured logging configuration for UrbanTwin research monorepo.

Configures standard library logging and structlog (with graceful fallback
if structlog is not installed) to output either formatted console logs or
structured JSON logs based on settings.
"""

import json
import logging
import sys
from typing import Any
from config.settings import settings

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


class FallbackStructuredLogger:
    """Fallback logger wrapper mimicking structlog API using standard logging."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _format_msg(self, msg: str, **kwargs: Any) -> str:
        if not kwargs:
            return msg
        if settings.LOG_FORMAT.lower() == "json":
            payload = {"event": msg, **kwargs}
            return json.dumps(payload, default=str)
        context = " ".join(f"{k}={v}" for k, v in kwargs.items())
        return f"{msg} | {context}"

    def info(self, msg: str, **kwargs: Any) -> None:
        self._logger.info(self._format_msg(msg, **kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._logger.warning(self._format_msg(msg, **kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        self._logger.error(self._format_msg(msg, **kwargs))

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._logger.debug(self._format_msg(msg, **kwargs))

    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(self._format_msg(msg, **kwargs))


def setup_logging() -> None:
    """Initialize structured logging system for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if HAS_STRUCTLOG:
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        if settings.LOG_FORMAT.lower() == "json":
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer(colors=True)

        structlog.configure(
            processors=shared_processors + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


def get_logger(name: str = __name__) -> Any:
    """Helper to retrieve a structured logger instance."""
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return FallbackStructuredLogger(logging.getLogger(name))
