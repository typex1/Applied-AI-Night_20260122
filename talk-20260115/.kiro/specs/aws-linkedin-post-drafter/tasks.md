# Implementation Plan: AWS LinkedIn Post Drafter

## Overview

This implementation plan breaks down the AWS LinkedIn Post Drafter into discrete coding tasks. The system will be built as a Python Lambda function with supporting infrastructure. Tasks are ordered to enable incremental validation, with core functionality implemented first, followed by testing and integration.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create Python project structure with src/ and tests/ directories
  - Create requirements.txt with dependencies: feedparser, boto3, hypothesis (for testing)
  - Set up logging configuration
  - Create data models (FeedItem, PostDraft, AppConfig) as dataclasses
  - _Requirements: 7.1_

- [x] 2. Implement configuration management
  - [x] 2.1 Create configuration loader that reads from environment variables
    - Load RSS_FEED_URL, KEYWORDS, SNS_TOPIC_ARN, DAILY_LIMIT, DYNAMODB_TABLE_NAME
    - Parse comma-separated KEYWORDS into list
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ]* 2.2 Write property test for configuration parsing
    - **Property 13: Configuration Parsing**
    - **Validates: Requirements 7.2**
  
  - [x] 2.3 Implement configuration validation
    - Validate required fields are present and non-empty
    - Validate SNS_TOPIC_ARN format
    - Raise clear errors for invalid configuration
    - _Requirements: 7.6_
  
  - [ ]* 2.4 Write property test for configuration validation
    - **Property 14: Configuration Validation**
    - **Validates: Requirements 7.6**

- [x] 3. Implement RSS feed fetcher
  - [x] 3.1 Create RSS feed fetcher with retry logic
    - Use feedparser library to fetch and parse RSS feed
    - Implement exponential backoff retry (3 attempts)
    - Parse feed items into FeedItem objects
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 3.2 Write unit test for successful RSS feed fetch
    - Test with mock RSS feed data
    - _Requirements: 1.1_
  
  - [ ]* 3.3 Write property test for RSS parsing completeness
    - **Property 1: RSS Feed Parsing Completeness**
    - **Validates: Requirements 1.3**
  
  - [ ]* 3.4 Write property test for error recovery
    - **Property 2: RSS Feed Error Recovery**
    - **Validates: Requirements 1.2**
  
  - [x] 3.5 Implement graceful handling of malformed items
    - Log errors for invalid items
    - Continue processing valid items
    - _Requirements: 1.4_
  
  - [ ]* 3.6 Write property test for malformed item handling
    - **Property 3: Malformed Item Graceful Handling**
    - **Validates: Requirements 1.4**

- [x] 4. Implement content filter
  - [x] 4.1 Create keyword-based content filter
    - Implement case-insensitive keyword matching
    - Search both title and description fields
    - Return items that match at least one keyword
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 4.2 Write property test for filtering correctness
    - **Property 4: Keyword Filtering Correctness**
    - **Validates: Requirements 2.2, 2.3, 2.4**
  
  - [ ]* 4.3 Write unit tests for edge cases
    - Test with empty keyword list
    - Test with empty feed list
    - Test with no matches
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 5. Checkpoint - Ensure feed fetching and filtering work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement post drafter
  - [x] 6.1 Create LinkedIn post draft generator
    - Format feed item into LinkedIn-friendly post
    - Include title, summary, and link
    - Enforce 3000 character limit
    - Extract and include hashtags
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 6.2 Write property test for content completeness
    - **Property 5: Post Draft Content Completeness**
    - **Validates: Requirements 3.1**
  
  - [ ]* 6.3 Write property test for character limit compliance
    - **Property 6: LinkedIn Character Limit Compliance**
    - **Validates: Requirements 3.2**
  
  - [ ]* 6.4 Write property test for hashtag extraction
    - **Property 7: Hashtag Extraction**
    - **Validates: Requirements 3.3**
  
  - [x] 6.5 Implement deduplication logic
    - Check GUID against previously processed items
    - Skip duplicates
    - _Requirements: 3.4_
  
  - [ ]* 6.6 Write property test for deduplication
    - **Property 8: Draft Deduplication**
    - **Validates: Requirements 3.4**

- [x] 7. Implement daily counter manager
  - [x] 7.1 Create DynamoDB counter operations
    - Implement get_daily_count() using DynamoDB query
    - Implement increment_daily_count() with atomic counter
    - Implement can_send_more_posts() check
    - Use conditional updates to prevent race conditions
    - _Requirements: 4.1, 4.2_
  
  - [ ]* 7.2 Write property test for counter accuracy
    - **Property 9: Daily Counter Accuracy**
    - **Validates: Requirements 4.1**
  
  - [ ]* 7.3 Write unit test for daily limit enforcement
    - Test that 6th post is rejected when limit is 5
    - _Requirements: 4.2_
  
  - [ ]* 7.4 Write unit test for counter reset on new day
    - Test that counter starts at 0 for new date
    - _Requirements: 6.2_

- [x] 8. Implement SNS email sender
  - [x] 8.1 Create SNS publisher with retry logic
    - Format post draft as SNS message
    - Include subject line with news title
    - Include complete draft content and metadata
    - Implement retry with exponential backoff (3 attempts)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 8.2 Write property test for SNS message structure
    - **Property 11: SNS Message Structure Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.3**
  
  - [ ]* 8.3 Write property test for retry behavior
    - **Property 12: SNS Publish Retry Behavior**
    - **Validates: Requirements 5.4**
  
  - [ ]* 8.4 Write unit test for final failure case
    - Test that critical error is logged after all retries fail
    - _Requirements: 5.5_

- [x] 9. Checkpoint - Ensure core components work independently
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement logging infrastructure
  - [x] 10.1 Set up structured logging
    - Configure Python logging with appropriate formatters
    - Include timestamps and component names in all logs
    - Support configurable log levels via environment variable
    - _Requirements: 8.1, 8.4_
  
  - [ ]* 10.2 Write property test for error logging
    - **Property 15: Error Logging with Context**
    - **Validates: Requirements 8.1, 8.4**
  
  - [ ]* 10.3 Write property test for log level appropriateness
    - **Property 16: Log Level Appropriateness**
    - **Validates: Requirements 8.2, 8.3**

- [x] 11. Implement main orchestrator (Lambda handler)
  - [x] 11.1 Create Lambda handler function
    - Load configuration
    - Check daily limit
    - Fetch and filter RSS feed
    - Draft and send posts (up to remaining limit)
    - Handle errors gracefully
    - Return execution summary
    - _Requirements: 6.1, 6.2, 6.4_
  
  - [ ]* 11.2 Write integration test for complete flow
    - Test end-to-end execution with mocked AWS services
    - _Requirements: 6.1, 6.2, 6.4_
  
  - [ ]* 11.3 Write unit test for execution error handling
    - Test that execution failures are logged and reported
    - _Requirements: 6.4_

- [x] 12. Create AWS CDK infrastructure code
  - [x] 12.1 Create CDK stack for Lambda function
    - Define Lambda function with Python 3.11 runtime
    - Set memory to 512MB and timeout to 5 minutes
    - Configure environment variables
    - _Requirements: 7.1_
  
  - [x] 12.2 Create DynamoDB table with CDK
    - Define table with date as partition key
    - Enable TTL on ttl attribute
    - Use on-demand billing
    - _Requirements: 4.1_
  
  - [x] 12.3 Create SNS topic with CDK
    - Define SNS topic for email delivery
    - Configure email subscriptions
    - _Requirements: 5.1_
  
  - [x] 12.4 Create EventBridge Scheduler with CDK
    - Define daily schedule (e.g., 9 AM UTC)
    - Configure Lambda as target
    - _Requirements: 6.1_
  
  - [x] 12.5 Configure IAM roles and permissions
    - Grant Lambda permissions for DynamoDB, SNS, CloudWatch Logs
    - Grant EventBridge permission to invoke Lambda
    - Use least-privilege principle
    - _Requirements: 5.1, 4.1_

- [x] 13. Final checkpoint - End-to-end validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end flows with AWS services
- CDK infrastructure tasks can be done in parallel with application code
