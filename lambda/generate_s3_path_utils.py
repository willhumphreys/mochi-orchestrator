from datetime import datetime


def generate_s3_path(ticker, asset_type, source='polygon', timeframe='1min'):

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

    s3_key = s3_path + f"/{ticker}_{source}_{timeframe}.csv.lzo"

    return s3_key