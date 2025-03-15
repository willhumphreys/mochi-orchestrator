import json


def handler(event, context):
    """
    Simple Hello World Lambda function.
    """
    # Log the received event
    print('Received event:', json.dumps(event))

    # Prepare the response
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello World from Lambda!',
            'input': event
        })
    }

    return response
