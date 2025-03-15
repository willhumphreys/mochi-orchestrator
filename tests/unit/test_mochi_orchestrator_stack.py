import aws_cdk as core
import aws_cdk.assertions as assertions

from mochi_orchestrator.mochi_orchestrator_stack import MochiOrchestratorStack

# example tests. To run these tests, uncomment this file along with the example
# resource in mochi_orchestrator/mochi_orchestrator_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MochiOrchestratorStack(app, "mochi-orchestrator")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
