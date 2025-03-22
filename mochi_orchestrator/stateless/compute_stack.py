import os

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigateway,
    CfnOutput,
    aws_s3 as s3
)
from constructs import Construct
from .batch_resources import MochiBatchResources


class MochiComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 raw_bucket_name: str = None,
                 prepared_bucket_name: str = None,
                 trades_bucket_name: str = None,
                 traders_bucket_name: str = None,
                 aggregation_bucket_name: str = None,
                 staging_aggregation_bucket_name: str = None,
                 mochi_graphs_bucket: str = None,
                 mochi_prod_trade_extracts: str = None,
                 mochi_prod_trade_performance_graphs: str = None,
                 mochi_prod_final_trader_ranking: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        lambda_function = _lambda.Function(
            self, "OrchestratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="market_data_pipeline_launcher.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.minutes(1),
            environment={
                "RAW_BUCKET_NAME": raw_bucket_name or "",
                "PREPARED_BUCKET_NAME": prepared_bucket_name or "",
                "POLYGON_API_KEY": os.environ.get("POLYGON_API_KEY", ""),
                "TRADES_BUCKET_NAME": trades_bucket_name or "",
                "TRADER_BUCKET_NAME": traders_bucket_name or "",
                "MOCHI_AGGREGATION_BUCKET_STAGING" : staging_aggregation_bucket_name or "",
                "MOCHI_AGGREGATION_BUCKET" : aggregation_bucket_name or "",
                "MOCHI_GRAPHS_BUCKET" : mochi_graphs_bucket or "",
                "MOCHI_PROD_TRADE_EXTRACTS" : mochi_prod_trade_extracts or "",
                "MOCHI_PROD_TRADE_PERFORMANCE_GRAPHS" : mochi_prod_trade_performance_graphs or "",
                "MOCHI_PROD_FINAL_TRADER_RANKING" : mochi_prod_final_trader_ranking or "",

            }
        )

        lambda_function.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "batch:SubmitJob",
                "batch:DescribeJobs",
                "batch:TerminateJob",
                "batch:TagResource",
                "batch:UntagResource"

            ],
            resources=["*"]  # You can restrict this to specific Batch resources if needed
        ))


        # Grant bucket permissions without direct stack reference
        if raw_bucket_name:
            raw_bucket = s3.Bucket.from_bucket_name(
                self, "ImportedInputBucket", raw_bucket_name
            )
            raw_bucket.grant_read(lambda_function)

        if prepared_bucket_name:
            prepared_bucket = s3.Bucket.from_bucket_name(
                self, "ImportedOutputBucket", prepared_bucket_name
            )
            prepared_bucket.grant_read_write(lambda_function)



        # Create API Gateway
        api = apigateway.RestApi(
            self, "MochiBacktestApi",
            rest_api_name="Mochi Backtest Service",
            description="API for triggering backtest processes with ticker data",
        )

        # Create resource and method
        backtest_resource = api.root.add_resource("backtest")

        # Use the lambda function directly
        lambda_integration = apigateway.LambdaIntegration(
            lambda_function,
            proxy=True,
        )

        backtest_resource.add_method("POST", lambda_integration)

        # Add Lambda permission for API Gateway
        lambda_function.add_permission(
            id="ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*/*/backtest"
        )

        # Output the API URL
        CfnOutput(
            self, "ApiEndpoint",
            value=f"{api.url}backtest",
            description="URL for triggering the backtest process"
        )

        # Create Batch resources
        batch_resources = MochiBatchResources(
            self,
            "MochiBatchResources",
            max_vcpus=4,
            compute_env_name="MochiFargate",
            job_queue_name="fargateSpotTrades",
            tags={
                "Project": "Mochi",
                "Environment": "QA"
            }
        )

        # Output Batch resource ARNs using property methods for consistency
        CfnOutput(
            self,
            "BatchComputeEnvironmentArn",
            value=batch_resources.compute_environment_arn,
            description="ARN of the AWS Batch Compute Environment"
        )

        CfnOutput(
            self, "BatchJobQueueArn",
            value=batch_resources.job_queue_arn,
            description="ARN of the AWS Batch Job Queue"
        )
