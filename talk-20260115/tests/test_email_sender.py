"""Tests for SNS email sender."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError

from src.email_sender import send_via_sns, SNSPublishError, _format_subject, _format_message
from src.models import PostDraft


@pytest.fixture
def sample_draft():
    """Create a sample PostDraft for testing."""
    return PostDraft(
        content="🚀 AWS News Update!\n\n📢 New Lambda Feature\n\nAWS Lambda now supports...\n\n🔗 Read more: https://aws.amazon.com/news\n\n#AWS #Lambda",
        hashtags=["#AWS", "#Lambda", "#Serverless"],
        source_link="https://aws.amazon.com/news/lambda-feature",
        source_title="AWS Lambda Introduces New Feature for Serverless Applications",
        created_at=datetime(2026, 1, 15, 10, 30, 0),
        guid="aws-lambda-feature-2026-01-15"
    )


class TestSendViaSNS:
    """Tests for send_via_sns function."""
    
    @patch('src.email_sender.boto3.client')
    def test_successful_publish(self, mock_boto_client, sample_draft):
        """Test successful SNS publish on first attempt."""
        # Setup mock
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-123'}
        mock_boto_client.return_value = mock_sns
        
        # Execute
        result = send_via_sns(sample_draft, 'arn:aws:sns:us-east-1:123456789012:test-topic')
        
        # Verify
        assert result is True
        mock_sns.publish.assert_called_once()
        
        # Check the call arguments
        call_args = mock_sns.publish.call_args
        assert call_args[1]['TopicArn'] == 'arn:aws:sns:us-east-1:123456789012:test-topic'
        assert 'LinkedIn Post Draft:' in call_args[1]['Subject']
        assert 'AWS Lambda' in call_args[1]['Subject']
        assert sample_draft.content in call_args[1]['Message']
        assert sample_draft.source_link in call_args[1]['Message']
    
    @patch('src.email_sender.boto3.client')
    @patch('src.email_sender.time.sleep')
    def test_retry_on_transient_error(self, mock_sleep, mock_boto_client, sample_draft):
        """Test retry logic with transient errors."""
        # Setup mock to fail twice then succeed
        mock_sns = Mock()
        mock_sns.publish.side_effect = [
            ClientError({'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}}, 'publish'),
            ClientError({'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}}, 'publish'),
            {'MessageId': 'test-message-id-456'}
        ]
        mock_boto_client.return_value = mock_sns
        
        # Execute
        result = send_via_sns(sample_draft, 'arn:aws:sns:us-east-1:123456789012:test-topic')
        
        # Verify
        assert result is True
        assert mock_sns.publish.call_count == 3
        assert mock_sleep.call_count == 2  # Should sleep between retries
        
        # Verify exponential backoff
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == 1.0  # First retry: base_delay * 2^0
        assert sleep_calls[1] == 2.0  # Second retry: base_delay * 2^1
    
    @patch('src.email_sender.boto3.client')
    @patch('src.email_sender.time.sleep')
    def test_all_retries_fail(self, mock_sleep, mock_boto_client, sample_draft):
        """Test that SNSPublishError is raised after all retries fail."""
        # Setup mock to always fail
        mock_sns = Mock()
        error = ClientError(
            {'Error': {'Code': 'InvalidParameter', 'Message': 'Invalid topic ARN'}},
            'publish'
        )
        mock_sns.publish.side_effect = error
        mock_boto_client.return_value = mock_sns
        
        # Execute and verify exception
        with pytest.raises(SNSPublishError) as exc_info:
            send_via_sns(sample_draft, 'arn:aws:sns:us-east-1:123456789012:test-topic')
        
        assert 'Failed to publish to SNS after 3 attempts' in str(exc_info.value)
        assert mock_sns.publish.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between attempts, not after last
    
    @patch('src.email_sender.boto3.client')
    def test_custom_retry_parameters(self, mock_boto_client, sample_draft):
        """Test with custom max_attempts and base_delay."""
        # Setup mock to always fail
        mock_sns = Mock()
        mock_sns.publish.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'publish'
        )
        mock_boto_client.return_value = mock_sns
        
        # Execute with custom parameters
        with pytest.raises(SNSPublishError):
            send_via_sns(
                sample_draft,
                'arn:aws:sns:us-east-1:123456789012:test-topic',
                max_attempts=2,
                base_delay=0.5
            )
        
        # Verify custom max_attempts was respected
        assert mock_sns.publish.call_count == 2


class TestFormatSubject:
    """Tests for _format_subject function."""
    
    def test_normal_title(self, sample_draft):
        """Test subject formatting with normal title."""
        subject = _format_subject(sample_draft)
        
        assert subject.startswith('LinkedIn Post Draft: ')
        assert 'AWS Lambda' in subject
    
    def test_long_title_truncation(self):
        """Test that very long titles are truncated."""
        long_title = "A" * 100  # Very long title
        draft = PostDraft(
            content="Test content",
            hashtags=["#AWS"],
            source_link="https://example.com",
            source_title=long_title,
            created_at=datetime.now(),
            guid="test-guid"
        )
        
        subject = _format_subject(draft)
        
        # Subject should be truncated
        assert len(subject) < len(long_title) + 25  # "LinkedIn Post Draft: " is 22 chars
        assert subject.endswith('...')


class TestFormatMessage:
    """Tests for _format_message function."""
    
    def test_message_contains_all_required_fields(self, sample_draft):
        """Test that formatted message contains all required fields."""
        message = _format_message(sample_draft)
        
        # Check for all required sections
        assert 'LINKEDIN POST DRAFT' in message
        assert 'DRAFT CONTENT:' in message
        assert 'METADATA' in message
        
        # Check for draft content
        assert sample_draft.content in message
        
        # Check for metadata fields
        assert sample_draft.source_title in message
        assert sample_draft.source_link in message
        assert sample_draft.guid in message
        
        # Check for hashtags
        for hashtag in sample_draft.hashtags:
            assert hashtag in message
        
        # Check for instructions
        assert 'To publish this post:' in message
    
    def test_message_formatting_structure(self, sample_draft):
        """Test that message has proper structure with separators."""
        message = _format_message(sample_draft)
        
        # Check for section separators
        assert '=' * 70 in message
        assert '-' * 70 in message
        
        # Check for proper line breaks
        assert '\n\n' in message
    
    def test_timestamp_formatting(self, sample_draft):
        """Test that timestamp is properly formatted."""
        message = _format_message(sample_draft)
        
        # Check timestamp format
        assert '2026-01-15 10:30:00 UTC' in message


class TestIntegration:
    """Integration tests for email sender."""
    
    @patch('src.email_sender.boto3.client')
    def test_complete_flow_with_all_metadata(self, mock_boto_client):
        """Test complete flow with all metadata included."""
        # Create a comprehensive draft
        draft = PostDraft(
            content="🚀 AWS News Update!\n\n📢 Amazon S3 Express One Zone\n\nNew storage class...\n\n🔗 Read more: https://aws.amazon.com/s3\n\n#AWS #S3 #Storage",
            hashtags=["#AWS", "#S3", "#Storage", "#Cloud"],
            source_link="https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-s3-express-one-zone/",
            source_title="Amazon S3 Express One Zone - High Performance Storage",
            created_at=datetime(2026, 1, 15, 14, 45, 30),
            guid="s3-express-one-zone-announcement"
        )
        
        # Setup mock
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'integration-test-id'}
        mock_boto_client.return_value = mock_sns
        
        # Execute
        result = send_via_sns(draft, 'arn:aws:sns:us-east-1:123456789012:linkedin-drafts')
        
        # Verify
        assert result is True
        
        # Verify the published message contains all metadata
        call_args = mock_sns.publish.call_args[1]
        message = call_args['Message']
        
        assert draft.content in message
        assert draft.source_link in message
        assert draft.source_title in message
        assert draft.guid in message
        assert all(tag in message for tag in draft.hashtags)
        assert '2026-01-15 14:45:30 UTC' in message

