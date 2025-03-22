import subprocess
import requests
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_path: str = '.env') -> Dict[str, str]:
    """
    Load environment variables from a .env file
    """
    env_vars = {}
    env_file = Path(env_path)

    if env_file.exists():
        print(f"Loading environment variables from {env_path}")
        with open(env_file, 'r') as file:
            for line in file:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key-value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('\'"')
                    env_vars[key] = value
                    # Also set in environment
                    os.environ[key] = value

        print(f"Loaded {len(env_vars)} environment variables")
    else:
        print(f"Warning: .env file not found at {env_path}")

    return env_vars


def deploy_cdk_stack():
    """Deploy the CDK stack and return the success status"""
    print("Deploying MochiComputeStack...")

    try:
        # Run the CDK deploy command and capture output
        result = subprocess.run(
            ["cdk", "deploy", "MochiComputeStack"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print("Deployment output:")
        print(result.stdout)

        if result.stderr:
            print("Deployment warnings/errors:")
            print(result.stderr)

        print("Deployment complete.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Deployment failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False


def make_api_request(api_url: Optional[str] = None):
    """Make the API request to the backtest endpoint"""
    # Give some time for the deployment to fully propagate (if needed)
    print("Waiting 5 seconds before making the API request...")
    time.sleep(5)

    # API endpoint - use from environment if available
    url = api_url or os.environ.get("API_URL",
                                    "https://6a3jgki3ul.execute-api.eu-central-1.amazonaws.com/prod/backtest")

    # Request headers
    headers = {
        "Content-Type": "application/json"
    }

    # Request payload - can use environment variables if defined
    payload = {
        "ticker": os.environ.get("TICKER", "AAPL"),
        "from_date": os.environ.get("FROM_DATE", "2025-03-21"),
        "to_date": os.environ.get("TO_DATE", "2050-03-16")
    }

    # Make the request
    print(f"Making POST request to {url}...")
    print(f"With payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Print response status and content
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        # Pretty-print if JSON response
        try:
            print("\nFormatted response:")
            print(json.dumps(response.json(), indent=2))
        except:
            pass

    except Exception as e:
        print(f"Error making the request: {e}")


if __name__ == "__main__":
    # Load environment variables from .env file
    env_vars = load_env_file()

    # Deploy the stack first
    success = deploy_cdk_stack()

    # Only proceed with API request if deployment was successful
    if success:
        make_api_request()
    else:
        print("Skipping API request due to deployment failure.")
        sys.exit(1)
