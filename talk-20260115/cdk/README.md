# AWS LinkedIn Post Drafter - CDK Infrastructure

This directory contains the AWS CDK infrastructure code for the LinkedIn Post Drafter application.

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS CDK CLI installed (`npm install -g aws-cdk`)
3. Python 3.11+ installed

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Bootstrap CDK (first time only):
   ```bash
   cdk bootstrap
   ```

## Deployment

### Basic Deployment

```bash
cdk deploy
```

### Deployment with Email Subscription

To automatically subscribe an email address to the SNS topic:

```bash
cdk deploy --context email=your-email@example.com
```

### Deployment with Custom Keywords

To customize the keywords used for filtering:

```bash
cdk deploy --context keywords="Lambda,S3,DynamoDB,AI,Bedrock" --context email=your-email@example.com
```

## Infrastructure Components

The stack creates the following AWS resources:

### Lambda Function
- **Runtime**: Python 3.11
- **Memory**: 512MB
- **Timeout**: 5 minutes
- **Handler**: `lambda_handler.lambda_handler`
- **Source**: `../src` directory

### DynamoDB Table
- **Name**: `LinkedInPostDrafterStack-CounterTable-*`
- **Partition Key**: `date` (String)
- **Billing**: On-demand
- **TTL**: Enabled on `ttl` attribute
- **Purpose**: Track daily post count

### SNS Topic
- **Name**: `linkedin-post-drafts`
- **Purpose**: Send email notifications with post drafts
- **Subscriptions**: Email (if provided via context)

### EventBridge Rule
- **Schedule**: Daily at 9:00 AM UTC
- **Target**: Lambda function
- **Purpose**: Trigger daily execution

### IAM Permissions
- Lambda execution role with permissions for:
  - DynamoDB read/write on counter table
  - SNS publish to post drafts topic
  - CloudWatch Logs write access
- EventBridge permission to invoke Lambda

## Environment Variables

The Lambda function is configured with these environment variables:

- `RSS_FEED_URL`: AWS "What's New" RSS feed URL
- `KEYWORDS`: Comma-separated list of keywords for filtering
- `SNS_TOPIC_ARN`: ARN of the SNS topic (auto-generated)
- `DAILY_LIMIT`: Maximum posts per day (5)
- `DYNAMODB_TABLE_NAME`: Name of the counter table (auto-generated)
- `LOG_LEVEL`: Logging level (INFO)

## Customization

### Changing the Schedule

Edit the `daily_schedule` in `linkedin_post_drafter_stack.py`:

```python
daily_schedule = events.Rule(
    self,
    "DailySchedule",
    schedule=events.Schedule.cron(
        minute="0",
        hour="14",  # 2 PM UTC
        month="*",
        week_day="*",
        year="*"
    ),
)
```

### Adding Multiple Email Subscriptions

Modify the SNS topic configuration to add multiple email addresses:

```python
emails = ["user1@example.com", "user2@example.com"]
for email in emails:
    post_drafts_topic.add_subscription(
        subscriptions.EmailSubscription(email)
    )
```

## Monitoring

The stack includes:
- CloudWatch Logs with 1-week retention
- Automatic CloudWatch metrics for Lambda
- DynamoDB metrics

## Cleanup

To destroy all resources:

```bash
cdk destroy
```

## Useful CDK Commands

- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation template
- `cdk diff` - Compare deployed stack with current state
- `cdk docs` - Open CDK documentation