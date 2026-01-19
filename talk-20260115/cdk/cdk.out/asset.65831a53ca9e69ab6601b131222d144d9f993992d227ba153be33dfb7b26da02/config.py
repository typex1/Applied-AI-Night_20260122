"""Configuration management for AWS LinkedIn Post Drafter."""

import os
import re
from typing import List

from src.models import AppConfig
from src.logging_config import logger


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config() -> AppConfig:
    """
    Load application configuration from environment variables.
    
    Reads the following environment variables:
    - RSS_FEED_URL: URL of the AWS RSS feed
    - KEYWORDS: Comma-separated list of keywords
    - SNS_TOPIC_ARN: ARN of the SNS topic
    - DAILY_LIMIT: Maximum posts per day (default: 5)
    - DYNAMODB_TABLE_NAME: Name of the DynamoDB table
    
    Returns:
        AppConfig object with loaded configuration
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    logger.info("Loading configuration from environment variables")
    
    # Load required environment variables
    rss_feed_url = os.environ.get('RSS_FEED_URL', '').strip()
    keywords_str = os.environ.get('KEYWORDS', '').strip()
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', '').strip()
    daily_limit_str = os.environ.get('DAILY_LIMIT', '5').strip()
    dynamodb_table_name = os.environ.get('DYNAMODB_TABLE_NAME', '').strip()
    
    # Parse comma-separated keywords into list
    keywords = parse_keywords(keywords_str)
    
    # Parse daily limit
    try:
        daily_limit = int(daily_limit_str)
    except ValueError:
        raise ConfigurationError(
            f"DAILY_LIMIT must be a valid integer, got: {daily_limit_str}"
        )
    
    # Create config object
    config = AppConfig(
        rss_feed_url=rss_feed_url,
        keywords=keywords,
        sns_topic_arn=sns_topic_arn,
        daily_limit=daily_limit,
        dynamodb_table_name=dynamodb_table_name
    )
    
    # Validate configuration
    validate_config(config)
    
    logger.info(f"Configuration loaded successfully with {len(keywords)} keywords")
    return config


def parse_keywords(keywords_str: str) -> List[str]:
    """
    Parse comma-separated keyword string into a list of keywords.
    
    Splits on commas and trims whitespace from each keyword.
    Empty keywords are filtered out.
    
    Args:
        keywords_str: Comma-separated keyword string
        
    Returns:
        List of trimmed keywords
    """
    if not keywords_str:
        return []
    
    # Split by comma and trim whitespace
    keywords = [kw.strip() for kw in keywords_str.split(',')]
    
    # Filter out empty strings
    keywords = [kw for kw in keywords if kw]
    
    return keywords


def validate_config(config: AppConfig) -> None:
    """
    Validate that configuration contains all required fields with valid values.
    
    Args:
        config: AppConfig object to validate
        
    Raises:
        ConfigurationError: If any required field is missing or invalid
    """
    # Validate RSS_FEED_URL
    if not config.rss_feed_url:
        raise ConfigurationError(
            "RSS_FEED_URL is required but not set or empty"
        )
    
    # Validate KEYWORDS
    if not config.keywords:
        raise ConfigurationError(
            "KEYWORDS is required but not set or empty"
        )
    
    # Validate SNS_TOPIC_ARN
    if not config.sns_topic_arn:
        raise ConfigurationError(
            "SNS_TOPIC_ARN is required but not set or empty"
        )
    
    # Validate SNS_TOPIC_ARN format (must be a valid ARN)
    arn_pattern = r'^arn:aws:sns:[a-z0-9-]+:\d{12}:[a-zA-Z0-9_-]+$'
    if not re.match(arn_pattern, config.sns_topic_arn):
        raise ConfigurationError(
            f"SNS_TOPIC_ARN has invalid format: {config.sns_topic_arn}. "
            f"Expected format: arn:aws:sns:region:account-id:topic-name"
        )
    
    # Validate DYNAMODB_TABLE_NAME
    if not config.dynamodb_table_name:
        raise ConfigurationError(
            "DYNAMODB_TABLE_NAME is required but not set or empty"
        )
    
    # Validate DAILY_LIMIT
    if config.daily_limit <= 0:
        raise ConfigurationError(
            f"DAILY_LIMIT must be greater than 0, got: {config.daily_limit}"
        )
    
    logger.debug("Configuration validation passed")
