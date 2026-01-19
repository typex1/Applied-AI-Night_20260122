"""LinkedIn post draft generator for AWS LinkedIn Post Drafter."""

import re
from datetime import datetime
from typing import List, Set

from src.models import FeedItem, PostDraft
from src.logging_config import logger


# LinkedIn character limit
LINKEDIN_CHARACTER_LIMIT = 3000


def draft_linkedin_post(item: FeedItem, processed_guids: Set[str] = None) -> PostDraft:
    """
    Creates a LinkedIn post draft from a feed item.
    
    Formats the content to be LinkedIn-friendly with a maximum of 3000 characters.
    Extracts relevant hashtags from the content and includes the original AWS news link.
    Checks for duplicates using the item's GUID.
    
    Args:
        item: The feed item to transform
        processed_guids: Set of GUIDs that have already been processed (for deduplication)
        
    Returns:
        PostDraft object containing formatted content, hashtags, and metadata
        
    Raises:
        ValueError: If the item has already been processed (duplicate GUID)
    """
    # Check for duplicates
    if processed_guids is not None and item.guid in processed_guids:
        logger.warning(f"Duplicate item detected: {item.guid}. Skipping.")
        raise ValueError(f"Item with GUID {item.guid} has already been processed")
    
    logger.info(f"Drafting LinkedIn post for: {item.title}")
    
    # Extract hashtags from the content
    hashtags = _extract_hashtags(item)
    
    # Format the post content
    content = _format_post_content(item, hashtags)
    
    # Create the PostDraft object
    draft = PostDraft(
        content=content,
        hashtags=hashtags,
        source_link=item.link,
        source_title=item.title,
        created_at=datetime.now(),
        guid=item.guid
    )
    
    logger.info(
        f"Successfully drafted post with {len(content)} characters "
        f"and {len(hashtags)} hashtags"
    )
    
    return draft


def _extract_hashtags(item: FeedItem) -> List[str]:
    """
    Extract relevant hashtags from the feed item content.
    
    Identifies AWS services, technologies, and relevant keywords from the
    title and description to generate appropriate hashtags.
    
    Args:
        item: The feed item to extract hashtags from
        
    Returns:
        List of hashtags (including the # symbol)
    """
    hashtags = []
    
    # Always include #AWS
    hashtags.append("#AWS")
    
    # Common AWS services and technologies to look for
    aws_services = [
        "Lambda", "S3", "EC2", "DynamoDB", "RDS", "CloudFormation",
        "CloudWatch", "SNS", "SQS", "ECS", "EKS", "Fargate",
        "API Gateway", "Step Functions", "EventBridge", "Kinesis",
        "Redshift", "Athena", "Glue", "SageMaker", "Bedrock",
        "CodePipeline", "CodeBuild", "CodeDeploy", "CloudFront",
        "Route 53", "VPC", "IAM", "KMS", "Secrets Manager",
        "AppSync", "Amplify", "Cognito", "ElastiCache", "Neptune"
    ]
    
    # Combine title and description for searching
    combined_text = f"{item.title} {item.description}"
    
    # Search for AWS services (case-insensitive)
    for service in aws_services:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(service) + r'\b'
        if re.search(pattern, combined_text, re.IGNORECASE):
            # Convert to hashtag format (remove spaces, capitalize words)
            hashtag = "#" + service.replace(" ", "")
            if hashtag not in hashtags:
                hashtags.append(hashtag)
    
    # Look for common technology keywords
    tech_keywords = [
        "AI", "MachineLearning", "ML", "Serverless", "Container",
        "Kubernetes", "Docker", "DevOps", "Cloud", "Security",
        "Database", "Analytics", "BigData", "IoT", "Edge"
    ]
    
    for keyword in tech_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, combined_text, re.IGNORECASE):
            hashtag = "#" + keyword
            if hashtag not in hashtags:
                hashtags.append(hashtag)
    
    # Limit to a reasonable number of hashtags (5-7 is typical for LinkedIn)
    if len(hashtags) > 7:
        hashtags = hashtags[:7]
    
    logger.debug(f"Extracted {len(hashtags)} hashtags: {', '.join(hashtags)}")
    
    return hashtags


def _format_post_content(item: FeedItem, hashtags: List[str]) -> str:
    """
    Format the feed item into LinkedIn-friendly post content.
    
    Creates an engaging post with the title, summary, link, and hashtags
    while enforcing the 3000 character limit.
    
    Args:
        item: The feed item to format
        hashtags: List of hashtags to include
        
    Returns:
        Formatted post content as a string (max 3000 characters)
    """
    # Create an engaging opening
    opening = "🚀 AWS News Update!\n\n"
    
    # Add the title
    title_section = f"📢 {item.title}\n\n"
    
    # Add the description/summary
    # Clean up HTML tags if present
    description = _clean_html(item.description)
    
    # Add the link
    link_section = f"\n\n🔗 Read more: {item.link}\n\n"
    
    # Add hashtags
    hashtag_section = " ".join(hashtags)
    
    # Calculate available space for description
    fixed_content_length = (
        len(opening) + len(title_section) + len(link_section) + len(hashtag_section)
    )
    
    available_space = LINKEDIN_CHARACTER_LIMIT - fixed_content_length
    
    # Truncate description if necessary
    if len(description) > available_space:
        # Leave room for ellipsis
        description = description[:available_space - 3].rsplit(' ', 1)[0] + "..."
        logger.debug(f"Truncated description to fit character limit")
    
    # Assemble the final content
    content = opening + title_section + description + link_section + hashtag_section
    
    # Final safety check
    if len(content) > LINKEDIN_CHARACTER_LIMIT:
        # This shouldn't happen, but just in case
        content = content[:LINKEDIN_CHARACTER_LIMIT - 3] + "..."
        logger.warning(f"Content exceeded limit, truncated to {LINKEDIN_CHARACTER_LIMIT} characters")
    
    return content


def _clean_html(text: str) -> str:
    """
    Remove HTML tags and clean up text for LinkedIn.
    
    Args:
        text: Text that may contain HTML tags
        
    Returns:
        Cleaned text without HTML tags
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
        '&#39;': "'"
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text
