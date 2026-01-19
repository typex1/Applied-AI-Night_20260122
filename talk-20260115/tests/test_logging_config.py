"""Tests for logging configuration."""

import logging
import os
import pytest
from io import StringIO

from src.logging_config import setup_logging, get_logger


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_default_log_level(self, monkeypatch):
        """Test that default log level is INFO."""
        monkeypatch.delenv('LOG_LEVEL', raising=False)
        logger = setup_logging('test.component')
        assert logger.level == logging.INFO
    
    def test_custom_log_level(self, monkeypatch):
        """Test that LOG_LEVEL environment variable is respected."""
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        logger = setup_logging('test.component.debug')
        assert logger.level == logging.DEBUG
    
    def test_invalid_log_level_defaults_to_info(self, monkeypatch):
        """Test that invalid LOG_LEVEL defaults to INFO."""
        monkeypatch.setenv('LOG_LEVEL', 'INVALID')
        logger = setup_logging('test.component.invalid')
        assert logger.level == logging.INFO
    
    def test_logger_has_handler(self):
        """Test that logger has a handler configured."""
        logger = setup_logging('test.component.handler')
        assert len(logger.handlers) > 0
    
    def test_logger_handler_has_formatter(self):
        """Test that logger handler has a formatter."""
        logger = setup_logging('test.component.formatter')
        handler = logger.handlers[0]
        assert handler.formatter is not None
    
    def test_formatter_includes_timestamp(self):
        """Test that formatter includes timestamp."""
        logger = setup_logging('test.component.timestamp')
        handler = logger.handlers[0]
        formatter = handler.formatter
        # Check that format string includes asctime
        assert '%(asctime)s' in formatter._fmt
    
    def test_formatter_includes_component_name(self):
        """Test that formatter includes component name."""
        logger = setup_logging('test.component.name')
        handler = logger.handlers[0]
        formatter = handler.formatter
        # Check that format string includes name
        assert '%(name)s' in formatter._fmt
    
    def test_formatter_includes_level(self):
        """Test that formatter includes log level."""
        logger = setup_logging('test.component.level')
        handler = logger.handlers[0]
        formatter = handler.formatter
        # Check that format string includes levelname
        assert '%(levelname)s' in formatter._fmt
    
    def test_different_components_get_different_loggers(self):
        """Test that different component names get different logger instances."""
        logger1 = setup_logging('component.one')
        logger2 = setup_logging('component.two')
        assert logger1.name != logger2.name
        assert logger1.name == 'component.one'
        assert logger2.name == 'component.two'
    
    def test_no_duplicate_handlers(self):
        """Test that calling setup_logging multiple times doesn't add duplicate handlers."""
        logger1 = setup_logging('test.component.duplicate')
        handler_count_1 = len(logger1.handlers)
        
        logger2 = setup_logging('test.component.duplicate')
        handler_count_2 = len(logger2.handlers)
        
        assert handler_count_1 == handler_count_2
        assert logger1 is logger2


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a properly configured logger."""
        logger = get_logger('test.module')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test.module'
        assert len(logger.handlers) > 0
    
    def test_get_logger_with_module_name(self):
        """Test that get_logger works with __name__ pattern."""
        logger = get_logger('src.rss_fetcher')
        assert logger.name == 'src.rss_fetcher'


class TestLoggingOutput:
    """Tests for actual logging output."""
    
    def test_log_message_format(self, monkeypatch, capsys):
        """Test that log messages are formatted correctly."""
        monkeypatch.setenv('LOG_LEVEL', 'INFO')
        logger = setup_logging('test.output')
        
        # Log a test message
        logger.info("Test message")
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify format: timestamp - component - level - message
        assert 'test.output' in captured.out
        assert 'INFO' in captured.out
        assert 'Test message' in captured.out
        # Check for timestamp pattern (YYYY-MM-DD HH:MM:SS)
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        assert re.search(timestamp_pattern, captured.out)
    
    def test_different_log_levels(self, monkeypatch, capsys):
        """Test that different log levels work correctly."""
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        logger = setup_logging('test.levels')
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        captured = capsys.readouterr()
        
        assert 'DEBUG' in captured.out
        assert 'INFO' in captured.out
        assert 'WARNING' in captured.out
        assert 'ERROR' in captured.out
    
    def test_log_level_filtering(self, monkeypatch, capsys):
        """Test that log level filtering works correctly."""
        monkeypatch.setenv('LOG_LEVEL', 'WARNING')
        logger = setup_logging('test.filtering')
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        captured = capsys.readouterr()
        
        # DEBUG and INFO should not appear
        assert 'Debug message' not in captured.out
        assert 'Info message' not in captured.out
        # WARNING and ERROR should appear
        assert 'Warning message' in captured.out
        assert 'Error message' in captured.out
