import json
import os
import random

import boto3

from generate_s3_path_utils import generate_s3_path
from do_all_s3_keys_exist import do_all_s3_keys_exist


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
    group_tag = random.choice(easy_words)
    print(f"Using group tag: {group_tag} for all jobs in this execution")

    # Extract ticker from event
    ticker, from_date, to_date = extract_arguments_from_event(event)
    print(f"Processing ticker: {ticker} {from_date} {to_date}")

    s3_key_min = generate_s3_path(ticker, "stocks", "polygon", timeframe="min")
    s3_key_hour = generate_s3_path(ticker, "stocks", "polygon", timeframe="hour")
    s3_key_day = generate_s3_path(ticker, "stocks", "polygon", timeframe="day")

    # Common job queue
    queue_name = "fargateSpotTrades"
    print(f"Using queue: {queue_name}")

    # Step 1: Submit the polygon job (first in the chain)
    polygon_job_name = f"polygon-job-{ticker}-{group_tag}"
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
    enhance_job_name = f"trade-data-enhancer-{ticker}-{group_tag}"
    print(f"Submitting trade-data-enhancer job: {enhance_job_name}")

    enhance_response = batch_client.submit_job(jobName=enhance_job_name, jobQueue=queue_name,
                                               jobDefinition="trade-data-enhancer",
                                               dependsOn=dependencies,
                                               containerOverrides={
                                                   'command': ["python", "src/enhancer.py", "--ticker", ticker,
                                                               "--provider", "polygon", "--s3_key_min", s3_key_min,
                                                               "--s3_key_hour", s3_key_hour, "--s3_key_day",
                                                               s3_key_day], 'environment': [
                                                       {'name': 'INPUT_BUCKET_NAME',
                                                        'value': os.environ.get('RAW_BUCKET_NAME')},
                                                       {'name': 'OUTPUT_BUCKET_NAME',
                                                        'value': os.environ.get('PREPARED_BUCKET_NAME')}]},
                                               tags={"Ticker": ticker, "SubmissionGroupTag": group_tag,
                                                     "TaskType": "trade-data-enhancer"})

    enhance_job_id = enhance_response['jobId']
    print(f"Submitted trade-data-enhancer job with ID: {enhance_job_id}")

    # Step 3: Submit trading jobs (dependent on trade-data-enhancer job)
    # Single hardcoded scenario
    scenario_template = 's_-3000..-100..400___l_100..7500..400___o_-800..800..100___d_14..14..7___out_8..8..4'

    # Format ticker for scenario
    symbol_file = f"{ticker}-1mF.csv"
    base_symbol = ticker

    # Build the full scenario string
    full_scenario = f"{scenario_template}___{symbol_file}"

    # Determine trade type
    trade_type = "long"  # Default to long since our scenario doesn't have "short"

    # Generate job names
    trades_job_name = f"Trades{ticker}-{group_tag}"
    aggregate_job_name = f"Aggregate{ticker}-{group_tag}"
    graphs_job_name = f"Graphs{ticker}-"

    print(f"Submitting job with name: {trades_job_name} with scenario: {full_scenario}")

    # Submit the trades job (dependent on trade-data-enhancer-job)
    trades_response = batch_client.submit_job(jobName=trades_job_name, jobQueue=queue_name,
                                              jobDefinition="mochi-trades", dependsOn=[{'jobId': enhance_job_id}],
                                              containerOverrides={
                                                  "command": ["-scenario", full_scenario, "-output_dir", "results",
                                                              "-write_trades", "-upload_to_s3", "-s3_key_min",
                                                              s3_key_min], 'environment': [{'name': 'MOCHI_DATA_BUCKET',
                                                                                            'value': os.environ.get(
                                                                                                'PREPARED_BUCKET_NAME')},
                                                                                           {
                                                                                               'name': 'MOCHI_TRADES_BUCKET',
                                                                                               'value': os.environ.get(
                                                                                                   'TRADES_BUCKET_NAME')},
                                                                                           {
                                                                                               'name': 'MOCHI_TRADERS_BUCKET',
                                                                                               'value': os.environ.get(
                                                                                                   'TRADER_BUCKET_NAME')}]},
                                              tags={"Scenario": full_scenario, "Symbol": symbol_file,
                                                    "SubmissionGroupTag": group_tag, "TradeType": trade_type,
                                                    "TaskType": "trade"})

    trades_job_id = trades_response['jobId']
    print(f"Submitted trades job with ID: {trades_job_id}")

    # Submit aggregation job
    print(f"Submitting aggregation job with name: {aggregate_job_name} with scenario: {full_scenario}")
    agg_response = batch_client.submit_job(jobName=aggregate_job_name, dependsOn=[{'jobId': trades_job_id}],
                                           jobQueue=queue_name, jobDefinition="mochi-trades", containerOverrides={
            "command": ["-scenario", full_scenario, "-output_dir", "results", "-upload_to_s3", "-aggregate",
                        "-s3_key_min", s3_key_min],
            'environment': [{'name': 'MOCHI_DATA_BUCKET', 'value': os.environ.get('PREPARED_BUCKET_NAME')},
                            {'name': 'MOCHI_TRADES_BUCKET', 'value': os.environ.get('TRADES_BUCKET_NAME')},
                            {'name': 'MOCHI_TRADERS_BUCKET', 'value': os.environ.get('TRADER_BUCKET_NAME')},
                            {'name': 'MOCHI_AGGREGATION_BUCKET', 'value': os.environ.get('MOCHI_AGGREGATION_BUCKET')},
                            {'name': 'MOCHI_AGGREGATION_BUCKET_STAGING',
                             'value': os.environ.get('MOCHI_AGGREGATION_BUCKET_STAGING')}

                            ]}, tags={"Scenario": full_scenario, "Symbol": symbol_file, "SubmissionGroupTag": group_tag,
                                      "TradeType": trade_type, "TaskType": "aggregation"})

    agg_job_id = agg_response['jobId']
    print(f"Submitted aggregation job with ID: {agg_job_id}")

    # Submit graph jobs
    best_traders_job_id = None

    for script in ["years.r", "stops.r", "bestTraders.r"]:
        job_name = f"{graphs_job_name}{script.split('.')[0]}-{group_tag}"
        just_scenario = full_scenario.rsplit('___', 1)[0]
        scenario_value = f"{base_symbol}_polygon_min/{just_scenario}/aggregated-{base_symbol}_polygon_min_{just_scenario}_aggregationQueryTemplate-all.csv.lzo"
        symbol_with_provider = f"{base_symbol}_polygon_min"

        print(f"Submitting graph job with name: {job_name} with scenario: {scenario_value}")
        graph_response = batch_client.submit_job(jobName=job_name, dependsOn=[{'jobId': agg_job_id}],
                                                 jobQueue=queue_name, jobDefinition="r-graphs",
                                                 containerOverrides={"command": [scenario_value, script],
                                                                     'environment': [
                                                                         {'name': 'MOCHI_AGGREGATION_BUCKET',
                                                                          'value': os.environ.get(
                                                                              'MOCHI_AGGREGATION_BUCKET')},
                                                                         {'name': 'MOCHI_GRAPHS_BUCKET',
                                                                          'value': os.environ.get(
                                                                              'MOCHI_GRAPHS_BUCKET')}

                                                                     ]},
                                                 tags={"Scenario": just_scenario, "Symbol": base_symbol,
                                                       "SubmissionGroupTag": group_tag, "TradeType": trade_type,
                                                       "TaskType": "graph"})

        if script == "bestTraders.r":
            best_traders_job_id = graph_response['jobId']
            print(f"Submitted bestTraders.r graph job with ID: {best_traders_job_id}")

    # Submit trade-extract job
    trade_extract_job_name = f"trade-extract-{base_symbol}-{group_tag}"
    print(f"Submitting trade-extract job with name: {trade_extract_job_name}")
    trade_extract_response = batch_client.submit_job(jobName=trade_extract_job_name, jobQueue=queue_name,
                                                     jobDefinition="trade-extract",
                                                     dependsOn=[{'jobId': best_traders_job_id}], containerOverrides={
            "command": ["--symbol", symbol_with_provider, "--scenario", scenario_template],
            'environment': [{'name': 'MOCHI_GRAPHS_BUCKET', 'value': os.environ.get('MOCHI_GRAPHS_BUCKET')},
                            {'name': 'MOCHI_TRADES_BUCKET', 'value': os.environ.get('TRADES_BUCKET_NAME')},
                            {'name': 'MOCHI_PROD_TRADE_EXTRACTS', 'value': os.environ.get('MOCHI_PROD_TRADE_EXTRACTS')}

                            ]}, tags={"Scenario": scenario_template, "Symbol": base_symbol,
                                      "SubmissionGroupTag": group_tag, "TaskType": "trade-extract"})

    trade_extract_job_id = trade_extract_response['jobId']
    print(f"Submitted trade-extract job with ID: {trade_extract_job_id}")

    # Submit py-trade-lens job
    py_trade_lens_job_name = f"py-trade-lens-{base_symbol}-{group_tag}"
    print(f"Submitting py-trade-lens job with name: {py_trade_lens_job_name}")
    py_trade_lens_response = batch_client.submit_job(jobName=py_trade_lens_job_name, jobQueue=queue_name,
                                                     jobDefinition="py-trade-lens",
                                                     dependsOn=[{'jobId': trade_extract_job_id}], containerOverrides={
            "command": ["--symbol", symbol_with_provider, "--scenario", scenario_template]},
                                                     tags={"Scenario": scenario_template, "Symbol": base_symbol,
                                                           "SubmissionGroupTag": group_tag,
                                                           "TaskType": "py-trade-lens"})

    py_trade_lens_job_id = py_trade_lens_response['jobId']
    print(f"Submitted py-trade-lens job with ID: {py_trade_lens_job_id}")

    # Submit trade-summary job
    trade_summary_job_name = f"trade_summary-{base_symbol}-{group_tag}"
    print(f"Submitting trade-summary job with name: {trade_summary_job_name}")
    trade_summary_response = batch_client.submit_job(jobName=trade_summary_job_name, jobQueue=queue_name,
                                                     jobDefinition="trade-summary",
                                                     dependsOn=[{'jobId': py_trade_lens_job_id}],
                                                     containerOverrides={"command": ["--symbol", symbol_with_provider]},
                                                     tags={"Symbol": base_symbol, "SubmissionGroupTag": group_tag,
                                                           "TaskType": "trade_summary"})

    print(f"Submitted trade-summary job with ID: {trade_summary_response['jobId']}")

    # Return the results
    return {'statusCode': 200, 'body': json.dumps(
        {'message': f'Successfully submitted job chain for {ticker}', 'polygonJobId': polygon_job_id,
         'enhanceJobId': enhance_job_id, 'tradesJobId': trades_job_id, 'groupTag': group_tag})}


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

        # Return the values as separate items, not as a dictionary
        return ticker, from_date, to_date
    except Exception as e:
        print(f"Error extracting arguments from event body: {str(e)}")
        raise ValueError("Could not extract arguments from event body")
