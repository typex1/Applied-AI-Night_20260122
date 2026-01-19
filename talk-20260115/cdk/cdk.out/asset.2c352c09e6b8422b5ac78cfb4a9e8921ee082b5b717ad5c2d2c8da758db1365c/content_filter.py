"""Content filtering for AWS LinkedIn Post Drafter."""

from typing import List

from src.models import FeedItem
from src.logging_config import logger


def filter_by_keywords(items: List[FeedItem], keywords: List[str]) -> List[FeedItem]:
    """
    Filters feed items that match any of the provided keywords.
    
    Performs case-insensitive keyword matching against both the title
    and description fields of each feed item. Returns items that contain
    at least one keyword in either field.
    
    Args:
        items: List of feed items to filter
        keywords: List of keywords to match (case-insensitive)
        
    Returns:
        List of feed items that contain at least one keyword in title or description
    """
    if not items:
        logger.info("No items to filter")
        return []
    
    if not keywords:
        logger.warning("No keywords provided, returning empty list")
        return []
    
    # Convert keywords to lowercase for case-insensitive matching
    keywords_lower = [kw.lower() for kw in keywords]
    
    filtered_items = []
    
    for item in items:
        # Convert title and description to lowercase for matching
        title_lower = item.title.lower()
        description_lower = item.description.lower()
        
        # Check if any keyword appears in title or description
        matches = False
        for keyword in keywords_lower:
            if keyword in title_lower or keyword in description_lower:
                matches = True
                break
        
        if matches:
            filtered_items.append(item)
    
    logger.info(
        f"Filtered {len(filtered_items)} items from {len(items)} "
        f"using {len(keywords)} keywords"
    )
    
    return filtered_items
