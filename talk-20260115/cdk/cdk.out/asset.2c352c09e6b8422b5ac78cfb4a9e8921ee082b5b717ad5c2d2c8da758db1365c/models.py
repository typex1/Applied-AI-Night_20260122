"""Data models for AWS LinkedIn Post Drafter."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class FeedItem:
    """Represents a single item from the RSS feed."""
    title: str
    description: str
    link: str
    pub_date: datetime
    guid: str  # Unique identifier from RSS feed


@dataclass
class PostDraft:
    """Represents a drafted LinkedIn post."""
    content: str  # Formatted LinkedIn post content
    hashtags: List[str]
    source_link: str
    source_title: str
    created_at: datetime
    guid: str  # Reference to original feed item


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""
    rss_feed_url: str
    keywords: List[str]
    sns_topic_arn: str
    daily_limit: int
    dynamodb_table_name: str
