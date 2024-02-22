import sky

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
sky.launch(task, cluster_name="dnn")
