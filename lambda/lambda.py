import json
import os
import boto3


def handler(event, context):
    """
    Lambda function that submits a Batch job with the ticker argument.
    """
    try:
        # Log the received event
        print('Received event:', json.dumps(event))

        # Extract ticker from the event
        ticker = extract_ticker_from_event(event)

        # Initialize Batch client
        batch_client = boto3.client('batch')

        # Submit job to AWS Batch
        # Submit job to AWS Batch
        response = batch_client.submit_job(
            jobName='polygon-job',
            jobQueue='fargateSpotTrades',
            jobDefinition='polygon-extract',
            parameters={
                'ticker': ticker  # This is used for parameter substitution in the job definition
            },
            containerOverrides={
                'command': ["python", "src/main.py", "--tickers", ticker],
                'environment': [
                    {
                        "name": "POLYGON_API_KEY",
                        "value": os.environ.get('POLYGON_API_KEY')
                    },
                    {
                        'name': 'OUTPUT_BUCKET_NAME',
                        'value': os.environ.get('RAW_BUCKET_NAME')
                    }
                ]
            }
        )

        # Store the job ID from the first job
        first_job_id = response['jobId']

        # Submit dependent job that processes the data further
        enhancer_response = batch_client.submit_job(
            jobName='enhance-data-job',
            jobQueue='fargateSpotTrades',
            jobDefinition='trade-data-enhancer',
            parameters={
                'ticker': ticker  # Pass the same ticker to the enhancer job
            },
            containerOverrides={
                'command': ["python", "src/enhancer.py", "--ticker", ticker, "--provider", "polygon"],
                'environment': [
                    {
                        'name': 'INPUT_BUCKET_NAME',
                        'value': os.environ.get('RAW_BUCKET_NAME')
                    },
                    {
                        'name': 'OUTPUT_BUCKET_NAME',
                        'value': os.environ.get('PREPARED_BUCKET_NAME')
                    }
                ]
            },
            # Make this job dependent on the first job
            dependsOn=[
                {
                    'jobId': first_job_id
                }
            ]
        )

        # Include the enhancer job ID in the response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Enable CORS
            },
            'body': json.dumps({
                'message': f'Submitted batch jobs for ticker: {ticker}',
                'ticker': ticker,
                'polygonJobId': response['jobId'],
                'enhancerJobId': enhancer_response['jobId'],
                'input': event
            })
        }


    except Exception as e:
            # Log the error
            print(f'Error in Lambda execution: {str(e)}')

            # Return error response
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'  # Enable CORS
                },
                'body': json.dumps({
                    'message': 'Failed to process request',
                    'error': str(e)
                })
            }


def extract_ticker_from_event(event):
    """Helper function to extract ticker from different event formats."""
    # Check for ticker in JSON body (for API Gateway proxy integration)
    if 'body' in event and event['body'] is not None:
        # The body might be a string that needs parsing
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']
        ticker = body.get('ticker')
        if ticker:
            return ticker

    # If not found in body, check queryStringParameters
    if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
        ticker = event['queryStringParameters'].get('ticker')
        if ticker:
            return ticker

    # If not found in query parameters, check direct event
    ticker = event.get('ticker')
    if ticker:
        return ticker

    # If ticker not found anywhere, raise exception
    raise ValueError("No ticker provided in the request")
