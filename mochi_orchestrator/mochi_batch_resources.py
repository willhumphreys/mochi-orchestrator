# mochi_orchestrator/mochi_batch_resources.py
from aws_cdk import (
    Stack,
    Tags,
    aws_batch as batch,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
from typing import Optional


class MochiBatchResources(Construct):
    """
    A CDK construct that creates AWS Batch resources including a compute environment and job queue.

    This construct creates:
    - Custom VPC with public subnets (no NAT Gateway)
    - Fargate Spot compute environment
    - Batch job queue
    """

    def __init__(self, scope: Construct, id: str, *,
                 max_vcpus: int = 4,
                 compute_env_name: str = "MochiFargate",
                 job_queue_name: str = "fargateSpotTrades",
                 tags: Optional[dict] = None,
                 **kwargs) -> None:
        """
        Initialize Batch resources.

        :param scope: The parent construct
        :param id: The construct ID
        :param max_vcpus: Maximum vCPUs for the compute environment
        :param compute_env_name: Name of the compute environment
        :param job_queue_name: Name of the job queue
        :param tags: Optional tags to apply to all resources
        """
        super().__init__(scope, id)

        # Create a custom VPC with only public subnets (no NAT Gateway)
        vpc = ec2.Vpc(self, "MochiVPC",
                      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
                      max_azs=2,  # Use 2 AZs for better availability
                      subnet_configuration=[
                          ec2.SubnetConfiguration(
                              name="Public",
                              subnet_type=ec2.SubnetType.PUBLIC,
                              cidr_mask=24
                          )
                      ],
                      # No NAT Gateways needed
                      nat_gateways=0
                      )

        # Create service role for Batch
        batch_service_role = iam.Role.from_role_arn(
            self, "BatchServiceRole",
            f"arn:aws:iam::{Stack.of(self).account}:role/aws-service-role/batch.amazonaws.com/AWSServiceRoleForBatch"
        )

        # Create a security group for the Batch compute environment
        security_group = ec2.SecurityGroup(self, "BatchSecurityGroup",
                                           vpc=vpc,
                                           description="Security group for AWS Batch compute environment",
                                           allow_all_outbound=True
                                           )

        # Create Batch Compute Environment - using lower level CfnComputeEnvironment
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
                    compute_environment=self.batch_compute_env.attr_compute_environment_arn
                )
            ]
        )

        # Output the VPC ID and other useful information
        CfnOutput(self, "VpcId", value=vpc.vpc_id)
        CfnOutput(self, "SubnetIds", value=",".join(vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids))
        CfnOutput(self, "SecurityGroupId", value=security_group.security_group_id)

        # Apply tags if provided
        if tags:
            for key, value in tags.items():
                Tags.of(self).add(key, value)

    @property
    def compute_environment_arn(self) -> str:
        """Get the ARN of the Batch compute environment."""
        return self.batch_compute_env.attr_compute_environment_arn

    @property
    def job_queue_arn(self) -> str:
        """Get the ARN of the Batch job queue."""
        return self.batch_job_queue.attr_job_queue_arn
