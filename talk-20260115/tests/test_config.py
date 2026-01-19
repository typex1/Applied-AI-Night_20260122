"""Tests for configuration management."""

import os
import pytest

from src.config import load_config, parse_keywords, validate_config, ConfigurationError
from src.models import AppConfig


class TestParseKeywords:
    """Tests for keyword parsing."""
    
    def test_parse_simple_keywords(self):
        """Test parsing simple comma-separated keywords."""
        result = parse_keywords("Lambda,S3,DynamoDB")
        assert result == ["Lambda", "S3", "DynamoDB"]
    
    def test_parse_keywords_with_whitespace(self):
        """Test parsing keywords with extra whitespace."""
        result = parse_keywords("Lambda , S3 ,  DynamoDB  ")
        assert result == ["Lambda", "S3", "DynamoDB"]
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_keywords("")
        assert result == []
    
    def test_parse_keywords_filters_empty(self):
        """Test that empty keywords are filtered out."""
        result = parse_keywords("Lambda,,S3,  ,DynamoDB")
        assert result == ["Lambda", "S3", "DynamoDB"]


class TestValidateConfig:
    """Tests for configuration validation."""
    
    def test_valid_config(self):
        """Test that valid configuration passes validation."""
        config = AppConfig(
            rss_feed_url="https://aws.amazon.com/feed",
            keywords=["Lambda", "S3"],
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
            daily_limit=5,
            dynamodb_table_name="my-table"
        )
        # Should not raise
        validate_config(config)
    
    def test_missing_rss_feed_url(self):
        """Test that missing RSS_FEED_URL raises error."""
        config = AppConfig(
            rss_feed_url="",
            keywords=["Lambda"],
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
            daily_limit=5,
            dynamodb_table_name="my-table"
        )
        with pytest.raises(ConfigurationError, match="RSS_FEED_URL is required"):
            validate_config(config)
    
    def test_missing_keywords(self):
        """Test that missing KEYWORDS raises error."""
        config = AppConfig(
            rss_feed_url="https://aws.amazon.com/feed",
            keywords=[],
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
            daily_limit=5,
            dynamodb_table_name="my-table"
        )
        with pytest.raises(ConfigurationError, match="KEYWORDS is required"):
            validate_config(config)
    
    def test_missing_sns_topic_arn(self):
        """Test that missing SNS_TOPIC_ARN raises error."""
        config = AppConfig(
            rss_feed_url="https://aws.amazon.com/feed",
            keywords=["Lambda"],
            sns_topic_arn="",
            daily_limit=5,
            dynamodb_table_name="my-table"
        )
        with pytest.raises(ConfigurationError, match="SNS_TOPIC_ARN is required"):
            validate_config(config)
    
    def test_invalid_sns_topic_arn_format(self):
        """Test that invalid SNS_TOPIC_ARN format raises error."""
        config = AppConfig(
            rss_feed_url="https://aws.amazon.com/feed",
            keywords=["Lambda"],
            sns_topic_arn="invalid-arn",
            daily_limit=5,
            dynamodb_table_name="my-table"
        )
        with pytest.raises(ConfigurationError, match="SNS_TOPIC_ARN has invalid format"):
            validate_config(config)
    
    def test_missing_dynamodb_table_name(self):
        """Test that missing DYNAMODB_TABLE_NAME raises error."""
        config = AppConfig(
            rss_feed_url="https://aws.amazon.com/feed",
            keywords=["Lambda"],
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
            daily_limit=5,
            dynamodb_table_name=""
        )
        with pytest.raises(ConfigurationError, match="DYNAMODB_TABLE_NAME is required"):
            validate_config(config)
    
    def test_invalid_daily_limit(self):
        """Test that invalid DAILY_LIMIT raises error."""
        config = AppConfig(
            rss_feed_url="https://aws.amazon.com/feed",
            keywords=["Lambda"],
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
            daily_limit=0,
            dynamodb_table_name="my-table"
        )
        with pytest.raises(ConfigurationError, match="DAILY_LIMIT must be greater than 0"):
            validate_config(config)


class TestLoadConfig:
    """Tests for configuration loading."""
    
    def test_load_config_success(self, monkeypatch):
        """Test successful configuration loading."""
        monkeypatch.setenv('RSS_FEED_URL', 'https://aws.amazon.com/feed')
        monkeypatch.setenv('KEYWORDS', 'Lambda,S3,DynamoDB')
        monkeypatch.setenv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:my-topic')
        monkeypatch.setenv('DAILY_LIMIT', '5')
        monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'my-table')
        
        config = load_config()
        
        assert config.rss_feed_url == 'https://aws.amazon.com/feed'
        assert config.keywords == ['Lambda', 'S3', 'DynamoDB']
        assert config.sns_topic_arn == 'arn:aws:sns:us-east-1:123456789012:my-topic'
        assert config.daily_limit == 5
        assert config.dynamodb_table_name == 'my-table'
    
    def test_load_config_default_daily_limit(self, monkeypatch):
        """Test that DAILY_LIMIT defaults to 5."""
        monkeypatch.setenv('RSS_FEED_URL', 'https://aws.amazon.com/feed')
        monkeypatch.setenv('KEYWORDS', 'Lambda')
        monkeypatch.setenv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:my-topic')
        monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'my-table')
        monkeypatch.delenv('DAILY_LIMIT', raising=False)
        
        config = load_config()
        
        assert config.daily_limit == 5
    
    def test_load_config_invalid_daily_limit(self, monkeypatch):
        """Test that invalid DAILY_LIMIT raises error."""
        monkeypatch.setenv('RSS_FEED_URL', 'https://aws.amazon.com/feed')
        monkeypatch.setenv('KEYWORDS', 'Lambda')
        monkeypatch.setenv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:my-topic')
        monkeypatch.setenv('DAILY_LIMIT', 'not-a-number')
        monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'my-table')
        
        with pytest.raises(ConfigurationError, match="DAILY_LIMIT must be a valid integer"):
            load_config()
