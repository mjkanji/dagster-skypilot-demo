import os
from textwrap import dedent

from upath import UPath


def get_environment() -> str:
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
        return "PROD"
    return "LOCAL"


def populate_keyfiles():
    """
    SkyPilot only supports reading credentials from key files and not environment
    variables.

    This reads the required credentials from env vars (set in the Dagster Cloud
    UI) and then populates the expected key files accordingly.

    This is currently set up for AWS and Lambda Labs only but you can use it as
    a template to set up the details for your choice of cloud provider.
    """
    # Determine the environment
    deployment_type = get_environment()

    # Specify the expected key file paths
    lambda_key_file = UPath.home() / ".lambda_cloud" / "lambda_keys"
    aws_key_file = UPath.home() / ".aws" / "credentials"

    # Read the credentials from env vars
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", None)
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    lambda_labs_key = os.getenv("LAMBDA_LABS_API_KEY", None)

    # Never overwrite local keys
    if deployment_type == "LOCAL":
        return

    # If AWS secrets are found, populate the relevant key file
    if aws_access_key and aws_secret_key:
        aws_key_file.parent.mkdir(parents=True, exist_ok=True)
        with aws_key_file.open("w") as f:
            key_text = f"""\
                [default]
                aws_access_key_id = {aws_access_key}
                aws_secret_access_key = {aws_secret_key}
            """
            f.write(dedent(key_text))

    # If a Lambda Labs API key is found, populate the relevant key file
    if lambda_labs_key:
        lambda_key_file.parent.mkdir(parents=True, exist_ok=True)
        with lambda_key_file.open("w") as f:
            f.write(f"api_key = {lambda_labs_key}")
