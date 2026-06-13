"""Tests for core/logging.py."""

import logging

import structlog
from structlog._config import BoundLoggerLazyProxy

from konsilisyum.core.logging import (
    CorrelationLogger,
    add_level,
    add_logger_name,
    add_timestamp,
    create_correlation_logger,
    get_logger,
    setup_logging,
)


class TestProcessors:
    def test_add_timestamp(self):
        event = {"event": "test"}
        result = add_timestamp(logging.getLogger("test"), "info", event)
        assert "timestamp" in result

    def test_add_level(self):
        event = {"event": "test"}
        result = add_level(logging.getLogger("test"), "info", event)
        assert result["level"] == "INFO"

    def test_add_logger_name(self):
        logger = logging.getLogger("my_logger")
        event = {"event": "test"}
        result = add_logger_name(logger, "info", event)
        assert result["logger"] == "my_logger"


class TestSetupLogging:
    def test_returns_logger(self):
        logger = setup_logging(log_level="DEBUG")
        # structlog returns lazy proxy before first use
        assert isinstance(logger, (structlog.BoundLogger, BoundLoggerLazyProxy))

    def test_creates_log_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        setup_logging(log_level="INFO", log_file=str(log_file))
        assert log_file.exists()

    def test_json_format(self):
        logger = setup_logging(log_level="INFO", json_format=True)
        assert isinstance(logger, (structlog.BoundLogger, BoundLoggerLazyProxy))

    def test_different_levels(self):
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            logger = setup_logging(log_level=level)
            assert isinstance(logger, (structlog.BoundLogger, BoundLoggerLazyProxy))


class TestGetLogger:
    def test_returns_logger(self):
        logger = get_logger("test_module")
        assert isinstance(logger, (structlog.BoundLogger, BoundLoggerLazyProxy))


class TestCorrelationLogger:
    def test_info_without_correlation(self, caplog):
        base_logger = get_logger("test_corr")
        corr = CorrelationLogger(base_logger)
        # should not raise
        corr.info("test event", key="value")

    def test_info_with_correlation(self, caplog):
        base_logger = get_logger("test_corr2")
        corr = CorrelationLogger(base_logger, correlation_id="abc-123")
        corr.info("test event")

    def test_all_levels(self):
        base_logger = get_logger("test_levels")
        corr = CorrelationLogger(base_logger, correlation_id="x")
        corr.debug("debug msg")
        corr.info("info msg")
        corr.warning("warn msg")
        corr.error("error msg")
        corr.critical("critical msg")
        # should not raise

    def test_exception(self):
        base_logger = get_logger("test_exc")
        corr = CorrelationLogger(base_logger, correlation_id="x")
        try:
            raise ValueError("test")
        except ValueError:
            corr.exception("caught")
        # should not raise

    def test_bind_returns_new_logger(self):
        base_logger = get_logger("test_bind")
        corr = CorrelationLogger(base_logger, correlation_id="x")
        new_corr = corr.bind(user_id=42)
        assert isinstance(new_corr, CorrelationLogger)
        assert new_corr._correlation_id == "x"

    def test_add_correlation_when_none(self):
        base_logger = get_logger("test_none")
        corr = CorrelationLogger(base_logger, correlation_id=None)
        result = corr._add_correlation({"event": "test"})
        assert "correlation_id" not in result

    def test_add_correlation_when_set(self):
        base_logger = get_logger("test_set")
        corr = CorrelationLogger(base_logger, correlation_id="cid-1")
        result = corr._add_correlation({"event": "test"})
        assert result["correlation_id"] == "cid-1"


class TestCreateCorrelationLogger:
    def test_factory(self):
        logger = create_correlation_logger("module", "corr-1")
        assert isinstance(logger, CorrelationLogger)
        assert logger._correlation_id == "corr-1"
