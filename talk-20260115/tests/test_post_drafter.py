"""Tests for the post drafter module."""

import pytest
from datetime import datetime

from src.models import FeedItem, PostDraft
from src.post_drafter import draft_linkedin_post, _extract_hashtags, _format_post_content, _clean_html


class TestDraftLinkedInPost:
    """Tests for the draft_linkedin_post function."""
    
    def test_draft_basic_post(self):
        """Test drafting a basic LinkedIn post from a feed item."""
        item = FeedItem(
            title="AWS Lambda Announces New Feature",
            description="AWS Lambda now supports Python 3.12 runtime with improved performance.",
            link="https://aws.amazon.com/about-aws/whats-new/2026/01/lambda-python-312",
            pub_date=datetime(2026, 1, 15, 10, 0, 0),
            guid="lambda-python-312"
        )
        
        draft = draft_linkedin_post(item)
        
        assert isinstance(draft, PostDraft)
        assert draft.guid == "lambda-python-312"
        assert draft.source_link == item.link
        assert draft.source_title == item.title
        assert len(draft.content) <= 3000
        assert len(draft.hashtags) > 0
        assert "#AWS" in draft.hashtags
        assert item.title in draft.content
        assert item.link in draft.content
    
    def test_draft_with_long_description(self):
        """Test that long descriptions are truncated to fit character limit."""
        long_description = "A" * 3500  # Exceeds LinkedIn limit
        
        item = FeedItem(
            title="Test Title",
            description=long_description,
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test-long"
        )
        
        draft = draft_linkedin_post(item)
        
        assert len(draft.content) <= 3000
        assert "..." in draft.content  # Should be truncated
    
    def test_deduplication_prevents_duplicate_drafts(self):
        """Test that deduplication logic prevents processing the same item twice."""
        item = FeedItem(
            title="Test Title",
            description="Test description",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test-guid-123"
        )
        
        processed_guids = {"test-guid-123"}
        
        with pytest.raises(ValueError, match="already been processed"):
            draft_linkedin_post(item, processed_guids)
    
    def test_draft_without_deduplication_check(self):
        """Test drafting without providing processed_guids set."""
        item = FeedItem(
            title="Test Title",
            description="Test description",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test-guid-456"
        )
        
        # Should work fine without processed_guids
        draft = draft_linkedin_post(item, None)
        assert draft.guid == "test-guid-456"


class TestExtractHashtags:
    """Tests for hashtag extraction."""
    
    def test_extract_aws_service_hashtags(self):
        """Test extraction of AWS service names as hashtags."""
        item = FeedItem(
            title="AWS Lambda and DynamoDB Integration",
            description="New integration between Lambda and DynamoDB",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test"
        )
        
        hashtags = _extract_hashtags(item)
        
        assert "#AWS" in hashtags
        assert "#Lambda" in hashtags
        assert "#DynamoDB" in hashtags
    
    def test_always_includes_aws_hashtag(self):
        """Test that #AWS is always included."""
        item = FeedItem(
            title="Generic Title",
            description="Generic description",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test"
        )
        
        hashtags = _extract_hashtags(item)
        
        assert "#AWS" in hashtags
        assert len(hashtags) >= 1
    
    def test_extract_technology_keywords(self):
        """Test extraction of technology keywords as hashtags."""
        item = FeedItem(
            title="Serverless AI with Machine Learning",
            description="Build serverless applications with AI and ML",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test"
        )
        
        hashtags = _extract_hashtags(item)
        
        assert "#AWS" in hashtags
        assert any(tag in ["#Serverless", "#AI", "#MachineLearning", "#ML"] for tag in hashtags)
    
    def test_hashtag_limit(self):
        """Test that hashtags are limited to a reasonable number."""
        # Create item with many potential hashtags
        item = FeedItem(
            title="Lambda S3 DynamoDB RDS EC2 ECS EKS Fargate CloudFormation",
            description="API Gateway Step Functions EventBridge Kinesis Redshift",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test"
        )
        
        hashtags = _extract_hashtags(item)
        
        # Should be limited to 7 hashtags
        assert len(hashtags) <= 7


class TestFormatPostContent:
    """Tests for post content formatting."""
    
    def test_format_includes_all_components(self):
        """Test that formatted content includes all required components."""
        item = FeedItem(
            title="Test Title",
            description="Test description",
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test"
        )
        
        hashtags = ["#AWS", "#Lambda"]
        content = _format_post_content(item, hashtags)
        
        assert "Test Title" in content
        assert "Test description" in content
        assert "https://example.com" in content
        assert "#AWS" in content
        assert "#Lambda" in content
    
    def test_format_respects_character_limit(self):
        """Test that formatted content respects the 3000 character limit."""
        long_description = "A" * 5000
        
        item = FeedItem(
            title="Test Title",
            description=long_description,
            link="https://example.com",
            pub_date=datetime.now(),
            guid="test"
        )
        
        hashtags = ["#AWS"]
        content = _format_post_content(item, hashtags)
        
        assert len(content) <= 3000


class TestCleanHtml:
    """Tests for HTML cleaning."""
    
    def test_remove_html_tags(self):
        """Test removal of HTML tags."""
        text = "<p>This is <strong>bold</strong> text</p>"
        cleaned = _clean_html(text)
        
        assert "<p>" not in cleaned
        assert "<strong>" not in cleaned
        assert "This is bold text" == cleaned
    
    def test_decode_html_entities(self):
        """Test decoding of HTML entities."""
        text = "AWS &amp; Cloud &lt;Services&gt;"
        cleaned = _clean_html(text)
        
        assert "&amp;" not in cleaned
        assert "&lt;" not in cleaned
        assert "&gt;" not in cleaned
        assert "AWS & Cloud <Services>" == cleaned
    
    def test_clean_whitespace(self):
        """Test cleaning of excessive whitespace."""
        text = "Text   with    multiple     spaces"
        cleaned = _clean_html(text)
        
        assert "Text with multiple spaces" == cleaned
