from aws_cdk import (
    Stack,
    aws_ecr as ecr,
    aws_iam as iam,
    Duration,
    CfnOutput
)
from constructs import Construct


class EcrStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        repositories = [
            {"name": "MochiJavaEcrRepository", "repo_name": "mochi-java"},
            {"name": "TradingAssistantEcrRepository", "repo_name": "trading-assistant"},
        ]

        self.repositories = {}
        for repo in repositories:
            lifecycle_rule = ecr.LifecycleRule(
                description="Keep only last 5 images",
                max_image_count=5,
                rule_priority=1
            )

            self.repositories[repo["name"]] = ecr.Repository(
                self,
                repo["name"],
                repository_name=repo["repo_name"],
                image_scan_on_push=True,
                lifecycle_rules=[lifecycle_rule]
            )


class GitHubOIDCProviderStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        github_domain = "token.actions.githubusercontent.com"

        # Create the GitHub OIDC provider
        self.gh_provider = iam.OpenIdConnectProvider(
            self,
            "githubProvider",
            url=f"https://{github_domain}",
            client_ids=["sts.amazonaws.com"]
        )

        # Export the provider ARN so it can be imported in other stacks
        CfnOutput(
            self,
            "GithubProviderArn",
            value=self.gh_provider.open_id_connect_provider_arn,
            export_name="GitHubOIDCProviderArn"
        )


class GitHubStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            gh_provider_arn: str,
            deploy_role_name: str = "gitHubDeployRole",
            repository_configs=None,
            **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        if repository_configs is None:
            repository_configs = []

        github_domain = "token.actions.githubusercontent.com"

        # Map repository configurations to IAM conditions
        iam_repo_deploy_access = [
            f"repo:{config['owner']}/{config['repo']}:{config.get('filter', '*')}"
            for config in repository_configs
        ]

        # Set up conditions for the OIDC provider
        conditions = {
            "StringLike": {
                f"{github_domain}:sub": iam_repo_deploy_access
            }
        }

        # Create the deployment role using the provided provider ARN
        iam.Role(
            self,
            "cloudNationGitHubDeployRole",
            assumed_by=iam.WebIdentityPrincipal(
                gh_provider_arn,
                conditions=conditions
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ],
            role_name=deploy_role_name,
            description="This role is used via GitHub Actions to deploy with AWS CDK or Terraform on the target AWS account",
            max_session_duration=Duration.hours(1)
        )
