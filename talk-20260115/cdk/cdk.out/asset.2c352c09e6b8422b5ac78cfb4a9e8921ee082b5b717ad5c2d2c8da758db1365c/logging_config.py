"""Logging configuration for AWS LinkedIn Post Drafter."""

import logging
import os
import sys


def setup_logging(component_name: str = 'aws-linkedin-post-drafter') -> logging.Logger:
    """
    Configure and return a logger for the specified component.
    
    This function sets up structured logging with:
    - Timestamps in YYYY-MM-DD HH:MM:SS format
    - Component names for identifying log sources
    - Configurable log levels via LOG_LEVEL environment variable
    - Consistent formatting across all components
    
    Args:
        component_name: Name of the component (module) requesting the logger
    
    Returns:
        Configured logger instance for the component
    """
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Get or create logger for this component
    logger = logging.getLogger(component_name)
    
    # Only configure if not already configured (avoid duplicate handlers)
    if not logger.handlers:
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create formatter with timestamp and component name
        # Format: YYYY-MM-DD HH:MM:SS - component.name - LEVEL - message
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False
    
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    This is the recommended way to get a logger in application code.
    It creates a hierarchical logger name that includes the module path.
    
    Args:
        module_name: The __name__ of the calling module
    
    Returns:
        Configured logger instance for the module
    
    Example:
        >>> from src.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("This is a log message")
    """
    return setup_logging(module_name)


# Create default logger instance for backward compatibility
logger = setup_logging('aws-linkedin-post-drafter')
