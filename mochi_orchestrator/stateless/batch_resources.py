# mochi_orchestrator/mochi_batch_resources.py
from aws_cdk import (
    Stack,
    Tags,
    aws_batch as batch,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput,
    Fn
)
from constructs import Construct
from typing import Optional


class MochiBatchResources(Construct):
    """
    A CDK construct that creates AWS Batch resources including a compute environment,
    job queue, and job definitions.
    """

    def __init__(self, scope: Construct, id: str, *,
                 max_vcpus: int = 4,
                 compute_env_name: str = "MochiFargate",
                 job_queue_name: str = "fargateSpotTrades",
                 tags: Optional[dict] = None,
                 **kwargs) -> None:
        """
        Initialize Batch resources.
        """
        super().__init__(scope, id)

        # Create a custom VPC with only public subnets (no NAT Gateway)
        vpc = ec2.Vpc(self, "MochiVPC",
                      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
                      max_azs=2,
                      subnet_configuration=[
                          ec2.SubnetConfiguration(
                              name="Public",
                              subnet_type=ec2.SubnetType.PUBLIC,
                              cidr_mask=24
                          )
                      ],
                      nat_gateways=0
                      )

        # Create service role for Batch
        batch_service_role = iam.Role.from_role_arn(
            self, "BatchServiceRole",
            f"arn:aws:iam::{Stack.of(self).account}:role/aws-service-role/batch.amazonaws.com/AWSServiceRoleForBatch"
        )

        # Create security group for the Batch compute environment
        security_group = ec2.SecurityGroup(self, "BatchSecurityGroup",
                                           vpc=vpc,
                                           description="Security group for AWS Batch compute environment",
                                           allow_all_outbound=True
                                           )

        # Create Batch Compute Environment
        self.batch_compute_env = batch.CfnComputeEnvironment(
            self, "BatchComputeEnv",
            compute_environment_name=compute_env_name,
            type="MANAGED",
            state="ENABLED",
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type="FARGATE_SPOT",
                maxv_cpus=max_vcpus,
                subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids,
                security_group_ids=[security_group.security_group_id]
            ),
            service_role=batch_service_role.role_arn
        )

        # Create Batch Job Queue
        self.batch_job_queue = batch.CfnJobQueue(
            self, "BatchJobQueue",
            job_queue_name=job_queue_name,
            priority=1,
            state="ENABLED",
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=self.batch_compute_env.ref
                )
            ]
        )

        # Define job definitions
        job_definitions_config = [
            {
                "name": "polygon-extract",
                "image": "ghcr.io/willhumphreys/polygon:latest",
                "vcpu": 1.0,
                "memory": 2048,
                "timeout_seconds": 3600,
            },
            {
                "name": "trade-data-enhancer",
                "image": "ghcr.io/willhumphreys/trade-data-enhancer:latest",
                "vcpu": 2.0,
                "memory": 16384,
                "timeout_seconds": 3600,
            },
            {
                "name": "mochi-graphs",
                "image": "ghcr.io/willhumphreys/r-graphs:latest",
                "vcpu": 2.0,
                "memory": 16384,
                "timeout_seconds": 3600,
            },
            {
                "name": "mochi-trades",
                "image": "739275456034.dkr.ecr.eu-central-1.amazonaws.com/mochi-java:latest",
                "vcpu": 4.0,
                "memory": 30720,
                "timeout_seconds": 14400,
            },
            {
                "name": "py-trade-lens",
                "image": "ghcr.io/willhumphreys/py-trade-lens:latest",
                "vcpu": 4.0,
                "memory": 30720,
                "timeout_seconds": 14400,
            },
            {
                "name": "r-graphs",
                "image": "ghcr.io/willhumphreys/r-graphs:latest",
                "vcpu": 2.0,
                "memory": 16384,
                "timeout_seconds": 14400,
            },
            {
                "name": "trade-extract",
                "image": "ghcr.io/willhumphreys/trade-extract:latest",
                "vcpu": 1.0,
                "memory": 2048,
                "timeout_seconds": 600,
            },
            {
                "name": "trade-summary",
                "image": "ghcr.io/willhumphreys/trade-summary:latest",
                "vcpu": 1.0,
                "memory": 2048,
                "timeout_seconds": 600,
            },
            {
                "name": "data-metadata",
                "image": "ghcr.io/willhumphreys/data-metadata:latest",
                "vcpu": 1.0,
                "memory": 2048,
                "timeout_seconds": 3600,
            }
        ]

        # Create task execution role
        execution_role = iam.Role(
            self, "BatchTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Create job role with permissions to access S3
        job_role = iam.Role(
            self, "BatchJobRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAthenaFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSBatchFullAccess")
            ]


        )

        # Create all job definitions using the configurations
        self.job_definitions = {}
        for i, job_def in enumerate(job_definitions_config):
            job_definition = batch.CfnJobDefinition(
                self, f"JobDef{i}",
                job_definition_name=job_def["name"],
                type="container",
                platform_capabilities=["FARGATE"],
                container_properties={
                    "image": job_def["image"],
                    "command": [],
                    "jobRoleArn": job_role.role_arn,
                    "executionRoleArn": execution_role.role_arn,
                    "resourceRequirements": [
                        {
                            "type": "VCPU",
                            "value": str(job_def["vcpu"])
                        },
                        {
                            "type": "MEMORY",
                            "value": str(job_def["memory"])
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {}
                    },
                    "networkConfiguration": {
                        "assignPublicIp": "ENABLED"
                    },
                    "fargatePlatformConfiguration": {
                        "platformVersion": "LATEST"
                    },
                    "runtimePlatform": {
                        "operatingSystemFamily": "LINUX",
                        "cpuArchitecture": "X86_64"
                    }
                },
                # --- Updated Retry Strategy ---
                retry_strategy=batch.CfnJobDefinition.RetryStrategyProperty(
                    attempts=3,  # Set maximum potential retries (e.g., 3 attempts = 1 initial + 2 retries)
                    evaluate_on_exit=[
                        # Rule 1: Retry specifically on Spot Interruption
                        batch.CfnJobDefinition.EvaluateOnExitProperty(
                            action="RETRY",
                            # This reason is typically used for Fargate Spot interruptions
                            on_reason="SpotInterruption"
                        ),

                    ]
                ),
                # --- End of Updated Retry Strategy ---
                timeout={
                    "attemptDurationSeconds": job_def["timeout_seconds"]
                }
            )
            self.job_definitions[job_def["name"]] = job_definition


            CfnOutput(
                self, f"JobDefinitionArn{i}",
                value=job_definition.ref,
                description=f"ARN of the {job_def['name']} job definition"
            )

        # Output the VPC ID and other useful information
        CfnOutput(self, "VpcId", value=vpc.vpc_id)
        CfnOutput(self, "SubnetIds", value=Fn.join(",", vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids))
        CfnOutput(self, "SecurityGroupId", value=security_group.security_group_id)
        CfnOutput(self, "JobQueueArn", value=self.batch_job_queue.ref)
        CfnOutput(self, "ComputeEnvironmentArn", value=self.batch_compute_env.ref)

        # Apply tags if provided
        if tags:
            for key, value in tags.items():
                Tags.of(self).add(key, value)

    @property
    def compute_environment_arn(self) -> str:
        """Get the ARN of the Batch compute environment."""
        return self.batch_compute_env.ref

    @property
    def job_queue_arn(self) -> str:
        """Get the ARN of the Batch job queue."""
        return self.batch_job_queue.ref
