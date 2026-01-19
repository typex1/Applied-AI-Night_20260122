"""Tests for daily counter manager."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.daily_counter import (
    DailyCounterManager,
    DailyLimitExceeded,
    get_daily_count,
    increment_daily_count,
    can_send_more_posts
)


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    table = Mock()
    return table


@pytest.fixture
def counter_manager(mock_dynamodb_table):
    """Create a DailyCounterManager with mocked DynamoDB."""
    with patch('src.daily_counter.boto3') as mock_boto3:
        mock_resource = Mock()
        mock_boto3.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_dynamodb_table
        
        manager = DailyCounterManager(table_name='test-table', daily_limit=5)
        manager.table = mock_dynamodb_table
        return manager


class TestDailyCounterManager:
    """Test suite for DailyCounterManager."""
    
    def test_get_daily_count_existing_record(self, counter_manager, mock_dynamodb_table):
        """Test getting count when record exists."""
        mock_dynamodb_table.get_item.return_value = {
            'Item': {'date': '2026-01-15', 'count': 3}
        }
        
        count = counter_manager.get_daily_count('2026-01-15')
        
        assert count == 3
        mock_dynamodb_table.get_item.assert_called_once_with(Key={'date': '2026-01-15'})
    
    def test_get_daily_count_no_record(self, counter_manager, mock_dynamodb_table):
        """Test getting count when no record exists."""
        mock_dynamodb_table.get_item.return_value = {}
        
        count = counter_manager.get_daily_count('2026-01-15')
        
        assert count == 0
        mock_dynamodb_table.get_item.assert_called_once_with(Key={'date': '2026-01-15'})
    
    def test_get_daily_count_uses_today_by_default(self, counter_manager, mock_dynamodb_table):
        """Test that get_daily_count uses today's date when not specified."""
        mock_dynamodb_table.get_item.return_value = {'Item': {'date': '2026-01-15', 'count': 2}}
        
        with patch.object(counter_manager, '_get_today_date', return_value='2026-01-15'):
            count = counter_manager.get_daily_count()
        
        assert count == 2
        mock_dynamodb_table.get_item.assert_called_once_with(Key={'date': '2026-01-15'})
    
    def test_increment_daily_count_success(self, counter_manager, mock_dynamodb_table):
        """Test successful counter increment."""
        mock_dynamodb_table.update_item.return_value = {
            'Attributes': {'count': 3}
        }
        
        new_count = counter_manager.increment_daily_count('2026-01-15')
        
        assert new_count == 3
        assert mock_dynamodb_table.update_item.called
    
    def test_increment_daily_count_limit_exceeded(self, counter_manager, mock_dynamodb_table):
        """Test that incrementing beyond limit raises exception."""
        # Simulate conditional check failure (limit reached)
        error_response = {'Error': {'Code': 'ConditionalCheckFailedException'}}
        mock_dynamodb_table.update_item.side_effect = ClientError(error_response, 'UpdateItem')
        mock_dynamodb_table.get_item.return_value = {'Item': {'date': '2026-01-15', 'count': 5}}
        
        with pytest.raises(DailyLimitExceeded) as exc_info:
            counter_manager.increment_daily_count('2026-01-15')
        
        assert 'Daily limit of 5 posts has been reached' in str(exc_info.value)
    
    def test_increment_daily_count_uses_today_by_default(self, counter_manager, mock_dynamodb_table):
        """Test that increment_daily_count uses today's date when not specified."""
        mock_dynamodb_table.update_item.return_value = {'Attributes': {'count': 1}}
        
        with patch.object(counter_manager, '_get_today_date', return_value='2026-01-15'):
            new_count = counter_manager.increment_daily_count()
        
        assert new_count == 1
    
    def test_can_send_more_posts_true(self, counter_manager, mock_dynamodb_table):
        """Test can_send_more_posts returns True when under limit."""
        mock_dynamodb_table.get_item.return_value = {'Item': {'date': '2026-01-15', 'count': 3}}
        
        result = counter_manager.can_send_more_posts('2026-01-15')
        
        assert result is True
    
    def test_can_send_more_posts_false(self, counter_manager, mock_dynamodb_table):
        """Test can_send_more_posts returns False when at limit."""
        mock_dynamodb_table.get_item.return_value = {'Item': {'date': '2026-01-15', 'count': 5}}
        
        result = counter_manager.can_send_more_posts('2026-01-15')
        
        assert result is False
    
    def test_can_send_more_posts_no_record(self, counter_manager, mock_dynamodb_table):
        """Test can_send_more_posts returns True when no record exists."""
        mock_dynamodb_table.get_item.return_value = {}
        
        result = counter_manager.can_send_more_posts('2026-01-15')
        
        assert result is True
    
    def test_get_today_date_format(self, counter_manager):
        """Test that _get_today_date returns correct format."""
        date_str = counter_manager._get_today_date()
        
        # Verify format YYYY-MM-DD
        assert len(date_str) == 10
        assert date_str[4] == '-'
        assert date_str[7] == '-'
        
        # Verify it's a valid date
        datetime.strptime(date_str, '%Y-%m-%d')


class TestConvenienceFunctions:
    """Test suite for convenience functions."""
    
    @patch('src.daily_counter.DailyCounterManager')
    def test_get_daily_count_function(self, mock_manager_class):
        """Test get_daily_count convenience function."""
        mock_manager = Mock()
        mock_manager.get_daily_count.return_value = 3
        mock_manager_class.return_value = mock_manager
        
        count = get_daily_count('test-table', '2026-01-15')
        
        assert count == 3
        mock_manager.get_daily_count.assert_called_once_with('2026-01-15')
    
    @patch('src.daily_counter.DailyCounterManager')
    def test_increment_daily_count_function(self, mock_manager_class):
        """Test increment_daily_count convenience function."""
        mock_manager = Mock()
        mock_manager.increment_daily_count.return_value = 4
        mock_manager_class.return_value = mock_manager
        
        new_count = increment_daily_count('test-table', 5, '2026-01-15')
        
        assert new_count == 4
        mock_manager.increment_daily_count.assert_called_once_with('2026-01-15')
    
    @patch('src.daily_counter.DailyCounterManager')
    def test_can_send_more_posts_function(self, mock_manager_class):
        """Test can_send_more_posts convenience function."""
        mock_manager = Mock()
        mock_manager.can_send_more_posts.return_value = True
        mock_manager_class.return_value = mock_manager
        
        result = can_send_more_posts('test-table', 5, '2026-01-15')
        
        assert result is True
        mock_manager.can_send_more_posts.assert_called_once_with('2026-01-15')
