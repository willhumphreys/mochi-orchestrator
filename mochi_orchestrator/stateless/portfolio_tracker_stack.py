import os

from aws_cdk import (
    Stack,
    Duration,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    CfnOutput
)
from constructs import Construct


class PortfolioTrackerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC for the ECS tasks
        vpc = ec2.Vpc(
            self, "PortfolioTrackerVpc",
            max_azs=2,
            nat_gateways=0,  # Use NAT gateway to allow outbound internet access
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                )
            ]
        )

        # Create an ECS cluster
        cluster = ecs.Cluster(
            self, "PortfolioTrackerCluster",
            vpc=vpc
        )

        # Create a Fargate task definition
        task_definition = ecs.FargateTaskDefinition(
            self, "PortfolioTrackerTaskDef",
            memory_limit_mib=512,
            cpu=256
        )

        # Add S3 permissions to the task for the specific bucket
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=[
                    "arn:aws:s3:::mochi-prod-portfolio-tracking",
                    "arn:aws:s3:::mochi-prod-portfolio-tracking/*"
                ],
                effect=iam.Effect.ALLOW
            )
        )

        # Add container to the task definition
        container = task_definition.add_container(
            "PortfolioTrackerContainer",
            image=ecs.ContainerImage.from_registry("registry.gitlab.com/whumphreys/portfolio-tracker/main:latest"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="portfolio-tracker"),
            environment={
                "S3_BUCKET_NAME": "mochi-prod-portfolio-tracking"
            },
            command=[
                "--cik", "1067983",
                "--which", "latest",
                "--email", "test@test.com",
                "--name", "test"
            ]
        )

        # Create a scheduled Fargate task
        scheduled_task = targets.EcsTask(
            cluster=cluster,
            task_definition=task_definition,
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            )
        )

        # Create EventBridge rule to schedule the task
        rule = events.Rule(
            self, "PortfolioTrackerScheduleRule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="0",  # Run at midnight UTC
                day="*",
                month="*",
                year="*"
            )
        )

        # Add the ECS task as a target for the rule
        rule.add_target(scheduled_task)

        # Output the task ARN
        CfnOutput(
            self, "TaskDefinitionArn",
            value=task_definition.task_definition_arn,
            description="ARN of the ECS Task Definition"
        )

        # Output the schedule rule ARN
        CfnOutput(
            self, "ScheduleRuleArn",
            value=rule.rule_arn,
            description="ARN of the EventBridge Rule for scheduling"
        )
