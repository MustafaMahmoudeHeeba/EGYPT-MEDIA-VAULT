
from airflow.exceptions import AirflowException


def run_python_pipeline():
    """
    Execute the existing Egypt Media Vault Python pipeline.

    Airflow treats the task as failed if the pipeline returns False
    or raises an exception.
    """

    # Import project modules only when the task executes.
    from pipeline.egypt_media_vault.orchestration.pipeline import run_pipeline
    from pipeline.egypt_media_vault.orchestration.run_context import (
        create_pipeline_results,
    )

    results = create_pipeline_results()

    success = run_pipeline(results)

    if not success:
        raise AirflowException(
            "Egypt Media Vault Python pipeline failed."
        )

    return "Python pipeline completed successfully."
