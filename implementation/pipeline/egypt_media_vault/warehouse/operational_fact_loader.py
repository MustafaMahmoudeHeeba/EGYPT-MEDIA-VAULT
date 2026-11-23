"""
Operational (pipeline-monitoring) fact loading.

Loads:

    dbo.fact_pipeline_run        grain: one row per pipeline run
    dbo.fact_source_collection   grain: one row per configured source
                                        per pipeline run

This module is deliberately separate from fact_loader.py, which owns the
article-grain fact (fact_news_articles). It takes plain dataclasses, not
PipelineResults, so it has no dependency on the orchestration layer and can
be called from an Airflow task later.

Transaction rules:

    - Both tables are written in ONE transaction, parent row first.
    - Every dimension key is resolved BEFORE the first write, so a missing
      dimension row raises and nothing is written.
    - When no connection is supplied, the load opens its own transaction.
      It must never be given the article DWH connection: operational facts
      are independent of the article load.
    - Re-running with the same run_id updates the existing rows
      (primary keys: run_id; run_id + source_key).

Existing lookups are reused from fact_loader.py:
    _get_date_key, _get_source_key, _to_utc_naive, _connection_scope
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import text

from pipeline.egypt_media_vault.warehouse.fact_loader import (
    _connection_scope,
    _get_date_key,
    _get_source_key,
    _to_utc_naive,
)


# ---------------------------------------------------------------------
# Dimension labels (dbo.dim_run_status / dbo.dim_collection_outcome)
#
# dim_collection_outcome has several "Failed" rows that differ only by
# failed_step, so outcomes are always resolved by the
# (collection_outcome, failed_step) pair. Only the two outcomes below are
# used today: the source outcome is the scraper-call outcome only.
# ---------------------------------------------------------------------

RUN_STATUS_SUCCESS = "Success"
RUN_STATUS_PARTIAL = "Partial"
RUN_STATUS_FAILED = "Failed"

OUTCOME_SUCCEEDED = ("Succeeded", "Not applicable")
OUTCOME_FAILED_SCRAPING = ("Failed", "Scraping")

RUN_ID_MAX_LENGTH = 100
TEXT_MAX_LENGTH = 2000


@dataclass(frozen=True)
class PipelineRunFact:
    """One row of fact_pipeline_run (dimension keys are resolved on load)."""

    run_id: str
    run_status: str
    start_timestamp: datetime
    end_timestamp: datetime | None
    run_count: int = 1
    scheduled_timestamp: datetime | None = None
    missed_reason: str | None = None


@dataclass(frozen=True)
class SourceCollectionFact:
    """One row of fact_source_collection (keys are resolved on load)."""

    source_id: str
    collection_outcome: str
    failed_step: str
    attempt_count: int
    articles_collected_count: int | None
    articles_rejected_count: int = 0
    duplicate_record_count: int = 0
    error_description: str | None = None


# ---------------------------------------------------------------------
# Validation and small helpers
# ---------------------------------------------------------------------


def _truncate(value: str | None, max_length: int = TEXT_MAX_LENGTH) -> str | None:
    """Fit a value into an NVARCHAR(2000) column; empty becomes NULL."""
    if value is None:
        return None

    text_value = str(value)

    if not text_value.strip():
        return None

    if len(text_value) <= max_length:
        return text_value

    return text_value[: max_length - 3] + "..."


def _is_count(value, allow_none: bool = False) -> bool:
    if value is None:
        return allow_none

    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    )


def _validate_operational_facts(
    run: PipelineRunFact,
    sources: list[SourceCollectionFact],
) -> None:
    run_id = run.run_id

    if not isinstance(run_id, str) or not run_id.strip():
        raise RuntimeError("Cannot load operational facts without a run_id.")

    if len(run_id) > RUN_ID_MAX_LENGTH:
        raise RuntimeError(
            f"run_id is longer than {RUN_ID_MAX_LENGTH} characters."
        )

    if not isinstance(run.start_timestamp, datetime):
        raise RuntimeError(
            "Cannot load fact_pipeline_run without a start_timestamp."
        )

    if not run.run_status:
        raise RuntimeError("Cannot load fact_pipeline_run without run_status.")

    if (
        not isinstance(run.run_count, int)
        or isinstance(run.run_count, bool)
        or run.run_count < 1
    ):
        raise RuntimeError("run_count must be a positive integer.")

    if run.end_timestamp is not None:
        if _to_utc_naive(run.end_timestamp) < _to_utc_naive(
            run.start_timestamp
        ):
            raise RuntimeError(
                "end_timestamp is earlier than start_timestamp."
            )

    seen_source_ids: set[str] = set()

    for source in sources:
        source_id = source.source_id

        if not isinstance(source_id, str) or not source_id.strip():
            raise RuntimeError(
                "Cannot load fact_source_collection without a source_id."
            )

        if source_id in seen_source_ids:
            raise RuntimeError(
                f"Duplicate source_id supplied for one run: {source_id!r}."
            )

        seen_source_ids.add(source_id)

        if not source.collection_outcome or not source.failed_step:
            raise RuntimeError(
                f"Source {source_id!r} has no collection outcome."
            )

        if not _is_count(source.attempt_count):
            raise RuntimeError(
                f"Source {source_id!r}: attempt_count must be an "
                "integer >= 0."
            )

        if not _is_count(source.articles_collected_count, allow_none=True):
            raise RuntimeError(
                f"Source {source_id!r}: articles_collected_count must be "
                "NULL or an integer >= 0."
            )

        if not _is_count(source.articles_rejected_count):
            raise RuntimeError(
                f"Source {source_id!r}: articles_rejected_count must be "
                "an integer >= 0."
            )

        if not _is_count(source.duplicate_record_count):
            raise RuntimeError(
                f"Source {source_id!r}: duplicate_record_count must be "
                "an integer >= 0."
            )


# ---------------------------------------------------------------------
# Dimension key lookups (dim_date and dim_source are reused from
# fact_loader.py)
# ---------------------------------------------------------------------


def _get_run_status_key(run_status: str, connection) -> int:
    row = connection.execute(
        text(
            """
            SELECT TOP 1
                run_status_key
            FROM dbo.dim_run_status
            WHERE run_status = :run_status
            ORDER BY run_status_key
            """
        ),
        {"run_status": run_status},
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"No dim_run_status row found for run_status={run_status!r}."
        )

    return int(row.run_status_key)


def _get_collection_outcome_key(
    collection_outcome: str,
    failed_step: str,
    connection,
) -> int:
    row = connection.execute(
        text(
            """
            SELECT TOP 1
                collection_outcome_key
            FROM dbo.dim_collection_outcome
            WHERE collection_outcome = :collection_outcome
              AND failed_step = :failed_step
            ORDER BY collection_outcome_key
            """
        ),
        {
            "collection_outcome": collection_outcome,
            "failed_step": failed_step,
        },
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "No dim_collection_outcome row found for "
            f"collection_outcome={collection_outcome!r}, "
            f"failed_step={failed_step!r}."
        )

    return int(row.collection_outcome_key)


# ---------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------


def _upsert_pipeline_run(connection, parameters: dict) -> None:
    existing = connection.execute(
        text(
            """
            SELECT
                run_id
            FROM dbo.fact_pipeline_run
            WHERE run_id = :run_id
            """
        ),
        {"run_id": parameters["run_id"]},
    ).fetchone()

    if existing is None:
        connection.execute(
            text(
                """
                INSERT INTO dbo.fact_pipeline_run (
                    run_id,
                    run_date_key,
                    run_status_key,
                    run_count,
                    scheduled_timestamp,
                    start_timestamp,
                    end_timestamp,
                    missed_reason
                )
                VALUES (
                    :run_id,
                    :run_date_key,
                    :run_status_key,
                    :run_count,
                    :scheduled_timestamp,
                    :start_timestamp,
                    :end_timestamp,
                    :missed_reason
                )
                """
            ),
            parameters,
        )
    else:
        connection.execute(
            text(
                """
                UPDATE dbo.fact_pipeline_run
                SET
                    run_date_key = :run_date_key,
                    run_status_key = :run_status_key,
                    run_count = :run_count,
                    scheduled_timestamp = :scheduled_timestamp,
                    start_timestamp = :start_timestamp,
                    end_timestamp = :end_timestamp,
                    missed_reason = :missed_reason
                WHERE run_id = :run_id
                """
            ),
            parameters,
        )


def _upsert_source_collection(connection, parameters: dict) -> None:
    existing = connection.execute(
        text(
            """
            SELECT
                run_id
            FROM dbo.fact_source_collection
            WHERE run_id = :run_id
              AND source_key = :source_key
            """
        ),
        {
            "run_id": parameters["run_id"],
            "source_key": parameters["source_key"],
        },
    ).fetchone()

    if existing is None:
        connection.execute(
            text(
                """
                INSERT INTO dbo.fact_source_collection (
                    run_id,
                    source_key,
                    run_date_key,
                    collection_outcome_key,
                    attempt_count,
                    articles_collected_count,
                    articles_rejected_count,
                    duplicate_record_count,
                    error_description
                )
                VALUES (
                    :run_id,
                    :source_key,
                    :run_date_key,
                    :collection_outcome_key,
                    :attempt_count,
                    :articles_collected_count,
                    :articles_rejected_count,
                    :duplicate_record_count,
                    :error_description
                )
                """
            ),
            parameters,
        )
    else:
        connection.execute(
            text(
                """
                UPDATE dbo.fact_source_collection
                SET
                    run_date_key = :run_date_key,
                    collection_outcome_key = :collection_outcome_key,
                    attempt_count = :attempt_count,
                    articles_collected_count = :articles_collected_count,
                    articles_rejected_count = :articles_rejected_count,
                    duplicate_record_count = :duplicate_record_count,
                    error_description = :error_description
                WHERE run_id = :run_id
                  AND source_key = :source_key
                """
            ),
            parameters,
        )


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def load_operational_facts(
    run: PipelineRunFact,
    sources: Iterable[SourceCollectionFact],
    connection=None,
) -> dict[str, int]:
    """
    Insert or update the fact_pipeline_run row and the
    fact_source_collection rows of one pipeline run, atomically.

    run_date_key (on the run row and on every source row) is the date key
    of the UTC date of start_timestamp.

    Returns:
        {"pipeline_run_rows": 1, "source_collection_rows": <n>}
    """
    source_list = list(sources)

    _validate_operational_facts(run, source_list)

    start_timestamp = _to_utc_naive(run.start_timestamp)
    end_timestamp = _to_utc_naive(run.end_timestamp)
    scheduled_timestamp = _to_utc_naive(run.scheduled_timestamp)

    with _connection_scope(connection) as conn:
        # -------------------------------------------------------------
        # 1. Resolve every key first. Any failure raises before the
        #    first write, so nothing partial is ever written.
        # -------------------------------------------------------------
        run_date_key = _get_date_key(start_timestamp, conn)

        run_status_key = _get_run_status_key(run.run_status, conn)

        resolved: list[tuple[SourceCollectionFact, int, int]] = []
        seen_source_keys: dict[int, str] = {}

        for source in source_list:
            source_key = _get_source_key(source.source_id, conn)

            if source_key in seen_source_keys:
                raise RuntimeError(
                    f"Sources {seen_source_keys[source_key]!r} and "
                    f"{source.source_id!r} resolve to the same "
                    f"source_key={source_key}."
                )

            seen_source_keys[source_key] = source.source_id

            outcome_key = _get_collection_outcome_key(
                source.collection_outcome,
                source.failed_step,
                conn,
            )

            resolved.append((source, source_key, outcome_key))

        # -------------------------------------------------------------
        # 2. Parent row first (fact_source_collection.run_id is an FK).
        # -------------------------------------------------------------
        _upsert_pipeline_run(
            conn,
            {
                "run_id": run.run_id,
                "run_date_key": run_date_key,
                "run_status_key": run_status_key,
                "run_count": run.run_count,
                "scheduled_timestamp": scheduled_timestamp,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "missed_reason": _truncate(run.missed_reason),
            },
        )

        # -------------------------------------------------------------
        # 3. Child rows.
        # -------------------------------------------------------------
        for source, source_key, outcome_key in resolved:
            _upsert_source_collection(
                conn,
                {
                    "run_id": run.run_id,
                    "source_key": source_key,
                    "run_date_key": run_date_key,
                    "collection_outcome_key": outcome_key,
                    "attempt_count": source.attempt_count,
                    "articles_collected_count": (
                        source.articles_collected_count
                    ),
                    "articles_rejected_count": (
                        source.articles_rejected_count
                    ),
                    "duplicate_record_count": source.duplicate_record_count,
                    "error_description": _truncate(source.error_description),
                },
            )

    return {
        "pipeline_run_rows": 1,
        "source_collection_rows": len(resolved),
    }
