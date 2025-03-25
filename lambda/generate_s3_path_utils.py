def generate_s3_path(ticker, asset_type, source='polygon', timeframe='1min'):
    # Construct the S3 key (path)
    s3_path = f"{asset_type}/{ticker}/{source}"

    s3_key = s3_path + f"/{ticker}_{source}_{timeframe}.csv.lzo"

    return s3_key