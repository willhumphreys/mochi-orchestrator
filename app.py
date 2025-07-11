#!/usr/bin/env python3
import os

from aws_cdk import App, Tags, Fn

from mochi_orchestrator.ecr_and_git_hub_deployment_stacks import EcrStack, GitHubOIDCProviderStack, GitHubStack
from mochi_orchestrator.stateful.storage_stack import MochiStorageStack
from mochi_orchestrator.stateless.compute_stack import MochiComputeStack
from mochi_orchestrator.stateless.dashboard_stack import MochiDashboardStack
from mochi_orchestrator.stateless.dashboard_zome_stack import DashboardSubdomainZoneStack
from mochi_orchestrator.stateless.kubernetes_access_stack import KubernetesAccessStack
from mochi_orchestrator.stateless.portfolio_tracker_stack import PortfolioTrackerStack

app = App()

# Create storage stack first
storage_stack = MochiStorageStack(app, "MochiStorageStack")

dashboard_stack = MochiDashboardStack(app, "MochiDashboardStack")

# Create compute stack and pass only the bucket names
compute_stack = MochiComputeStack(app, "MochiComputeStack", user_pool=dashboard_stack.user_pool,
    raw_bucket_name="mochi-prod-raw-historical-data", prepared_bucket_name="mochi-prod-prepared-historical-data",
    trades_bucket_name="mochi-prod-backtest-trades", traders_bucket_name="mochi-prod-backtest-traders",
    aggregation_bucket_name="mochi-prod-aggregated-trades",
    staging_aggregation_bucket_name="mochi-prod-athena-query-staging", mochi_graphs_bucket="mochi-prod-summary-graphs",
    mochi_prod_trade_extracts="mochi-prod-trade-extracts",
    mochi_prod_trade_performance_graphs="mochi-prod-trade_performance_graphs",
    mochi_prod_final_trader_ranking="mochi-prod-final-trader-ranking", mochi_prod_ticker_meta="mochi-prod-ticker-meta",
    mochi_prod_live_trades="mochi-prod-live-trades", mochi_prod_backtest_params="mochi-prod-backtest-params")

kubernetes_access_stack = KubernetesAccessStack(app, "MochiKubernetesAccessStack", bucket_name="mochi-prod-live-trades")

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

mochi_java_repos = [{"owner": "willhumphreys", "repo": "mochi-java", "filter": f"ref:refs/heads/master"},
    {"owner": "willhumphreys", "repo": "mochi-java", "filter": "pull_request"}, ]

trading_assistant_repos = [
    {"owner": "willhumphreys", "repo": "trading-assistant", "filter": f"ref:refs/heads/{github_branch}"},
    {"owner": "willhumphreys", "repo": "trading-assistant", "filter": "pull_request"}, ]

# Create GitHub stacks
mochi_java_github_stack = GitHubStack(app, "MochiJavaGitHubStack", gh_provider_arn=github_provider_arn,
    repository_configs=mochi_java_repos, deploy_role_name="MochiJavaGitHubDeployRole"  # Give each role a unique name
)
mochi_java_github_stack.add_dependency(oidc_provider_stack)  # Ensure the provider exists first

trading_assistant_github_stack = GitHubStack(app, "TradingAssistantGitHubStack", gh_provider_arn=github_provider_arn,
    repository_configs=trading_assistant_repos, deploy_role_name="TradingAssistantGitHubDeployRole"
    # Give each role a unique name
)
trading_assistant_github_stack.add_dependency(oidc_provider_stack)  # Ensure the provider exists first

dashboard_stack = DashboardSubdomainZoneStack(app, "DashboardSubdomainZoneStack")

# Create Portfolio Tracker stack
portfolio_tracker_stack = PortfolioTrackerStack(app, "PortfolioTrackerStack")

# Add common tags to all resources
Tags.of(app).add("Project", "Mochi")

app.synth()
