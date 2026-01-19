"""SNS email sender for AWS LinkedIn Post Drafter."""

import time
import json
from typing import Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from models import PostDraft
from logging_config import logger


class SNSPublishError(Exception):
    """Raised when SNS publish fails after all retry attempts."""
    pass


def send_via_sns(draft: PostDraft, topic_arn: str, max_attempts: int = 3, base_delay: float = 1.0) -> bool:
    """
    Publishes a post draft to the configured SNS topic.
    
    Formats the draft as a structured email message with a subject line
    containing the news title. Implements retry logic with exponential
    backoff for transient failures.
    
    Args:
        draft: The post draft to send
        topic_arn: ARN of the SNS topic
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        SNSPublishError: If all retry attempts fail
    """
    logger.info(f"Publishing post draft to SNS topic: {topic_arn}")
    logger.debug(f"Draft GUID: {draft.guid}, Title: {draft.source_title}")
    
    # Create SNS client
    sns_client = boto3.client('sns')
    
    # Format the message
    subject = _format_subject(draft)
    message = _format_message(draft)
    
    # Retry with exponential backoff
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"SNS publish attempt {attempt + 1}/{max_attempts}")
            
            # Publish to SNS
            response = sns_client.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
            
            message_id = response.get('MessageId', 'unknown')
            logger.info(f"Successfully published to SNS. MessageId: {message_id}")
            
            return True
            
        except (ClientError, BotoCoreError) as e:
            last_exception = e
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            error_message = str(e)
            
            logger.warning(
                f"SNS publish attempt {attempt + 1}/{max_attempts} failed. "
                f"Error: {error_code} - {error_message}"
            )
            
            # If this was the last attempt, don't sleep
            if attempt == max_attempts - 1:
                break
            
            # Calculate exponential backoff delay
            delay = base_delay * (2 ** attempt)
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    # All attempts failed
    logger.error(
        f"Failed to publish to SNS after {max_attempts} attempts. "
        f"Last error: {last_exception}"
    )
    
    raise SNSPublishError(
        f"Failed to publish to SNS after {max_attempts} attempts: {last_exception}"
    )


def _format_subject(draft: PostDraft) -> str:
    """
    Format the email subject line.
    
    Creates a subject line with the format:
    "LinkedIn Post Draft: [News Title]"
    
    Args:
        draft: The post draft
        
    Returns:
        Formatted subject line
    """
    # Truncate title if too long (email subjects should be < 78 chars ideally)
    max_title_length = 60
    title = draft.source_title
    
    if len(title) > max_title_length:
        title = title[:max_title_length - 3] + "..."
    
    subject = f"LinkedIn Post Draft: {title}"
    
    return subject


def _format_message(draft: PostDraft) -> str:
    """
    Format the email message body.
    
    Creates a structured message containing:
    - Complete draft content
    - Original AWS news link
    - Publication date
    - Metadata (GUID, hashtags, created timestamp)
    
    Args:
        draft: The post draft
        
    Returns:
        Formatted message body
    """
    # Format the message with clear sections
    message_parts = [
        "=" * 70,
        "LINKEDIN POST DRAFT",
        "=" * 70,
        "",
        "DRAFT CONTENT:",
        "-" * 70,
        draft.content,
        "",
        "=" * 70,
        "METADATA",
        "=" * 70,
        "",
        f"Original Title: {draft.source_title}",
        f"Source Link: {draft.source_link}",
        f"Hashtags: {', '.join(draft.hashtags)}",
        f"Draft Created: {draft.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Item GUID: {draft.guid}",
        "",
        "=" * 70,
        "",
        "To publish this post:",
        "1. Review the content above",
        "2. Copy the draft content section",
        "3. Paste into LinkedIn",
        "4. Make any final adjustments",
        "5. Publish!",
        "",
        "=" * 70,
    ]
    
    message = "\n".join(message_parts)
    
    return message

