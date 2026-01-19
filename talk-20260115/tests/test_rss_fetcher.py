"""Tests for RSS feed fetcher."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.rss_fetcher import (
    fetch_rss_feed,
    _parse_feed_entries,
    _parse_single_entry,
    _parse_publication_date,
    FeedFetchError
)
from src.models import FeedItem


class TestRSSFetcher:
    """Test suite for RSS feed fetcher functionality."""
    
    def test_parse_single_entry_success(self):
        """Test parsing a valid feed entry."""
        # Create a mock entry with all required fields
        entry = Mock()
        entry.title = "AWS Lambda Announces New Feature"
        entry.description = "AWS Lambda now supports Python 3.12"
        entry.link = "https://aws.amazon.com/about-aws/whats-new/2024/01/lambda-python-312"
        entry.id = "lambda-python-312"
        entry.published_parsed = (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        
        result = _parse_single_entry(entry)
        
        assert isinstance(result, FeedItem)
        assert result.title == "AWS Lambda Announces New Feature"
        assert result.description == "AWS Lambda now supports Python 3.12"
        assert result.link == "https://aws.amazon.com/about-aws/whats-new/2024/01/lambda-python-312"
        assert result.guid == "lambda-python-312"
        assert isinstance(result.pub_date, datetime)
    
    def test_parse_single_entry_missing_title(self):
        """Test that missing title raises ValueError."""
        entry = Mock()
        entry.title = ""
        entry.description = "Some description"
        entry.link = "https://example.com"
        entry.id = "test-id"
        
        with pytest.raises(ValueError, match="title"):
            _parse_single_entry(entry)
    
    def test_parse_single_entry_missing_description(self):
        """Test that missing description raises ValueError."""
        entry = Mock()
        entry.title = "Test Title"
        entry.description = ""
        entry.summary = ""
        entry.link = "https://example.com"
        entry.id = "test-id"
        
        with pytest.raises(ValueError, match="description"):
            _parse_single_entry(entry)
    
    def test_parse_single_entry_uses_summary_fallback(self):
        """Test that summary is used when description is missing."""
        entry = Mock()
        entry.title = "Test Title"
        entry.description = ""
        entry.summary = "Summary content"
        entry.link = "https://example.com"
        entry.id = "test-id"
        entry.published_parsed = (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        
        result = _parse_single_entry(entry)
        assert result.description == "Summary content"
    
    def test_parse_feed_entries_with_mixed_valid_invalid(self):
        """Test graceful handling of mixed valid and invalid entries."""
        # Create valid entry
        valid_entry = Mock()
        valid_entry.title = "Valid Entry"
        valid_entry.description = "Valid description"
        valid_entry.link = "https://example.com/valid"
        valid_entry.id = "valid-id"
        valid_entry.published_parsed = (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        
        # Create invalid entry (missing title)
        invalid_entry = Mock()
        invalid_entry.title = ""
        invalid_entry.description = "Invalid description"
        invalid_entry.link = "https://example.com/invalid"
        invalid_entry.id = "invalid-id"
        
        entries = [valid_entry, invalid_entry, valid_entry]
        
        result = _parse_feed_entries(entries)
        
        # Should return only the 2 valid entries
        assert len(result) == 2
        assert all(isinstance(item, FeedItem) for item in result)
        assert result[0].title == "Valid Entry"
        assert result[1].title == "Valid Entry"
    
    def test_parse_publication_date_with_published_parsed(self):
        """Test parsing publication date from published_parsed field."""
        entry = Mock()
        entry.published_parsed = (2024, 1, 15, 10, 30, 45, 0, 15, 0)
        
        result = _parse_publication_date(entry)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45
    
    def test_parse_publication_date_fallback_to_updated(self):
        """Test that updated_parsed is used when published_parsed is missing."""
        entry = Mock()
        entry.published_parsed = None
        entry.updated_parsed = (2024, 2, 20, 14, 15, 30, 0, 51, 0)
        
        result = _parse_publication_date(entry)
        
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 20
    
    def test_parse_publication_date_missing_all_fields(self):
        """Test that missing date fields raises ValueError."""
        entry = Mock()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.created_parsed = None
        
        with pytest.raises(ValueError, match="publication date"):
            _parse_publication_date(entry)
    
    @patch('src.rss_fetcher.feedparser.parse')
    def test_fetch_rss_feed_success(self, mock_parse):
        """Test successful RSS feed fetch."""
        # Create mock feed with entries
        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = [
            Mock(
                title="Entry 1",
                description="Description 1",
                link="https://example.com/1",
                id="id-1",
                published_parsed=(2024, 1, 15, 10, 0, 0, 0, 15, 0)
            )
        ]
        mock_parse.return_value = mock_feed
        
        result = fetch_rss_feed("https://example.com/feed")
        
        assert len(result) == 1
        assert result[0].title == "Entry 1"
        mock_parse.assert_called_once_with("https://example.com/feed")
    
    @patch('src.rss_fetcher.feedparser.parse')
    def test_fetch_rss_feed_no_entries(self, mock_parse):
        """Test that empty feed raises FeedFetchError."""
        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = []
        mock_parse.return_value = mock_feed
        
        with pytest.raises(FeedFetchError, match="No entries found"):
            fetch_rss_feed("https://example.com/feed")
    
    @patch('src.rss_fetcher.feedparser.parse')
    @patch('src.rss_fetcher.time.sleep')
    def test_fetch_rss_feed_retry_on_exception(self, mock_sleep, mock_parse):
        """Test retry logic with exponential backoff."""
        # First two attempts fail, third succeeds
        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = [
            Mock(
                title="Entry 1",
                description="Description 1",
                link="https://example.com/1",
                id="id-1",
                published_parsed=(2024, 1, 15, 10, 0, 0, 0, 15, 0)
            )
        ]
        
        mock_parse.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_feed
        ]
        
        result = fetch_rss_feed("https://example.com/feed")
        
        assert len(result) == 1
        assert mock_parse.call_count == 3
        assert mock_sleep.call_count == 2
        # Check exponential backoff: 1s, 2s
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)
    
    @patch('src.rss_fetcher.feedparser.parse')
    @patch('src.rss_fetcher.time.sleep')
    def test_fetch_rss_feed_fails_after_max_attempts(self, mock_sleep, mock_parse):
        """Test that FeedFetchError is raised after max retry attempts."""
        mock_parse.side_effect = Exception("Persistent error")
        
        with pytest.raises(FeedFetchError, match="Failed to fetch RSS feed after 3 attempts"):
            fetch_rss_feed("https://example.com/feed")
        
        assert mock_parse.call_count == 3
        assert mock_sleep.call_count == 2
