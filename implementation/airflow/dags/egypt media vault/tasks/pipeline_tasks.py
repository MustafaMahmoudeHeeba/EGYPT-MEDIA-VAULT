
"""
Airflow-side callables for the granular Egypt Media Vault DAG.

These are thin adapters. They

    * derive the warehouse run ID and scheduling metadata from the Airflow
      context (the same deterministic values in every task, no XCom needed),
    * call one ``execute_*`` function of
      pipeline.egypt_media_vault.orchestration.stage_runner,
    * translate its exceptions into Airflow exceptions,
    * guarantee that only a SMALL summary is returned (and therefore pushed to
      XCom). Article data never leaves the checkpoint store.

Project modules are imported inside the callables so the scheduler does not
load heavy dependencies (sentence-transformers, SQLAlchemy, Azure SDK) every
time it parses the DAG file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from airflow.exceptions import AirflowException, AirflowFailException

# Hard ceiling for anything returned to XCom (bytes of JSON).
MAX_XCOM_BYTES = 4096

# Tasks that run after everything else, whatever happened upstream.
FINALIZATION_TASK_IDS = ("record_operational_facts", "assert_pipeline_succeeded")

_FAILED_STATES = {"failed", "upstream_failed"}


# ---------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------


def _state_name(state) -> str:
    return str(getattr(state, "value", state) or "").lower()


def metadata_from_context(context):
    """RunMetadata of the DAG run a task instance belongs to."""

    from pipeline.egypt_media_vault.orchestration.run_identity import (
        build_run_metadata,
    )

    dag_run = context["dag_run"]

    # Use init_run as the stable pipeline start.
    # DagRun.start_date can change when a DAG run resumes after clearing tasks.
    task_instances = dag_run.get_task_instances()

    init_task = next(
        (ti for ti in task_instances if ti.task_id == "init_run"),
        None,
    )

    pipeline_start_date = (
        init_task.start_date
        if init_task is not None and init_task.start_date is not None
        else dag_run.start_date
    )

    return build_run_metadata(
        dag_id=dag_run.dag_id,
        airflow_run_id=dag_run.run_id,
        run_type=dag_run.run_type,
        logical_date=context["logical_date"],
        data_interval_end=context.get("data_interval_end"),
        start_date=pipeline_start_date,
    )


def _xcom_safe(summary):
    """Reject anything that is not a small JSON-friendly dict."""

    encoded = json.dumps(summary, default=str)

    if len(encoded.encode("utf-8")) > MAX_XCOM_BYTES:
        raise AirflowException(
            f"Task summary is {len(encoded)} bytes; XCom is reserved for "
            f"small metadata (limit {MAX_XCOM_BYTES} bytes). Article data "
            "belongs in the run checkpoint."
        )

    return json.loads(encoded)


def _run_stage(function_name: str, context, **kwargs):
    from pipeline.egypt_media_vault.orchestration import stage_runner
    from pipeline.egypt_media_vault.orchestration.run_state import (
        RunState,
        RunStateError,
    )

    meta = metadata_from_context(context)
    state = RunState(meta.run_id)

    try:
        summary = getattr(stage_runner, function_name)(state, meta, **kwargs)

    except stage_runner.NonRetryableStageError as exc:
        raise AirflowFailException(str(exc)) from exc

    except stage_runner.PipelineStageError as exc:
        raise AirflowException(str(exc)) from exc

    except RunStateError as exc:
        raise AirflowFailException(str(exc)) from exc

    return _xcom_safe(summary)


# ---------------------------------------------------------------------
# Pipeline tasks (one callable per Airflow task)
# ---------------------------------------------------------------------


def init_run(**context):
    retention_days = float(os.environ.get("EMV_RUN_STATE_RETENTION_DAYS", "3"))

    return _run_stage("execute_init_run", context, retention_days=retention_days)


def scrape_sources(**context):
    return _run_stage("execute_scrape", context)


def stage_raw_articles(**context):
    return _run_stage("execute_stage_raw", context)


def store_bronze(**context):
    return _run_stage("execute_bronze", context)


def validate_and_normalize(**context):
    return _run_stage("execute_process", context)


def deduplicate_articles(**context):
    return _run_stage("execute_dedup", context)


def cluster_stories(**context):
    return _run_stage("execute_cluster", context)


def persist_story_ids(**context):
    return _run_stage("execute_story_ids", context)


def load_dwh(**context):
    return _run_stage("execute_dwh", context)


def store_silver(**context):
    return _run_stage("execute_silver", context)


def run_integrity_checks(**context):
    return _run_stage("execute_integrity", context)


# ---------------------------------------------------------------------
# Finalization
# ---------------------------------------------------------------------


def _other_task_instances(context):
    dag_run = context["dag_run"]

    return [
        ti
        for ti in dag_run.get_task_instances()
        if ti.task_id not in FINALIZATION_TASK_IDS
    ]


def _failed_task_summary(task_instances) -> str | None:
    failed = sorted(
        f"{ti.task_id} ({_state_name(ti.state)})"
        for ti in task_instances
        if _state_name(ti.state) in _FAILED_STATES
    )

    if not failed:
        return None

    return "Airflow tasks failed or were not run: " + ", ".join(failed)


def _resolve_finished_at(task_instances) -> datetime:
    """
    End of the run = end of the last real pipeline task. Using the task
    instances (not "now") makes every retry of the finalization task write the
    same end timestamp.
    """

    end_dates = [ti.end_date for ti in task_instances if ti.end_date is not None]

    if end_dates:
        return max(end_dates).astimezone(timezone.utc)

    return datetime.now(timezone.utc)


def record_operational_facts(**context):
    """
    trigger_rule = all_done: runs after success, failure or skipped tasks.

    Fails (and is retried by Airflow) only when the fact rows could not be
    written. The upserts make a retry safe; it never duplicates rows.
    """

    task_instances = _other_task_instances(context)

    return _run_stage(
        "execute_operational_facts",
        context,
        finished_at=_resolve_finished_at(task_instances),
        failure_summary=_failed_task_summary(task_instances),
    )


def assert_pipeline_succeeded(**context):
    """
    trigger_rule = all_done leaf task.

    Airflow decides a DAG run's state from its LEAF tasks. record_operational_
    facts must run after failures (all_done) and therefore succeeds, which
    would hide an upstream failure and mark the whole run "success". This task
    is the leaf that re-raises it.
    """

    own_id = context["task_instance"].task_id

    problems = [
        f"{ti.task_id} ({_state_name(ti.state)})"
        for ti in context["dag_run"].get_task_instances()
        if ti.task_id != own_id and _state_name(ti.state) in _FAILED_STATES
    ]

    if problems:
        raise AirflowFailException(
            "Pipeline run failed: " + ", ".join(sorted(problems))
        )

    return {"result": "all tasks succeeded"}
