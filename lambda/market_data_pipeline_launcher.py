import json
import os
import random
import datetime
import re

import boto3

from do_all_s3_keys_exist import do_all_s3_keys_exist
from generate_s3_path_utils import generate_s3_path


def handler(event, context):
    """
    Lambda function handler that processes market data and submits a chain of batch jobs.
    All jobs use a common group_tag for better tracking and organization.
    """
    print("Received event:", json.dumps(event))

    # Initialize boto3 client
    batch_client = boto3.client('batch')

    # Easy-to-remember random words for group tagging
    easy_words = ["apple", "banana", "cherry", "dragonfruit", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon",
                  "mango", "nectarine", "orange", "papaya", "quince", "raspberry", "strawberry", "tangerine", "ugli",
                  "vanilla", "watermelon", "xigua", "yam", "zucchini"]

    # Generate a random group tag for all jobs in this execution
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    group_tag = f"{random.choice(easy_words)}-{timestamp}"
    print(f"Using group tag: {group_tag} for all jobs in this execution")

    # Extract ticker from event
    ticker, from_date, to_date, short_atr_period, long_atr_period, alpha = extract_arguments_from_event(event)
    print(f"Processing ticker: {ticker} {from_date} {to_date} {short_atr_period} {long_atr_period} {alpha}")

    s3_key_min = generate_s3_path(ticker, "stocks", "polygon", timeframe="min")
    s3_key_hour = generate_s3_path(ticker, "stocks", "polygon", timeframe="hour")
    s3_key_day = generate_s3_path(ticker, "stocks", "polygon", timeframe="day")

    # Common job queue
    queue_name = "fargateSpotTrades"
    print(f"Using queue: {queue_name}")

    # Step 1: Submit the polygon job (first in the chain)
    polygon_job_name = sanitize_job_name(f"polygon-job-{ticker}-{group_tag}")
    print(f"Submitting polygon job: {polygon_job_name}")

    keys_to_check = [s3_key_min, s3_key_hour, s3_key_day]

    raw_data_bucket = os.environ.get('RAW_BUCKET_NAME')

    if not do_all_s3_keys_exist(raw_data_bucket, keys_to_check):
        polygon_response = batch_client.submit_job(jobName=polygon_job_name, jobQueue=queue_name,
                                                   jobDefinition='polygon-extract',
                                                   parameters={'ticker': ticker, 'from_date': from_date,
                                                               'to_date': to_date}, containerOverrides={
                'command': ["python", "src/main.py", "--tickers", ticker, "--s3_key_min", s3_key_min, "--s3_key_hour",
                            s3_key_hour, "--s3_key_day", s3_key_day, "--from_date", from_date, "--to_date", to_date],
                'environment': [{"name": "POLYGON_API_KEY", "value": os.environ.get('POLYGON_API_KEY')},
                                {'name': 'OUTPUT_BUCKET_NAME', 'value': os.environ.get('RAW_BUCKET_NAME')}]},
                                                   tags={"Ticker": ticker, "SubmissionGroupTag": group_tag,
                                                         "TaskType": "polygon-extract"})

        polygon_job_id = polygon_response['jobId']
        print(f"Submitted polygon job with ID: {polygon_job_id}")
    else:
        print(f"All data files for {ticker} already exist. Skipping Polygon job.")

    dependencies = []
    if 'polygon_job_id' in locals():
        # Only add the polygon job as a dependency if it was actually submitted
        dependencies.append({'jobId': polygon_job_id})
    else:
        polygon_job_id = "skipped"



    # Step 2: Submit the trade-data-enhancer job (dependent on polygon job)
    enhance_job_name = sanitize_job_name(f"trade-data-enhancer-{ticker}-{group_tag}")
    print(f"Submitting trade-data-enhancer job: {enhance_job_name}")

    enhance_response = batch_client.submit_job(jobName=enhance_job_name, jobQueue=queue_name,
                                               jobDefinition="trade-data-enhancer", dependsOn=dependencies,
                                               containerOverrides={
                                                   'command': ["python", "src/enhancer.py", "--ticker", ticker,
                                                               "--provider", "polygon", "--s3_key_min", s3_key_min,
                                                               "--s3_key_hour", s3_key_hour, "--s3_key_day", s3_key_day,
                                                               "--short_atr_period", str(short_atr_period),
                                                               "--long_atr_period", str(long_atr_period),
                                                               "--alpha", str(alpha)
                                                               ], 'environment': [
                                                       {'name': 'INPUT_BUCKET_NAME',
                                                        'value': os.environ.get('RAW_BUCKET_NAME')},
                                                       {'name': 'OUTPUT_BUCKET_NAME',
                                                        'value': os.environ.get('PREPARED_BUCKET_NAME')},
                                                       {'name': 'AWS_REGION', 'value': 'eu-central-1'}, ]},
                                               tags={"Ticker": ticker, "SubmissionGroupTag": group_tag,
                                                     "TaskType": "trade-data-enhancer"})

    enhance_job_id = enhance_response['jobId']
    print(f"Submitted trade-data-enhancer job with ID: {enhance_job_id}")


    # Step 1: Submit the polygon job (first in the chain)
    metadata_job_name = sanitize_job_name(f"metadata-job-{ticker}-{group_tag}")

    print(f"Submitting job with name: {metadata_job_name}")

    # Submit the trades job (dependent on trade-data-enhancer-job)
    metadata_response = batch_client.submit_job(jobName=metadata_job_name, jobQueue=queue_name,
                                                jobDefinition="data-metadata", dependsOn=[{'jobId': polygon_job_id}, {'jobId': enhance_job_id}],
                                                containerOverrides={
                                                    "command": ["--s3-key-min", s3_key_min, "--ticker", ticker, "--group-tag", group_tag
                                                                ],
                                                    'environment': [
                                                                    {'name': 'AWS_REGION', 'value': 'eu-central-1'},
                                                                    {'name': 'S3_BUCKET',
                                                                     'value': os.environ.get('RAW_BUCKET_NAME')},
                                                                    {'name': 'S3_UPLOAD_BUCKET',
                                                                     'value': os.environ.get('MOCHI_PROD_TICKER_META')},
                                                                    {'name': 'MOCHI_DATA_BUCKET',
                                                                     'value': os.environ.get('PREPARED_BUCKET_NAME')},
                                                                    {'name': 'MOCHI_TRADES_BUCKET',
                                                                     'value': os.environ.get('TRADES_BUCKET_NAME')},
                                                                    {'name': 'MOCHI_TRADERS_BUCKET',
                                                                     'value': os.environ.get('TRADER_BUCKET_NAME')},
                                                                    {'name': 'S3_TICKER-META_BUCKET',
                                                                     'value': os.environ.get('MOCHI_PROD_TICKER_META')},
                                                                    {'name': 'MOCHI_AGGREGATION_BUCKET', 'value': os.environ.get('MOCHI_AGGREGATION_BUCKET')},
                                                                    {'name': 'MOCHI_AGGREGATION_BUCKET_STAGING',
                                                                        'value': os.environ.get('MOCHI_AGGREGATION_BUCKET_STAGING')},

                                                                    {'name': 'MOCHI_GRAPHS_BUCKET', 'value': os.environ.get('MOCHI_GRAPHS_BUCKET')},
                                                                    {'name': 'MOCHI_PROD_TRADE_EXTRACTS', 'value': os.environ.get('MOCHI_PROD_TRADE_EXTRACTS')}



                                                                    ]},



                                                tags={"Symbol": ticker, "SubmissionGroupTag": group_tag,
                                                      "TaskType": "meta"})



    return {'statusCode': 200, 'body': json.dumps(
        {'message': f'Successfully submitted job chain for {ticker}', 'polygonJobId': polygon_job_id,
         'enhanceJobId': enhance_job_id, 'groupTag': group_tag})}



def extract_arguments_from_event(event):
    """Extract ticker symbol and date range from the event body."""
    try:
        # Check if body is present
        if 'body' not in event:
            raise ValueError("No body in event")

        # Parse body as JSON
        body = event['body']
        if isinstance(body, str):
            import json
            body = json.loads(body)

        # Extract ticker from parsed body
        if 'ticker' in body:
            ticker = body['ticker']
        else:
            raise ValueError("No ticker field found in request body")

        if 'from_date' in body:
            from_date = body['from_date']
        else:
            raise ValueError("No from_date field found in request body")

        if 'to_date' in body:
            to_date = body['to_date']
        else:
            raise ValueError("No to_date field found in request body")

        if 'shortATRPeriod' in body:
            short_atr_period = body['shortATRPeriod']
        else:
            raise ValueError("No shortATRPeriod field found in request body")

        if 'longATRPeriod' in body:
            long_atr_period = body['longATRPeriod']
        else:
            raise ValueError("No longATRPeriod field found in request body")

        if 'alpha' in body:
            alpha = body['alpha']
        else:
            raise ValueError("No alpha field found in request body")

        return ticker, from_date, to_date, short_atr_period, long_atr_period, alpha
    except Exception as e:
        print(f"Error extracting arguments from event body: {str(e)}")
        raise ValueError("Could not extract arguments from event body")

def sanitize_job_name(name):
    """
    Sanitize job name by replacing invalid characters with valid ones.
    AWS Batch job names can only contain letters, numbers, hyphens (-) and underscores (_).
    """
    # Replace colons with underscores or another valid character
    return re.sub(r'[^a-zA-Z0-9\-_]', '_', name)