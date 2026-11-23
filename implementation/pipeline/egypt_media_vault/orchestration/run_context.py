"""
Run identity.

The run ID is created exactly once per pipeline execution (by the runner or,
later, by Airflow) and is carried on PipelineResults.run_id. No stage creates
its own run ID.
"""

from datetime import datetime, timezone
from uuid import uuid4

from pipeline.egypt_media_vault.orchestration.models import PipelineResults


def generate_run_id() -> str:
    return (
        datetime.now(timezone.utc)
        .strftime(
            "%Y%m%dT%H%M%S_%fZ"
        )
        + "_"
        + uuid4().hex[:8]
    )


def create_pipeline_results(run_id: str | None = None) -> PipelineResults:
    """
    Create a fresh PipelineResults carrying one run ID.

    A caller (for example an Airflow task) may supply its own run ID;
    otherwise one is generated here.
    """

    results = PipelineResults()

    results.run_id = run_id if run_id is not None else generate_run_id()

    # Actual UTC start of the run, recorded in fact_pipeline_run.
    results.started_at = datetime.now(timezone.utc)

    return results
