from datetime import datetime


def generate_s3_path(ticker, asset_type, source='polygon'):
    """
    Generates an S3 path based on asset type, ticker, source, timeframe and current date/time.

    Args:
        ticker (str): The ticker symbol
        metadata (dict): Dictionary containing metadata, including 'asset_type'
        source (str, optional): Data source name. Defaults to 'polygon'.
        timeframe (str, optional): Data timeframe. Defaults to '1min'.

    Returns:
        tuple: A tuple containing:
            - s3_path (str): The generated S3 path structure
            - datetime_components (dict): Dictionary with datetime components used
    """
    # Get current date and time for file path construction
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    hour = now.strftime('%H')
    datetime_str = now.strftime('%Y%m%d%H%M')

    # Construct the S3 key (path)
    s3_path = f"{asset_type}/{ticker}/{source}/{year}/{month}/{day}/{hour}"

    # Return both the path and datetime components for further use
    return s3_path