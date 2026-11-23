"""
Run identity for Airflow-driven runs.

One Airflow DAG run maps to exactly one warehouse pipeline run ID, and every
task of that DAG run derives the SAME ID without needing XCom.

Why the Airflow ``dag_run.run_id`` is not used directly
-------------------------------------------------------
Airflow run IDs look like ``scheduled__2026-11-22T00:30:00+00:00`` or can be an
arbitrary user string (``airflow dags trigger --run-id ...``). They contain
``:`` and ``+`` and have no length guarantee, while the warehouse run ID is

    * dbo.raw_articles.run_id            NVARCHAR(100)
    * fact_pipeline_run.run_id           (loader limit: 100 characters)
    * part of the ADLS file names        raw_articles_<run_id>.json
                                         cleaned_articles_<run_id>.json

So the warehouse run ID keeps the exact shape produced by
``run_context.generate_run_id()``  ->  ``YYYYmmddTHHMMSS_ffffffZ_<8 hex>``
(32 characters, URL/file-name safe) but is derived deterministically:

    timestamp part : the DAG run's logical date (unique per DAG run in Airflow)
    suffix         : first 8 hex chars of sha256("<dag_id>|<airflow run_id>")

Retrying any task therefore reuses the same run ID, the same Bronze/Silver file
names and the same operational fact rows.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone

RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}_\d{6}Z_[0-9a-f]{8}$")
RUN_ID_MAX_LENGTH = 100


@dataclass(frozen=True)
class RunMetadata:
    """Everything a task needs to know about the DAG run it belongs to."""

    run_id: str
    dag_id: str
    airflow_run_id: str
    run_type: str
    logical_date: datetime
    started_at: datetime
    # NULL for manual / backfill runs. For scheduled runs: the moment the
    # schedule says the run was due (end of its data interval).
    scheduled_timestamp: datetime | None

    @property
    def is_scheduled(self) -> bool:
        return self.run_type == "scheduled"


def _require_aware(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include timezone information.")

    return value.astimezone(timezone.utc)


def build_warehouse_run_id(
    dag_id: str,
    airflow_run_id: str,
    logical_date: datetime,
) -> str:
    """Deterministic warehouse run ID for one Airflow DAG run."""

    if not dag_id or not airflow_run_id:
        raise ValueError("dag_id and airflow_run_id are required.")

    logical_utc = _require_aware(logical_date, "logical_date")

    suffix = hashlib.sha256(
        f"{dag_id}|{airflow_run_id}".encode("utf-8")
    ).hexdigest()[:8]

    run_id = logical_utc.strftime("%Y%m%dT%H%M%S_%fZ") + "_" + suffix

    if not RUN_ID_PATTERN.match(run_id) or len(run_id) > RUN_ID_MAX_LENGTH:
        raise RuntimeError(f"Derived an invalid run ID: {run_id!r}")

    return run_id


def build_run_metadata(
    *,
    dag_id: str,
    airflow_run_id: str,
    run_type,
    logical_date: datetime,
    data_interval_end: datetime | None,
    start_date: datetime | None,
    now: datetime | None = None,
) -> RunMetadata:
    """
    Build RunMetadata from primitive Airflow values (no Airflow import).

    ``run_type`` may be a plain string or Airflow's DagRunType enum.
    scheduled_timestamp is only set for run_type == "scheduled"; manual and
    backfill runs keep the existing "not scheduled" semantics (NULL).
    """

    run_type_text = str(getattr(run_type, "value", run_type)).lower()

    started_at = start_date or now or datetime.now(timezone.utc)

    scheduled_timestamp = None

    if run_type_text == "scheduled" and data_interval_end is not None:
        scheduled_timestamp = _require_aware(
            data_interval_end,
            "data_interval_end",
        )

    return RunMetadata(
        run_id=build_warehouse_run_id(dag_id, airflow_run_id, logical_date),
        dag_id=dag_id,
        airflow_run_id=airflow_run_id,
        run_type=run_type_text,
        logical_date=_require_aware(logical_date, "logical_date"),
        started_at=_require_aware(started_at, "start_date"),
        scheduled_timestamp=scheduled_timestamp,
    )
