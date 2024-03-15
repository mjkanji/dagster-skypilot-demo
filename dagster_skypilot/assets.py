import json
import os

import sky
import yaml
from dagster import AssetExecutionContext, Config, asset
from pydantic import Field
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


class SkyPilotConfig(Config):
    """A minimal set of configurations for SkyPilot. This is NOT intended as a
    complete or exhaustive representation of a Task YAML config."""

    max_steps: int = Field(
        default=10, description="Number of training steps to perform."
    )
    spot_launch: bool = Field(
        default=False, description="Should the task be run as a managed spot job?"
    )


@asset(group_name="ai")
def skypilot_model(context: AssetExecutionContext, config: SkyPilotConfig) -> None:
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
            "SKYPILOT_BUCKET": skypilot_bucket,
            "MAX_STEPS": config.max_steps,
        },
    )
    task.workdir = str(parent_dir.absolute() / "scripts")

    try:
        if config.spot_launch:
            context.log.info(
                "Launching managed spot job. See stdout for SkyPilot logs."
            )
            sky.spot_launch(task, "gemma")  # type: ignore
        else:
            context.log.info("Launching task. See stdout for SkyPilot logs.")
            sky.launch(task, "gemma")  # type: ignore

        context.log.info("Task completed.")
        context.add_output_metadata(get_metrics(context, skypilot_bucket))

    finally:
        teardown_all_clusters(context.log)
        ...
