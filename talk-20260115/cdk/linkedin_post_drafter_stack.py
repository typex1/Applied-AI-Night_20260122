"""
CDK Stack for AWS LinkedIn Post Drafter
"""
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    BundlingOptions,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class LinkedInPostDrafterStack(Stack):
    """
    CDK Stack that defines all infrastructure for the LinkedIn Post Drafter application.
    
    This stack creates:
    - Lambda function for post drafting logic
    - DynamoDB table for daily counter tracking
    - SNS topic for email delivery
    - EventBridge Scheduler for daily execution
    - IAM roles and permissions
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Sub-task 12.2: Create DynamoDB table with CDK
        # Define table with date as partition key
        # Enable TTL on ttl attribute
        # Use on-demand billing
        counter_table = dynamodb.Table(
            self,
            "CounterTable",
            partition_key=dynamodb.Attribute(
                name="date",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # On-demand billing
            time_to_live_attribute="ttl",  # Enable TTL on ttl attribute
            removal_policy=RemovalPolicy.DESTROY,  # For development; use RETAIN in production
        )

        # Sub-task 12.3: Create SNS topic with CDK
        # Define SNS topic for email delivery
        post_drafts_topic = sns.Topic(
            self,
            "PostDraftsTopic",
            display_name="LinkedIn Post Drafts",
            topic_name="linkedin-post-drafts",
        )

        # Configure email subscriptions
        # Note: Email addresses should be provided via CDK context or parameters
        # Example: cdk deploy --context email=user@example.com
        email_address = self.node.try_get_context("email")
        if email_address:
            post_drafts_topic.add_subscription(
                subscriptions.EmailSubscription(email_address)
            )

        # Sub-task 12.1: Create CDK stack for Lambda function
        # Define Lambda function with Python 3.11 runtime
        # Set memory to 512MB and timeout to 5 minutes
        # Configure environment variables
        post_drafter_function = lambda_.Function(
            self,
            "PostDrafterFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,  # Python 3.11 runtime
            handler="lambda_handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda-deployment-fixed.zip"),  # Fixed deployment package
            memory_size=512,  # 512MB memory
            timeout=Duration.minutes(5),  # 5-minute timeout
            environment={
                "RSS_FEED_URL": "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
                "KEYWORDS": self.node.try_get_context("keywords") or "Lambda,S3,DynamoDB,AI,Machine Learning,Bedrock,SageMaker",
                "SNS_TOPIC_ARN": post_drafts_topic.topic_arn,
                "DAILY_LIMIT": "5",
                "DYNAMODB_TABLE_NAME": counter_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Sub-task 12.5: Configure IAM roles and permissions
        # Grant Lambda permissions for DynamoDB, SNS, CloudWatch Logs
        # Use least-privilege principle
        
        # Grant DynamoDB read/write permissions
        counter_table.grant_read_write_data(post_drafter_function)
        
        # Grant SNS publish permissions
        post_drafts_topic.grant_publish(post_drafter_function)
        
        # CloudWatch Logs permissions are automatically granted by CDK

        # Sub-task 12.4: Create EventBridge Scheduler with CDK
        # Define daily schedule (e.g., 9 AM UTC)
        # Configure Lambda as target
        daily_schedule = events.Rule(
            self,
            "DailySchedule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="9",  # 9 AM UTC
                month="*",
                week_day="*",
                year="*"
            ),
            description="Trigger LinkedIn Post Drafter daily at 9 AM UTC",
        )

        # Add Lambda function as target
        daily_schedule.add_target(
            targets.LambdaFunction(post_drafter_function)
        )

        # Grant EventBridge permission to invoke Lambda
        # This is automatically handled by add_target(), but we can be explicit
        post_drafter_function.grant_invoke(
            iam.ServicePrincipal("events.amazonaws.com")
        )
