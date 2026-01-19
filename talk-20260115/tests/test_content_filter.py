"""Tests for content filtering."""

import pytest
from datetime import datetime

from src.content_filter import filter_by_keywords
from src.models import FeedItem


class TestContentFilter:
    """Test suite for content filtering functionality."""
    
    def test_filter_by_keywords_matches_title(self):
        """Test that keywords in title are matched."""
        items = [
            FeedItem(
                title="AWS Lambda Announces New Feature",
                description="Some description",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            ),
            FeedItem(
                title="AWS S3 Update",
                description="Some description",
                link="https://example.com/2",
                pub_date=datetime.now(),
                guid="id-2"
            )
        ]
        keywords = ["Lambda"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 1
        assert result[0].title == "AWS Lambda Announces New Feature"
    
    def test_filter_by_keywords_matches_description(self):
        """Test that keywords in description are matched."""
        items = [
            FeedItem(
                title="AWS Update",
                description="This update includes Lambda improvements",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            ),
            FeedItem(
                title="AWS Update",
                description="This update includes S3 improvements",
                link="https://example.com/2",
                pub_date=datetime.now(),
                guid="id-2"
            )
        ]
        keywords = ["Lambda"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 1
        assert "Lambda" in result[0].description
    
    def test_filter_by_keywords_case_insensitive(self):
        """Test that keyword matching is case-insensitive."""
        items = [
            FeedItem(
                title="aws lambda update",
                description="lowercase description",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            ),
            FeedItem(
                title="AWS LAMBDA UPDATE",
                description="UPPERCASE DESCRIPTION",
                link="https://example.com/2",
                pub_date=datetime.now(),
                guid="id-2"
            )
        ]
        keywords = ["Lambda"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 2
    
    def test_filter_by_keywords_multiple_keywords(self):
        """Test filtering with multiple keywords (OR logic)."""
        items = [
            FeedItem(
                title="AWS Lambda Update",
                description="Description",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            ),
            FeedItem(
                title="AWS S3 Update",
                description="Description",
                link="https://example.com/2",
                pub_date=datetime.now(),
                guid="id-2"
            ),
            FeedItem(
                title="AWS EC2 Update",
                description="Description",
                link="https://example.com/3",
                pub_date=datetime.now(),
                guid="id-3"
            )
        ]
        keywords = ["Lambda", "S3"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 2
        assert any("Lambda" in item.title for item in result)
        assert any("S3" in item.title for item in result)
    
    def test_filter_by_keywords_no_matches(self):
        """Test that empty list is returned when no items match."""
        items = [
            FeedItem(
                title="AWS EC2 Update",
                description="Description",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            )
        ]
        keywords = ["Lambda", "S3"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 0
    
    def test_filter_by_keywords_empty_items(self):
        """Test that empty items list returns empty list."""
        items = []
        keywords = ["Lambda"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 0
    
    def test_filter_by_keywords_empty_keywords(self):
        """Test that empty keywords list returns empty list."""
        items = [
            FeedItem(
                title="AWS Lambda Update",
                description="Description",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            )
        ]
        keywords = []
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 0
    
    def test_filter_by_keywords_partial_match(self):
        """Test that partial keyword matches work (substring matching)."""
        items = [
            FeedItem(
                title="AWS Lambda Function Update",
                description="Description",
                link="https://example.com/1",
                pub_date=datetime.now(),
                guid="id-1"
            )
        ]
        keywords = ["Lambda"]
        
        result = filter_by_keywords(items, keywords)
        
        assert len(result) == 1
