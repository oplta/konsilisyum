from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.typing import EventDict


def add_timestamp(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["timestamp"] = structlog.processors.TimeStamper(fmt="iso")()
    return event_dict


def add_level(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["level"] = method_name.upper()
    return event_dict


def add_logger_name(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["logger"] = logger.name
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> structlog.BoundLogger:
    """Structured logging setup with console and optional file output."""

    shared_processors = [
        add_timestamp,
        add_level,
        add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        console_processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        console_processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True) if not json_format else structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    for handler in handlers:
        handler.setFormatter(formatter)

    return structlog.get_logger()


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


class CorrelationLogger:
    """Logger with correlation ID support for request tracing."""

    def __init__(self, logger: structlog.BoundLogger, correlation_id: Optional[str] = None):
        self._logger = logger
        self._correlation_id = correlation_id

    def _add_correlation(self, event_dict: EventDict) -> EventDict:
        if self._correlation_id:
            event_dict["correlation_id"] = self._correlation_id
        return event_dict

    def bind(self, **kwargs) -> "CorrelationLogger":
        new_logger = self._logger.bind(**kwargs)
        return CorrelationLogger(new_logger, self._correlation_id)

    def info(self, event: str, **kwargs) -> None:
        self._logger.info(event, **self._add_correlation(kwargs))

    def debug(self, event: str, **kwargs) -> None:
        self._logger.debug(event, **self._add_correlation(kwargs))

    def warning(self, event: str, **kwargs) -> None:
        self._logger.warning(event, **self._add_correlation(kwargs))

    def error(self, event: str, **kwargs) -> None:
        self._logger.error(event, **self._add_correlation(kwargs))

    def critical(self, event: str, **kwargs) -> None:
        self._logger.critical(event, **self._add_correlation(kwargs))

    def exception(self, event: str, **kwargs) -> None:
        self._logger.exception(event, **self._add_correlation(kwargs))


def create_correlation_logger(name: str, correlation_id: Optional[str] = None) -> CorrelationLogger:
    return CorrelationLogger(get_logger(name), correlation_id)
