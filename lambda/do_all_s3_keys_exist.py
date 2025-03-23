import boto3
from typing import List


def do_all_s3_keys_exist(bucket_name: str, s3_keys: List[str]) -> bool:
    """
    Check if all the provided S3 keys exist in the specified bucket.

    Args:
        bucket_name: Name of the S3 bucket to check
        s3_keys: List of S3 key paths to check for existence

    Returns:
        bool: True if all keys exist, False if any key is missing
    """
    s3_client = boto3.client('s3')

    try:
        for s3_key in s3_keys:
            try:
                # Check if the object exists by trying to get its metadata
                s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                print(f"File exists: s3://{bucket_name}/{s3_key}")
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # File doesn't exist
                    print(f"File doesn't exist: s3://{bucket_name}/{s3_key}")
                    return False
                else:
                    # Some other error occurred
                    print(f"Error checking file: s3://{bucket_name}/{s3_key}, Error: {str(e)}")
                    raise e

        # If we got here, all files exist
        return True

    except Exception as e:
        print(f"Unexpected error checking S3 files: {str(e)}")
        # It's safer to assume files don't exist if there's an error
        return False
