import os
from pathlib import Path

import sky
from dagster import AssetExecutionContext, asset
from sky.check import check

from dagster_skypilot.consts import DEPLOYMENT_TYPE


@asset(group_name="ai")
def skypilot_model(context: AssetExecutionContext) -> None:
    # Set up the API credentials by reading from the deployment env vars
    lambda_key_file = Path.home() / ".lambda_cloud" / "lambda_keys"
    aws_key_file = Path.home() / ".aws" / "credentials"

    # Don't overwrite local keys, but always populate them dynamically in
    # Dagster Cloud
    if not DEPLOYMENT_TYPE == "local":
        lambda_key_file.touch(exist_ok=True)
        aws_key_file.touch(exist_ok=True)

        with lambda_key_file.open("w") as f:
            f.write("api_key = {}".format(os.getenv("LAMBDA_LABS_API_KEY")))

        with aws_key_file.open("w") as f:
            f.write(
                "[default]\n"
                f"aws_access_key_id = {os.getenv('AWS_ACCESS_KEY_ID')}\n"
                f"aws_secret_access_key = {os.getenv('AWS_SECRET_ACCESS_KEY')}\n"
            )

    context.log.info(f"{DEPLOYMENT_TYPE = }")
    context.log.info(f"{lambda_key_file.exists() = }")
    context.log.info(f"{aws_key_file.exists() = }")

    check()

    # The setup command.
    setup = r"""
        set -e  # Exit if any command failed.
        git clone https://github.com/huggingface/transformers/ || true
        cd transformers
        pip install .
        cd examples/pytorch/text-classification
        pip install -r requirements.txt
        """

    # The command to run.  Will be run under the working directory.
    run = r"""
        set -e  # Exit if any command failed.
        cd transformers/examples/pytorch/text-classification
        python run_glue.py \
            --model_name_or_path bert-base-cased \
            --dataset_name imdb  \
            --do_train \
            --max_seq_length 128 \
            --per_device_train_batch_size 32 \
            --learning_rate 2e-5 \
            --max_steps 50 \
            --output_dir /tmp/imdb/ --overwrite_output_dir \
            --fp16
        """

    # Mount an external bucket
    storage_mounts = {
        "/dagster-skypilot-bucket": sky.Storage(
            source="s3://dagster-skypilot-bucket", mode=sky.StorageMode.MOUNT
        )
    }

    task = sky.Task(
        "huggingface",
        workdir=".",
        setup=setup,
        run=run,
    )

    task.set_resources(
        sky.Resources(sky.Lambda(), accelerators={"A10": 1})
    ).set_storage_mounts(storage_mounts)

    # sky.launch(task, dryrun=True)
    # sky.launch(task, cluster_name="dnn", idle_minutes_to_autostop=5, down=True)  # type: ignore

    return None
