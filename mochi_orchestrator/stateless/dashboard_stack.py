import os

from aws_cdk import (
    Stack,
    CfnOutput,
    SecretValue,
    aws_cognito as cognito,
    RemovalPolicy,
    aws_iam as iam,
)
from aws_cdk.aws_amplify_alpha import (
    App,
    GitHubSourceCodeProvider,
)
from aws_cdk.aws_codebuild import BuildSpec
from constructs import Construct


class MochiDashboardStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "MochiDashboardUserPool",
            user_pool_name="mochi-dashboard-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=False
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            removal_policy=RemovalPolicy.DESTROY  # For dev/test. Use RETAIN for production
        )

        # Add a domain to the user pool for hosted UI
        domain = self.user_pool.add_domain(
            "MochiDashboardDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="mochi-dashboard"
                # This creates a domain like mochi-dashboard.auth.region.amazoncognito.com
            )
        )

        # Create a Cognito User Pool Client
        client = self.user_pool.add_client(
            "MochiDashboardClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=[
                    "https://master.d37eokvg7j9het.amplifyapp.com",  # Your Amplify app URL
                    "https://master.d37eokvg7j9het.amplifyapp.com/",  # With trailing slash
                    "https://dashboard.minoko.life",  # Custom domain
                    "https://dashboard.minoko.life/",  # Custom domain with trailing slash
                    "http://localhost:5173"  # For Vite local development (default port)
                ],
                logout_urls=[
                    "https://master.d37eokvg7j9het.amplifyapp.com",  # Your Amplify app URL
                    "https://master.d37eokvg7j9het.amplifyapp.com/",  # With trailing slash
                    "https://dashboard.minoko.life",  # Custom domain
                    "https://dashboard.minoko.life/",  # Custom domain with trailing slash
                    "http://localhost:5173"  # For Vite local development (default port)
                ]
            )
        )

        # Create a role for Amplify app that can read from S3
        amplify_service_role = iam.Role(
            self, "AmplifyServiceRole",
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),
            description="Role for Amplify app to access S3"
        )

        # Add S3 read permissions to the role
        # If you have a specific bucket, replace the ARN with your bucket ARN
        amplify_service_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                resources=[
                    # For a specific bucket, use: arn:aws:s3:::your-bucket-name
                    # For all buckets, use: arn:aws:s3:::*
                    "arn:aws:s3:::*",
                    "arn:aws:s3:::*/*"
                ]
            )
        )

        # Create an Identity Pool linked to your Cognito User Pool
        identity_pool = cognito.CfnIdentityPool(
            self, "MochiDashboardIdentityPool",
            identity_pool_name="mochi_dashboard_identity_pool",
            allow_unauthenticated_identities=False,  # Require authentication
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=client.user_pool_client_id,
                    provider_name=f"cognito-idp.{self.region}.amazonaws.com/{self.user_pool.user_pool_id}"
                )
            ]
        )

        # Create Amplify app for the dashboard
        dashboard_app = App(
            self, "MochiDashboard",
            app_name="mochi-dashboard",
            source_code_provider=GitHubSourceCodeProvider(
                owner="willhumphreys",
                repository="mochi-dashboard",
                oauth_token=SecretValue.secrets_manager("mochi-dashboard-github-token")
            ),
            build_spec=BuildSpec.from_object({
                "version": 1,
                "frontend": {
                    "phases": {
                        "preBuild": {
                            "commands": [
                                "npm ci"
                            ]
                        },
                        "build": {
                            "commands": [
                                # Set environment variables for Vite
                                f"export VITE_USER_POOL_ID={self.user_pool.user_pool_id}",
                                f"export VITE_USER_POOL_CLIENT_ID={client.user_pool_client_id}",
                                f"export VITE_REGION={self.region}",
                                f"export VITE_COGNITO_DOMAIN=mochi-dashboard.auth.{self.region}.amazoncognito.com",
                                f"export VITE_COGNITO_IDENTITY_POOL_ID={identity_pool.ref}",
                                f"export VITE_POLYGON_API_KEY={os.environ.get('POLYGON_API_KEY')}",
                                "npm run build"
                            ]
                        }
                    },
                    "artifacts": {
                        "baseDirectory": "dist",
                        "files": ["**/*"]
                    }
                }
            })
        )

        # Add branch for main production deployment
        main_branch = dashboard_app.add_branch("master")

        # Create IAM role for authenticated users
        authenticated_role = iam.Role(
            self, "MochiDashboardAuthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                "sts:AssumeRoleWithWebIdentity"
            )
        )

        # Add S3 read permissions to the authenticated role
        authenticated_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:ListBucketVersions",
                    "s3:GetObjectVersion"
                ],
                resources=[
                    # Replace with your specific bucket ARN
                    "arn:aws:s3:::mochi-prod-final-trader-ranking",
                    "arn:aws:s3:::mochi-prod-final-trader-ranking/*",
                    "arn:aws:s3:::mochi-prod-live-trades",
                    "arn:aws:s3:::mochi-prod-live-trades/*",
                    "arn:aws:s3:::mochi-prod-portfolio-tracking",
                    "arn:aws:s3:::mochi-prod-portfolio-tracking/*"
                ]
            )
        )

        # Attach roles to the Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            self, "MochiDashboardIdentityPoolRoleAttachment",
            identity_pool_id=identity_pool.ref,
            roles={
                "authenticated": authenticated_role.role_arn
            }
        )

        # Pass the Identity Pool ID to your Amplify app environment
        # (Add to your existing environment_variables in the dashboard_app)
        environment_variables = {
            # Existing variables
            "VITE_IDENTITY_POOL_ID": identity_pool.ref,
            # Other variables
        }

        # Export the Identity Pool ID as an output
        CfnOutput(
            self, "IdentityPoolId",
            value=identity_pool.ref,
            description="Cognito Identity Pool ID for AWS service access"
        )


# Outputs
        CfnOutput(
            self, "AmplifyAppId",
            value=dashboard_app.app_id,
            description="Amplify App ID for the Mochi Dashboard"
        )

        CfnOutput(
            self, "DashboardURL",
            value=main_branch.branch_name,
            description="URL of the deployed Mochi Dashboard"
        )

        # Cognito Outputs
        CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "UserPoolClientId",
            value=client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

        CfnOutput(
            self, "CognitoDomain",
            value=domain.domain_name,
            description="Cognito Domain"
        )

        # Output the full hosted UI URLs
        CfnOutput(
            self, "HostedUISignInURL",
            value=f"https://{domain.domain_name}/login?client_id={client.user_pool_client_id}&response_type=code&scope=email+openid+profile&redirect_uri=https://master.d37eokvg7j9het.amplifyapp.com",
            description="URL for Cognito Hosted UI Sign-in (Amplify app)"
        )

        CfnOutput(
            self, "HostedUISignInURLCustomDomain",
            value=f"https://{domain.domain_name}/login?client_id={client.user_pool_client_id}&response_type=code&scope=email+openid+profile&redirect_uri=https://dashboard.minoko.life",
            description="URL for Cognito Hosted UI Sign-in (Custom domain)"
        )
