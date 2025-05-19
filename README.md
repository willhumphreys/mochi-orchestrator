# Mochi Orchestrator

This project contains the infrastructure code for the Mochi data processing platform.

## Stack Organization

The project is organized into two types of stacks:

### Stateful Stacks
Located in `mochi_orchestrator/stateful/`

These stacks contain resources that maintain persistent data. **DO NOT DELETE** these stacks without careful consideration and data migration planning.

Current stateful stacks:
- `MochiStorageStack`: Contains S3 buckets for input data and analysis results

### Stateless Stacks
Located in `mochi_orchestrator/stateless/`

These stacks contain compute and processing resources with no persistent data. These stacks can be safely destroyed and recreated as needed.

Current stateless stacks:
- `MochiComputeStack`: Contains Lambda functions, API Gateway, and AWS Batch resources
- `PortfolioTrackerStack`: Contains ECS Fargate task scheduled to run a Docker image daily

## Deployment Commands


# Deploy all stacks
```bash
cdk deploy --all
````

# Deploy only stateful resources
```bash
cdk deploy MochiStorageStack
````

# Deploy only stateless resources
```bash
cdk deploy MochiComputeStack
````

# Deploy only Portfolio Tracker stack
```bash
cdk deploy PortfolioTrackerStack
````

# Destroy stateless resources (SAFE)
```bash
cdk destroy MochiComputeStack
````

# Destroy Portfolio Tracker stack (SAFE)
```bash
cdk destroy PortfolioTrackerStack
````

# Destroy stateful resources (CAUTION!)
# Consider backing up data first
```bash
cdk destroy MochiStorageStack
```
