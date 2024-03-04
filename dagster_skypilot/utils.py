import os

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

    This reads the credentials for AWS and Lambda Labs from env vars (set in the
    Dagster Cloud UI) and then populates the expected key files accordingly.
    """
    lambda_key_file = UPath.home() / ".lambda_cloud" / "lambda_keys"
    aws_key_file = UPath.home() / ".aws" / "credentials"

    # Don't overwrite local keys, but always populate them dynamically in
    # Dagster Cloud
    if not get_environment() == "LOCAL":
        lambda_key_file.parent.mkdir(parents=True, exist_ok=True)
        aws_key_file.parent.mkdir(parents=True, exist_ok=True)

        with lambda_key_file.open("w") as f:
            f.write("api_key = {}".format(os.getenv("LAMBDA_LABS_API_KEY")))

        with aws_key_file.open("w") as f:
            f.write(
                "[default]\n"
                f"aws_access_key_id = {os.getenv('AWS_ACCESS_KEY_ID')}\n"
                f"aws_secret_access_key = {os.getenv('AWS_SECRET_ACCESS_KEY')}\n"
            )
