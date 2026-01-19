"""RSS feed fetcher with retry logic for AWS LinkedIn Post Drafter."""

import time
from typing import List
from datetime import datetime
import feedparser
from src.models import FeedItem
from src.logging_config import logger


class FeedFetchError(Exception):
    """Raised when the RSS feed cannot be retrieved or parsed."""
    pass


def fetch_rss_feed(feed_url: str, max_attempts: int = 3, base_delay: float = 1.0) -> List[FeedItem]:
    """
    Fetches and parses the RSS feed from the given URL with retry logic.
    
    Implements exponential backoff retry strategy for transient failures.
    Gracefully handles malformed items by logging errors and continuing
    with valid items.
    
    Args:
        feed_url: The URL of the RSS feed
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        
    Returns:
        List of FeedItem objects containing title, description, link, and pub_date
        
    Raises:
        FeedFetchError: If the feed cannot be retrieved after all retry attempts
    """
    logger.info(f"Fetching RSS feed from {feed_url}")
    
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            # Fetch and parse the feed
            feed = feedparser.parse(feed_url)
            
            # Check for feed-level errors
            if hasattr(feed, 'bozo') and feed.bozo:
                # bozo flag indicates malformed feed, but we may still have entries
                if hasattr(feed, 'bozo_exception'):
                    logger.warning(
                        f"Feed has parsing issues: {feed.bozo_exception}. "
                        f"Attempting to process available entries."
                    )
            
            # Check if we got any entries
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                raise FeedFetchError(
                    f"No entries found in feed. Status: {getattr(feed, 'status', 'unknown')}"
                )
            
            logger.info(f"Successfully fetched feed with {len(feed.entries)} entries")
            
            # Parse entries into FeedItem objects
            feed_items = _parse_feed_entries(feed.entries)
            
            logger.info(f"Successfully parsed {len(feed_items)} valid feed items")
            return feed_items
            
        except FeedFetchError:
            # Re-raise FeedFetchError without retry
            raise
            
        except Exception as e:
            last_error = e
            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {type(e).__name__}: {e}"
            )
            
            # If this was the last attempt, raise the error
            if attempt == max_attempts - 1:
                raise FeedFetchError(
                    f"Failed to fetch RSS feed after {max_attempts} attempts: {e}"
                ) from last_error
            
            # Calculate exponential backoff delay
            delay = base_delay * (2 ** attempt)
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    # This should never be reached, but just in case
    raise FeedFetchError(
        f"Failed to fetch RSS feed after {max_attempts} attempts"
    ) from last_error


def _parse_feed_entries(entries: list) -> List[FeedItem]:
    """
    Parse RSS feed entries into FeedItem objects.
    
    Gracefully handles malformed items by logging errors and continuing
    with valid items. Invalid items are skipped.
    
    Args:
        entries: List of feed entries from feedparser
        
    Returns:
        List of successfully parsed FeedItem objects
    """
    feed_items = []
    
    for idx, entry in enumerate(entries):
        try:
            feed_item = _parse_single_entry(entry)
            feed_items.append(feed_item)
        except Exception as e:
            # Log the error and continue with other items
            logger.error(
                f"Failed to parse feed entry at index {idx}: {type(e).__name__}: {e}. "
                f"Entry title: {getattr(entry, 'title', 'unknown')}. Skipping."
            )
            continue
    
    return feed_items


def _parse_single_entry(entry) -> FeedItem:
    """
    Parse a single feed entry into a FeedItem object.
    
    Args:
        entry: A single feed entry from feedparser
        
    Returns:
        FeedItem object
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract title
    title = getattr(entry, 'title', '').strip()
    if not title:
        raise ValueError("Entry missing required field: title")
    
    # Extract description (may be in 'description' or 'summary')
    description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
    description = description.strip()
    if not description:
        raise ValueError("Entry missing required field: description/summary")
    
    # Extract link
    link = getattr(entry, 'link', '').strip()
    if not link:
        raise ValueError("Entry missing required field: link")
    
    # Extract GUID (use id or link as fallback)
    guid = getattr(entry, 'id', '') or link
    guid = guid.strip()
    if not guid:
        raise ValueError("Entry missing required field: guid/id")
    
    # Extract publication date
    pub_date = _parse_publication_date(entry)
    
    return FeedItem(
        title=title,
        description=description,
        link=link,
        pub_date=pub_date,
        guid=guid
    )


def _parse_publication_date(entry) -> datetime:
    """
    Parse publication date from feed entry.
    
    Tries multiple date fields in order of preference:
    - published_parsed
    - updated_parsed
    - created_parsed
    
    Args:
        entry: A single feed entry from feedparser
        
    Returns:
        datetime object representing the publication date
        
    Raises:
        ValueError: If no valid date field is found
    """
    # Try published_parsed first
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError) as e:
            logger.debug(f"Failed to parse published_parsed: {e}")
    
    # Try updated_parsed
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except (TypeError, ValueError) as e:
            logger.debug(f"Failed to parse updated_parsed: {e}")
    
    # Try created_parsed
    if hasattr(entry, 'created_parsed') and entry.created_parsed:
        try:
            return datetime(*entry.created_parsed[:6])
        except (TypeError, ValueError) as e:
            logger.debug(f"Failed to parse created_parsed: {e}")
    
    # If no date field is available, raise an error
    raise ValueError("Entry missing valid publication date field")
