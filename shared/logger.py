"""
shared/logger.py — Structured logging configuration

Uses structlog to produce JSON-formatted logs in production and
human-readable colored logs in development. Every module should
use: from shared.logger import get_logger
"""

import sys
import logging
import structlog
from shared.config import config


def _configure_structlog() -> None:
    """
    Configure structlog processors based on environment.
    
    - Development: colored, human-readable console output
    - Production: JSON lines for log aggregation (ELK, Datadog, etc.)
    """
    # ── Shared processors run in both environments ──────────────
    shared_processors = [
        structlog.contextvars.merge_contextvars,       # merge thread-local context
        structlog.processors.add_log_level,            # inject "level" key
        structlog.processors.StackInfoRenderer(),      # render stack traces
        structlog.processors.TimeStamper(fmt="iso"),   # ISO 8601 timestamps
        structlog.processors.UnicodeDecoder(),         # decode bytes to str
    ]

    if config.APP_ENV == "development":
        # ── Dev: pretty-print to console ────────────────────────
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # ── Prod: structured JSON for log pipelines ─────────────
        renderer = structlog.processors.JSONRenderer()

    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


# ── Run configuration once on import ────────────────────────────
_configure_structlog()


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a named logger instance.
    
    Args:
        name: Module or component name (e.g., "q2.chunker")
    
    Returns:
        Bound structlog logger with the component name attached
    """
    return structlog.get_logger(component=name)
