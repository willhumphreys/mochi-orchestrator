from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    RemovalPolicy,
)
from constructs import Construct


class MochiOrchestratorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Create Lambda function
        lambda_function = _lambda.Function(
            self, "SimpleFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.minutes(5),
        )
