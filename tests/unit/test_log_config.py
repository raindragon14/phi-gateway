"""Unit tests for phi_gateway.log_config — JSONLogFormatter and setup_logging."""

import json
import logging
import logging.config

from phi_gateway.log_config import JSONLogFormatter, setup_logging


class TestJSONLogFormatter:
    """Tests for the JSONLogFormatter class."""

    def _make_record(self, level=logging.INFO, msg="test message", **extra) -> logging.LogRecord:
        """Helper: create a LogRecord with optional extra fields."""
        record = logging.LogRecord(
            name="test.logger",
            level=level,
            pathname="test.py",
            lineno=1,
            msg=msg,
            args=(),
            exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_json_output_is_valid_json(self):
        """Formatter output must be parseable JSON."""
        formatter = JSONLogFormatter()
        record = self._make_record()
        output = formatter.format(record)
        parsed = json.loads(output)  # would raise if invalid
        assert isinstance(parsed, dict)

    def test_json_has_required_fields(self):
        """Output must contain timestamp, level, logger, message."""
        formatter = JSONLogFormatter()
        record = self._make_record(level=logging.WARNING, msg="hello world")
        output = json.loads(formatter.format(record))

        assert "timestamp" in output
        assert output["level"] == "WARNING"
        assert output["logger"] == "test.logger"
        assert output["message"] == "hello world"

    def test_json_extra_fields(self):
        """Extra fields passed via `extra=` appear in the JSON output."""
        formatter = JSONLogFormatter()
        record = self._make_record(msg="with extra", request_id="abc-123", user="alice")
        output = json.loads(formatter.format(record))

        assert output["request_id"] == "abc-123"
        assert output["user"] == "alice"

    def test_json_exception_info(self):
        """Exception info is included when exc_info is set."""
        formatter = JSONLogFormatter()
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys
            exc_info = sys.exc_info()

        record = self._make_record(msg="error occurred", exc_info=exc_info)
        output = json.loads(formatter.format(record))

        assert "exception" in output
        assert "RuntimeError" in output["exception"]
        assert "boom" in output["exception"]

    def test_setup_logging_applies_config(self):
        """setup_logging() should not raise and should configure loggers."""
        setup_logging()  # should not raise

        logger = logging.getLogger("phi_gateway")
        # After setup_logging, phi_gateway logger should have handlers
        assert len(logger.handlers) > 0
        # Level should be INFO
        assert logger.level == logging.INFO or logger.isEnabledFor(logging.INFO)
