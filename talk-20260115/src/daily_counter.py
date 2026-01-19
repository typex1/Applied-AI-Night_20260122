"""Daily counter manager for tracking post limits using DynamoDB."""

from datetime import datetime, timezone
import time
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from logging_config import logger


class DailyLimitExceeded(Exception):
    """Raised when attempting to increment counter beyond daily limit."""
    pass


class DailyCounterManager:
    """
    Manages daily post counter using DynamoDB.
    
    Uses atomic operations to track the number of posts sent per day
    and enforce the daily limit.
    """
    
    def __init__(self, table_name: str, daily_limit: int):
        """
        Initialize the daily counter manager.
        
        Args:
            table_name: Name of the DynamoDB table
            daily_limit: Maximum number of posts allowed per day
        """
        self.table_name = table_name
        self.daily_limit = daily_limit
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Initialized DailyCounterManager with table={table_name}, limit={daily_limit}")
    
    def get_daily_count(self, date: Optional[str] = None) -> int:
        """
        Retrieve the current count of posts sent for the given date.
        
        Args:
            date: Date string in YYYY-MM-DD format. If None, uses today's date.
            
        Returns:
            Number of posts sent on that date (0 if no record exists)
        """
        if date is None:
            date = self._get_today_date()
        
        try:
            logger.debug(f"Querying daily count for date={date}")
            response = self.table.get_item(Key={'date': date})
            
            if 'Item' in response:
                count = response['Item'].get('count', 0)
                # Ensure count is an integer (DynamoDB returns Decimal)
                count = int(count)
                logger.info(f"Daily count for {date}: {count}")
                return count
            else:
                logger.info(f"No record found for {date}, returning 0")
                return 0
                
        except ClientError as e:
            logger.error(f"Error querying daily count: {e}")
            raise
    
    def increment_daily_count(self, date: Optional[str] = None) -> int:
        """
        Atomically increment the daily counter and return the new count.
        
        Uses conditional updates to prevent race conditions and enforce
        the daily limit.
        
        Args:
            date: Date string in YYYY-MM-DD format. If None, uses today's date.
            
        Returns:
            New count after increment
            
        Raises:
            DailyLimitExceeded: If incrementing would exceed the daily limit
        """
        if date is None:
            date = self._get_today_date()
        
        # Calculate TTL (7 days from now)
        ttl = int(time.time()) + (7 * 24 * 60 * 60)
        
        try:
            logger.debug(f"Attempting to increment counter for date={date}")
            
            # Use atomic update with condition to prevent exceeding limit
            # This ensures thread-safety and prevents race conditions
            response = self.table.update_item(
                Key={'date': date},
                UpdateExpression='SET #count = if_not_exists(#count, :zero) + :inc, #ttl = :ttl',
                ConditionExpression='attribute_not_exists(#count) OR #count < :limit',
                ExpressionAttributeNames={
                    '#count': 'count',
                    '#ttl': 'ttl'
                },
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':inc': 1,
                    ':limit': self.daily_limit,
                    ':ttl': ttl
                },
                ReturnValues='UPDATED_NEW'
            )
            
            new_count = int(response['Attributes']['count'])
            logger.info(f"Successfully incremented counter for {date}: {new_count}/{self.daily_limit}")
            return new_count
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ConditionalCheckFailedException':
                # Limit has been reached
                current_count = self.get_daily_count(date)
                logger.warning(
                    f"Daily limit reached for {date}: {current_count}/{self.daily_limit}"
                )
                raise DailyLimitExceeded(
                    f"Daily limit of {self.daily_limit} posts has been reached for {date}"
                )
            else:
                logger.error(f"Error incrementing daily count: {e}")
                raise
    
    def can_send_more_posts(self, date: Optional[str] = None) -> bool:
        """
        Check if more posts can be sent today.
        
        Args:
            date: Date string in YYYY-MM-DD format. If None, uses today's date.
            
        Returns:
            True if count < daily_limit, False otherwise
        """
        if date is None:
            date = self._get_today_date()
        
        current_count = self.get_daily_count(date)
        can_send = current_count < self.daily_limit
        
        logger.info(
            f"Can send more posts for {date}: {can_send} "
            f"(current: {current_count}/{self.daily_limit})"
        )
        
        return can_send
    
    def _get_today_date(self) -> str:
        """
        Get today's date in YYYY-MM-DD format (UTC).
        
        Returns:
            Date string in YYYY-MM-DD format
        """
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def get_daily_count(table_name: str, date: Optional[str] = None) -> int:
    """
    Convenience function to get daily count without creating a manager instance.
    
    Args:
        table_name: Name of the DynamoDB table
        date: Date string in YYYY-MM-DD format. If None, uses today's date.
        
    Returns:
        Number of posts sent on that date
    """
    # Note: This creates a new manager instance each time.
    # For production use, consider reusing a manager instance.
    manager = DailyCounterManager(table_name, daily_limit=5)
    return manager.get_daily_count(date)


def increment_daily_count(table_name: str, daily_limit: int, date: Optional[str] = None) -> int:
    """
    Convenience function to increment daily count without creating a manager instance.
    
    Args:
        table_name: Name of the DynamoDB table
        daily_limit: Maximum posts per day
        date: Date string in YYYY-MM-DD format. If None, uses today's date.
        
    Returns:
        New count after increment
        
    Raises:
        DailyLimitExceeded: If incrementing would exceed the daily limit
    """
    manager = DailyCounterManager(table_name, daily_limit)
    return manager.increment_daily_count(date)


def can_send_more_posts(table_name: str, daily_limit: int, date: Optional[str] = None) -> bool:
    """
    Convenience function to check if more posts can be sent.
    
    Args:
        table_name: Name of the DynamoDB table
        daily_limit: Maximum posts per day
        date: Date string in YYYY-MM-DD format. If None, uses today's date.
        
    Returns:
        True if count < daily_limit, False otherwise
    """
    manager = DailyCounterManager(table_name, daily_limit)
    return manager.can_send_more_posts(date)
