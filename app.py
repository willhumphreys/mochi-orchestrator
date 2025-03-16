#!/usr/bin/env python3
import os

from aws_cdk import App, Tags, Fn

from mochi_orchestrator.ecr_and_git_hub_deployment_stacks import EcrStack, GitHubOIDCProviderStack, GitHubStack
# Updated imports using the new structure
from mochi_orchestrator.stateful.storage_stack import MochiStorageStack
from mochi_orchestrator.stateless.compute_stack import MochiComputeStack

app = App()

# Create storage stack first
storage_stack = MochiStorageStack(app, "MochiStorageStack")

# Create compute stack and pass only the bucket names
compute_stack = MochiComputeStack(
    app,
    "MochiComputeStack",
    input_bucket_name="mochi-prod-raw-historical-data",  # Hardcoded value
    output_bucket_name="mochi-prod-prepared-historical-data"  # Hardcoded value
)


# Create ECR stack
ecr_stack = EcrStack(app, "EcrStack")

# Create the OIDC provider stack first
oidc_provider_stack = GitHubOIDCProviderStack(app, "GitHubOIDCProviderStack")

# Get the provider ARN from the OIDC provider stack
github_provider_arn = Fn.import_value("GitHubOIDCProviderArn")

# Or if using an existing provider, you could directly use its ARN:
# github_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"

# Define repository configurations
github_branch = os.environ.get('GITHUB_BRANCH', 'main')

mochi_java_repos = [
    {"owner": "willhumphreys", "repo": "mochi-java", "filter": f"ref:refs/heads/master"},
    {"owner": "willhumphreys", "repo": "mochi-java", "filter": "pull_request"},
]

trading_assistant_repos = [
    {"owner": "willhumphreys", "repo": "trading-assistant", "filter": f"ref:refs/heads/{github_branch}"},
    {"owner": "willhumphreys", "repo": "trading-assistant", "filter": "pull_request"},
]

# Create GitHub stacks
mochi_java_github_stack = GitHubStack(
    app,
    "MochiJavaGitHubStack",
    gh_provider_arn=github_provider_arn,
    repository_configs=mochi_java_repos,
    deploy_role_name="MochiJavaGitHubDeployRole"  # Give each role a unique name
)
mochi_java_github_stack.add_dependency(oidc_provider_stack)  # Ensure the provider exists first

trading_assistant_github_stack = GitHubStack(
    app,
    "TradingAssistantGitHubStack",
    gh_provider_arn=github_provider_arn,
    repository_configs=trading_assistant_repos,
    deploy_role_name="TradingAssistantGitHubDeployRole"  # Give each role a unique name
)
trading_assistant_github_stack.add_dependency(oidc_provider_stack)  # Ensure the provider exists first


# Add common tags to all resources
Tags.of(app).add("Project", "Mochi")

app.synth()
