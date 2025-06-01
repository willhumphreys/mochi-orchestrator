def generate_s3_path(ticker, asset_type, source='polygon', timeframe='1min', group_tag=None):
    # Construct the S3 key (path)
    s3_path = f"{asset_type}/{ticker}/{source}"

    s3_key = s3_path + f"/{ticker}_{source}_{timeframe}.csv.lzo"

    # Prefix the S3 key with group_tag if provided
    if group_tag:
        s3_key = f"{group_tag}/{s3_key}"

    return s3_key
