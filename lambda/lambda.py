import json


def handler(event, context):
    """
    Lambda function that returns the ticker argument passed to it.
    """
    # Log the received event
    print('Received event:', json.dumps(event))

    # Extract ticker from the event
    try:
        # First try to get from JSON body (for API Gateway proxy integration)
        if 'body' in event and event['body'] is not None:
            try:
                # The body might be a string that needs parsing
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
                ticker = body.get('ticker', 'No ticker provided')
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON body: {str(e)}")
                print(f"Body content: {event['body']}")
                ticker = 'Error parsing JSON body'
        # If not found in body, check queryStringParameters
        elif 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            ticker = event['queryStringParameters'].get('ticker', 'No ticker provided')
        # If not found in query parameters, check direct event
        else:
            ticker = event.get('ticker', 'No ticker provided')
    except Exception as e:
        print(f'Error extracting ticker: {str(e)}')
        ticker = f'Error extracting ticker: {str(e)}'

    # Prepare the response
    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # Enable CORS
        },
        'body': json.dumps({
            'message': f'Processing ticker: {ticker}',
            'ticker': ticker,
            'input': event
        })
    }

    return response
