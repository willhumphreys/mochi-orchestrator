from aws_cdk import (
    Stack,
    CfnOutput, SecretValue,
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

        # Create Amplify app for the dashboard with a public repository
        dashboard_app = App(
            self, "MochiDashboard",
            app_name="mochi-dashboard",
            source_code_provider=GitHubSourceCodeProvider(
                owner="willhumphreys",
                repository="mochi-dashboard",
                oauth_token=SecretValue.secrets_manager("mochi-dashboard-github-token")

            ),
            # Customize build specification if needed
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

        # Outputs
        CfnOutput(
            self, "AmplifyAppId",
            value=dashboard_app.app_id,
            description="Amplify App ID for the Mochi Dashboard"
        )

        CfnOutput(
            self, "DashboardURL",
            value=main_branch.branch_name,  # Use branch_url instead of branch_name
            description="URL of the deployed Mochi Dashboard"
        )
