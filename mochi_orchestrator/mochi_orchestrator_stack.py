from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigateway,
    CfnOutput
)
from constructs import Construct
from .mochi_batch_resources import MochiBatchResources


class MochiOrchestratorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        lambda_function = _lambda.Function(
            self, "OrchestratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.minutes(1),
        )

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
