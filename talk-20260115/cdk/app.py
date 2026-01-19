#!/usr/bin/env python3
"""
AWS CDK App for LinkedIn Post Drafter
"""
import aws_cdk as cdk
from linkedin_post_drafter_stack import LinkedInPostDrafterStack

app = cdk.App()

LinkedInPostDrafterStack(
    app,
    "LinkedInPostDrafterStack",
    description="AWS LinkedIn Post Drafter - Automated news aggregation and post drafting",
)

app.synth()
