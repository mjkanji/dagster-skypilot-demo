import json
import os

import sky
import yaml
from dagster import AssetExecutionContext, asset
from dagster_shell import execute_shell_command
from upath import UPath

from dagster_skypilot.utils import populate_keyfiles


def get_metrics(context: AssetExecutionContext, bucket):
    with (UPath(bucket) / context.run_id / "train_results.json").open("r") as f:
        return json.load(f)


def teardown_all_clusters(logger):
    clusters = sky.status(refresh=True)

    for c in clusters:
        logger.info(f"Shutting down cluster: {c['name']}.")
        sky.down(c["name"])

    logger.info("All clusters shut down.")


@asset(group_name="ai")
def skypilot_model(context: AssetExecutionContext) -> None:
    # SkyPilot doesn't support reading credentials from environment variables.
    # So, we need to populate the required keyfiles.
    populate_keyfiles()

    skypilot_bucket = os.getenv("SKYPILOT_BUCKET")

    # The parent of the current script
    parent_dir = UPath(__file__).parent
    yaml_file = parent_dir / "finetune.yaml"
    with yaml_file.open("r", encoding="utf-8") as f:
        task_config = yaml.safe_load(f)

    task = sky.Task().from_yaml_config(
        config=task_config,
        env_overrides={  # type: ignore
            "HF_TOKEN": os.getenv("HF_TOKEN", ""),
            "DAGSTER_RUN_ID": context.run_id,
            "BUCKET_NAME": skypilot_bucket,
        },
    )
    task.workdir = str(parent_dir.absolute() / "scripts")

    try:
        sky.launch(task, cluster_name="gemma", idle_minutes_to_autostop=5)  # type: ignore
        context.add_output_metadata(get_metrics(context, skypilot_bucket))

    finally:
        teardown_all_clusters(context.log)
        ...
