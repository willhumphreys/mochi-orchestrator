import aws_cdk as cdk
from mochi_orchestrator import MochiOrchestratorStack

app = cdk.App()
MochiOrchestratorStack(app, "MochiOrchestratorStack")
app.synth()
