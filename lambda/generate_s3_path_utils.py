def generate_s3_path(ticker, source='polygon', timeframe='1min', group_tag=None):
    # Validate that group_tag is provided
    if not group_tag:
        raise ValueError("group_tag is required")

    # Construct the S3 key (path)
    s3_path = f"{ticker}/{source}"

    s3_key = s3_path + f"/{ticker}_{source}_{timeframe}.csv.lzo"

    # Prefix the S3 key with group_tag
    s3_key = f"{group_tag}/{s3_key}"

    return s3_key
