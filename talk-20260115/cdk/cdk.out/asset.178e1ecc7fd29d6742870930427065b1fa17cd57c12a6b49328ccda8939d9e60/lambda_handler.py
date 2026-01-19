"""Main Lambda handler for AWS LinkedIn Post Drafter."""

from typing import Dict, Any, Set
from datetime import datetime

from config import load_config, ConfigurationError
from rss_fetcher import fetch_rss_feed, FeedFetchError
from content_filter import filter_by_keywords
from post_drafter import draft_linkedin_post
from daily_counter import DailyCounterManager, DailyLimitExceeded
from email_sender import send_via_sns, SNSPublishError
from logging_config import get_logger


logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function triggered by EventBridge.
    
    Orchestrates the complete workflow:
    1. Load configuration from environment variables
    2. Check if daily limit has been reached
    3. Fetch RSS feed from AWS
    4. Filter items by configured keywords
    5. Draft and send posts (up to remaining daily limit)
    6. Handle errors gracefully
    7. Return execution summary
    
    Args:
        event: EventBridge event payload
        context: Lambda execution context
        
    Returns:
        Response dict with status and summary containing:
        - status: 'success' or 'error'
        - posts_sent: Number of posts successfully sent
        - posts_failed: Number of posts that failed to send
        - items_fetched: Number of items fetched from RSS feed
        - items_filtered: Number of items after filtering
        - daily_limit_reached: Whether the daily limit was reached
        - errors: List of error messages (if any)
        - message: Human-readable summary message
    """
    logger.info("=" * 70)
    logger.info("AWS LinkedIn Post Drafter - Execution Started")
    logger.info("=" * 70)
    
    # Initialize execution summary
    summary = {
        'status': 'success',
        'posts_sent': 0,
        'posts_failed': 0,
        'items_fetched': 0,
        'items_filtered': 0,
        'daily_limit_reached': False,
        'errors': [],
        'message': ''
    }
    
    try:
        # Step 1: Load configuration
        logger.info("Step 1: Loading configuration")
        try:
            config = load_config()
            logger.info(f"Configuration loaded: {len(config.keywords)} keywords, limit={config.daily_limit}")
        except ConfigurationError as e:
            error_msg = f"Configuration error: {e}"
            logger.error(error_msg)
            summary['status'] = 'error'
            summary['errors'].append(error_msg)
            summary['message'] = 'Failed to load configuration'
            return summary
        
        # Step 2: Check daily limit
        logger.info("Step 2: Checking daily limit")
        counter_manager = DailyCounterManager(
            table_name=config.dynamodb_table_name,
            daily_limit=config.daily_limit
        )
        
        if not counter_manager.can_send_more_posts():
            logger.info(f"Daily limit of {config.daily_limit} posts already reached. Skipping execution.")
            summary['daily_limit_reached'] = True
            summary['message'] = f'Daily limit of {config.daily_limit} posts already reached'
            return summary
        
        current_count = counter_manager.get_daily_count()
        remaining_slots = config.daily_limit - current_count
        logger.info(f"Current count: {current_count}/{config.daily_limit}, remaining slots: {remaining_slots}")
        
        # Step 3: Fetch RSS feed
        logger.info("Step 3: Fetching RSS feed")
        try:
            feed_items = fetch_rss_feed(config.rss_feed_url)
            summary['items_fetched'] = len(feed_items)
            logger.info(f"Fetched {len(feed_items)} items from RSS feed")
        except FeedFetchError as e:
            error_msg = f"Failed to fetch RSS feed: {e}"
            logger.error(error_msg)
            summary['status'] = 'error'
            summary['errors'].append(error_msg)
            summary['message'] = 'Failed to fetch RSS feed'
            return summary
        
        # Step 4: Filter by keywords
        logger.info("Step 4: Filtering items by keywords")
        filtered_items = filter_by_keywords(feed_items, config.keywords)
        summary['items_filtered'] = len(filtered_items)
        logger.info(f"Filtered to {len(filtered_items)} relevant items")
        
        if not filtered_items:
            logger.info("No items matched the configured keywords")
            summary['message'] = 'No items matched the configured keywords'
            return summary
        
        # Step 5: Draft and send posts (up to remaining limit)
        logger.info(f"Step 5: Drafting and sending posts (max {remaining_slots})")
        
        # Track processed GUIDs for deduplication
        processed_guids: Set[str] = set()
        
        # Process items up to the remaining daily limit
        items_to_process = filtered_items[:remaining_slots]
        logger.info(f"Processing {len(items_to_process)} items")
        
        for idx, item in enumerate(items_to_process, 1):
            logger.info(f"Processing item {idx}/{len(items_to_process)}: {item.title}")
            
            try:
                # Draft the post
                draft = draft_linkedin_post(item, processed_guids)
                processed_guids.add(item.guid)
                
                # Increment the daily counter (atomic operation)
                try:
                    counter_manager.increment_daily_count()
                except DailyLimitExceeded:
                    logger.warning("Daily limit reached during processing")
                    summary['daily_limit_reached'] = True
                    break
                
                # Send via SNS
                send_via_sns(draft, config.sns_topic_arn)
                summary['posts_sent'] += 1
                logger.info(f"Successfully sent post {idx}/{len(items_to_process)}")
                
            except ValueError as e:
                # Duplicate item or validation error
                error_msg = f"Skipping item '{item.title}': {e}"
                logger.warning(error_msg)
                summary['errors'].append(error_msg)
                continue
                
            except SNSPublishError as e:
                # SNS publish failed after retries
                error_msg = f"Failed to send post for '{item.title}': {e}"
                logger.error(error_msg)
                summary['posts_failed'] += 1
                summary['errors'].append(error_msg)
                # Continue with next item
                continue
                
            except Exception as e:
                # Unexpected error
                error_msg = f"Unexpected error processing '{item.title}': {type(e).__name__}: {e}"
                logger.error(error_msg, exc_info=True)
                summary['posts_failed'] += 1
                summary['errors'].append(error_msg)
                # Continue with next item
                continue
        
        # Generate summary message
        if summary['posts_sent'] > 0:
            summary['message'] = f"Successfully sent {summary['posts_sent']} post(s)"
            if summary['posts_failed'] > 0:
                summary['message'] += f", {summary['posts_failed']} failed"
        elif summary['posts_failed'] > 0:
            summary['status'] = 'error'
            summary['message'] = f"All {summary['posts_failed']} post(s) failed to send"
        else:
            summary['message'] = 'No posts were sent'
        
        logger.info("=" * 70)
        logger.info(f"Execution Summary: {summary['message']}")
        logger.info(f"Posts sent: {summary['posts_sent']}, Failed: {summary['posts_failed']}")
        logger.info(f"Items fetched: {summary['items_fetched']}, Filtered: {summary['items_filtered']}")
        logger.info("=" * 70)
        
        return summary
        
    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error in lambda_handler: {type(e).__name__}: {e}"
        logger.error(error_msg, exc_info=True)
        summary['status'] = 'error'
        summary['errors'].append(error_msg)
        summary['message'] = 'Execution failed due to unexpected error'
        return summary
