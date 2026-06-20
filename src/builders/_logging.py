"""Logging estructurado compartido para el pipeline de chile-hub.

Proporciona loggers preconfigurados con structlog. En desarrollo usa
salida legible con colores; en CI usa JSON para parseo automatizado.

Uso:
    from src.builders._logging import get_logger

    log = get_logger("build_dev_db")
    log.info("dataset_loaded", dataset="comunas", records=346, duration_ms=120)

    # Errores del pipeline (siempre con exc_info=True en excepciones)
    try:
        ...
    except Exception:
        log.error("build_failed", phase="duckdb", exc_info=True)
        raise
"""

from __future__ import annotations

import os
import sys
from typing import Any

import structlog

_IS_CI = os.environ.get("CI", "").lower() in ("true", "1")


def _configure_pipeline_logging() -> None:
    """Configura structlog una sola vez al importar el módulo."""
    shared_processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.FILENAME]
        ),
    ]

    if _IS_CI:
        # JSON → los logs de CI son parseables por jq, grep, etc.
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(sys.stderr),
            cache_logger_on_first_use=True,
        )
    else:
        # Consola con colores para desarrollo
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(sys.stderr),
            cache_logger_on_first_use=True,
        )


_configure_pipeline_logging()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Retorna un logger estructurado con el nombre del módulo como contexto."""
    return structlog.get_logger(name)
