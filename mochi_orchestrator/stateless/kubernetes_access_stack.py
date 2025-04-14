
from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_iam as iam
from constructs import Construct


class KubernetesAccessStack(Stack):
    """
    Stack to create an IAM user with read access to a specific S3 bucket.
    Access keys can be created manually after deployment.
    """

    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an IAM policy that allows reading from the specified bucket
        bucket_access_policy = iam.ManagedPolicy(
            self,
            "BucketAccessPolicy",
            managed_policy_name=f"S3Access-{bucket_name}",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    resources=[
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                )
            ]
        )

        # Create a dedicated IAM user for S3 access
        s3_access_user = iam.User(
            self,
            "S3AccessUser",
            user_name=f"s3-{bucket_name}-reader"
        )

        # Attach the policy to the user
        s3_access_user.add_managed_policy(bucket_access_policy)

        # Output information
        CfnOutput(
            self,
            "BucketName",
            value=bucket_name,
            description="S3 bucket that can be accessed",
            export_name=f"{construct_id}-BucketName"
        )

        CfnOutput(
            self,
            "UserName",
            value=s3_access_user.user_name,
            description="IAM User for S3 bucket access",
            export_name=f"{construct_id}-UserName"
        )

        CfnOutput(
            self,
            "Instructions",
            value="Create access keys manually using AWS Console or CLI: aws iam create-access-key --user-name " + s3_access_user.user_name,
            description="Instructions for creating access keys"
        )
