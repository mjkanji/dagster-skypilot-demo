import os
from pathlib import Path

from dagster import AssetExecutionContext, asset
from dagster_shell import execute_shell_command

from dagster_skypilot.consts import DEPLOYMENT_TYPE


def populate_keyfiles():
    """
    SkyPilot only supports reading credentials from key files and not environment
    variables.

    This reads the credentials for AWS and Lambda Labs from env vars (set in the
    Dagster Cloud UI) and then populates the expected key files accordingly.
    """
    lambda_key_file = Path.home() / ".lambda_cloud" / "lambda_keys"
    aws_key_file = Path.home() / ".aws" / "credentials"

    # Don't overwrite local keys, but always populate them dynamically in
    # Dagster Cloud
    if not DEPLOYMENT_TYPE == "local":
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


@asset(group_name="ai")
def skypilot_model(context: AssetExecutionContext) -> None:
    # SkyPilot doesn't support reading credentials from environment variables.
    # So, we need to populate the required keyfiles.
    populate_keyfiles()

    execute_shell_command(
        "sky launch -c dnn dnn.yaml --yes -i 5 --down",
        output_logging="STREAM",
        log=context.log,
        cwd=str(Path(__file__).parent.parent),
        # Disable color and styling for rich
        env={"NO_COLOR": "1"},
    )
