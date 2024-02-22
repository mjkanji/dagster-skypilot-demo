import os

DEPLOYMENT_TYPE = (
    "branch"
    if os.environ.get("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
    else os.environ.get("DAGSTER_DEPLOYMENT", "local")
)
