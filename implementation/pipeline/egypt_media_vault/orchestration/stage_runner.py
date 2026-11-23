"""
Task-sized entry points for the Airflow DAG.

Every ``execute_*`` function is ONE Airflow task. It

    1. rebuilds PipelineResults from the durable checkpoint documents of the
       stages that already finished (``rebuild_results``),
    2. calls the EXISTING stage function from this package, unchanged,
    3. turns "the stage recorded an error but returned normally" into an
       exception (``PipelineStageError``) so Airflow sees the failure,
    4. writes its own checkpoint document and returns a SMALL summary dict
       (the only thing that goes through XCom).

No business logic lives here. Hashing, deduplication, clustering, Story ID
persistence, DWH loading, Bronze/Silver serialization, integrity checks and the
operational-fact status policy are all the original functions.

This module deliberately does not import Airflow; the Airflow-side wrapper
(airflow/dags/egypt_media_vault/tasks/pipeline_tasks.py) converts
PipelineStageError -> AirflowException and NonRetryableStageError ->
AirflowFailException.

Stable identifiers used instead of id(obj)
------------------------------------------
    raw articles          list position (== position in the staging id list)
    staging_record_id     SQL identity returned by the staging insert
    article_id            sha256 of the canonical URL (deterministic)
    normalized articles   list position + staging_record_id
    duplicate_matches     {duplicate list position: representative position}
    story_cluster_id      assigned by the clusterer (random uuid -> persisted)
    story_id              persisted in dbo.raw_articles AND in the checkpoint
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from pipeline.egypt_media_vault.domain.article import Article
from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.domain.story_cluster import StoryCluster
from pipeline.egypt_media_vault.orchestration import run_state as rs
from pipeline.egypt_media_vault.orchestration.models import (
    PipelineResults,
    get_source_stats,
)
from pipeline.egypt_media_vault.orchestration.run_context import (
    create_pipeline_results,
)
from pipeline.egypt_media_vault.orchestration.run_identity import RunMetadata
from pipeline.egypt_media_vault.orchestration.run_state import RunState


class PipelineStageError(RuntimeError):
    """A stage failed. Airflow may retry the task."""


class NonRetryableStageError(PipelineStageError):
    """A stage failed in a way a retry cannot fix (Airflow: fail, no retry)."""


# Per-source counters owned by each stage (see models.SourceStats).
SCRAPE_STAT_FIELDS = (
    "scraped",
    "scrape_succeeded",
    "scrape_error",
    "attempt_count",
    "errors",
)
PROCESS_STAT_FIELDS = (
    "valid",
    "rejected",
    "normalized",
    "normalization_failed",
)
DEDUP_STAT_FIELDS = ("unique", "duplicates")

# Attributes of Article that pipeline stages mutate after normalization.
DERIVED_FIELDS = (
    "canonical_url",
    "canonical_url_hash",
    "article_id",
    "title_hash",
    "content_fingerprint",
    "story_cluster_id",
    "story_id",
)


# ---------------------------------------------------------------------
# (De)serialization helpers
# ---------------------------------------------------------------------


def _stats_slice(results: PipelineResults, fields: tuple[str, ...]) -> dict:
    sliced = {}

    for source, stats in results.source_stats.items():
        sliced[source] = {
            field: (
                list(getattr(stats, field))
                if isinstance(getattr(stats, field), list)
                else getattr(stats, field)
            )
            for field in fields
        }

    return sliced


def _apply_stats(results: PipelineResults, sliced: dict) -> None:
    for source, values in sliced.items():
        stats = get_source_stats(results, source)

        for field, value in values.items():
            setattr(
                stats,
                field,
                list(value) if isinstance(value, list) else value,
            )


def _derived(article: Article) -> dict:
    return {field: getattr(article, field) for field in DERIVED_FIELDS}


def _apply_derived(articles: list, derived: list) -> None:
    if len(articles) != len(derived):
        raise rs.RunStateError(
            "Checkpoint is inconsistent: "
            f"{len(derived)} derived records for {len(articles)} articles."
        )

    for article, values in zip(articles, derived):
        for field, value in values.items():
            setattr(article, field, value)


def _is_ok(document: dict | None) -> bool:
    return bool(document) and document.get("status") == "ok"


def _save_ok(state: RunState, stage: str, document: dict) -> None:
    state.save(stage, {**document, "status": "ok"})


def _save_failed(
    state: RunState,
    stage: str,
    document: dict,
    message: str,
) -> None:
    """
    A failed stage keeps only what the operational facts need (source
    statistics). Downstream tasks treat it as missing.
    """

    state.save(stage, {**document, "status": "failed", "error": message})


def _require_ok(state: RunState, *stages: str) -> None:
    for stage in stages:
        document = state.load(stage)

        if not _is_ok(document):
            raise NonRetryableStageError(
                f"Upstream checkpoint '{stage}' of run {state.run_id} is "
                "missing or belongs to a failed stage. Fix the failed task "
                "and clear it together with everything downstream."
            )


# ---------------------------------------------------------------------
# Rebuild PipelineResults in a fresh process
# ---------------------------------------------------------------------


def rebuild_results(
    state: RunState,
    meta: RunMetadata,
    load_raw: bool = False,
) -> PipelineResults:
    """
    Recreate PipelineResults from the checkpoint documents that exist.

    The id()-keyed maps are rebuilt HERE, inside the current process, from
    stable identifiers. Documents of failed stages only contribute their
    statistics. Missing documents are tolerated (a failed run is still
    summarised by the operational facts).

    load_raw=False skips the (large) raw article payloads for tasks that do
    not need them.
    """

    results = create_pipeline_results(meta.run_id)
    results.started_at = meta.started_at

    raw_articles: list[RawArticle] = []

    # ---- scrape -------------------------------------------------------
    scrape = state.load(rs.SCRAPE)

    if scrape:
        results.configured_sources = list(scrape["configured_sources"])
        results.source_errors = list(scrape["source_errors"])
        _apply_stats(results, scrape["source_stats"])

        if _is_ok(scrape) and load_raw:
            raw_articles = [RawArticle(**item) for item in scrape["raw_articles"]]
            results.raw_articles = raw_articles

    # ---- staging ids --------------------------------------------------
    staging = state.load(rs.STAGE_RAW)
    staging_ids: list[int] = []

    if _is_ok(staging):
        staging_ids = list(staging["staging_record_ids"])

        if load_raw:
            if len(staging_ids) != len(raw_articles):
                raise rs.RunStateError(
                    f"{len(staging_ids)} staging ids for "
                    f"{len(raw_articles)} raw articles."
                )

            results.staging_record_ids = {
                id(article): staging_id
                for article, staging_id in zip(raw_articles, staging_ids)
            }

    # ---- validation + normalization -----------------------------------
    process = state.load(rs.PROCESS)

    if process:
        _apply_stats(results, process["source_stats"])

    if _is_ok(process):
        results.normalized_articles = [
            Article(**entry["article"]) for entry in process["normalized"]
        ]

        for entry, article in zip(
            process["normalized"],
            results.normalized_articles,
        ):
            if entry["staging_record_id"] is not None:
                results.normalized_staging_ids[id(article)] = entry[
                    "staging_record_id"
                ]

        results.normalization_errors = list(process["normalization_errors"])

        if load_raw:
            results.valid_raw_articles = [
                raw_articles[index] for index in process["valid_seqs"]
            ]

    normalized = results.normalized_articles

    # ---- deduplication ------------------------------------------------
    dedup = state.load(rs.DEDUP)

    if dedup:
        _apply_stats(results, dedup["source_stats"])

    if _is_ok(dedup):
        _apply_derived(normalized, dedup["derived"])

        results.unique_articles = [
            normalized[index] for index in dedup["unique_indices"]
        ]
        results.duplicate_articles = [
            normalized[index] for index in dedup["duplicate_indices"]
        ]
        results.duplicate_matches = {
            id(normalized[int(duplicate_index)]): normalized[unique_index]
            for duplicate_index, unique_index in dedup["matches"].items()
        }

    # ---- clustering ---------------------------------------------------
    cluster = state.load(rs.CLUSTER)

    if _is_ok(cluster):
        _apply_derived(normalized, cluster["derived"])

        results.clusters = [StoryCluster(**item) for item in cluster["clusters"]]

    # ---- story id persistence + verification --------------------------
    story_ids = state.load(rs.STORY_IDS)

    if _is_ok(story_ids):
        _apply_derived(normalized, story_ids["derived"])

        results.expected_story_ids = {
            int(staging_id): story_id
            for staging_id, story_id in story_ids["expected_story_ids"].items()
        }
        results.story_ids_persisted = story_ids["story_ids_persisted"]
        results.story_ids_not_persisted = story_ids["story_ids_not_persisted"]
        results.story_ids_verified = story_ids["story_ids_verified"]
        results.story_ids_verification_failed = story_ids[
            "story_ids_verification_failed"
        ]

    # ---- side branches ------------------------------------------------
    bronze = state.load(rs.BRONZE)

    if _is_ok(bronze):
        results.bronze_file = bronze["bronze_file"]

    dwh = state.load(rs.DWH)

    if _is_ok(dwh):
        results.dwh_articles_loaded = dwh["dwh_articles_loaded"]
        results.dwh_articles_failed = dwh["dwh_articles_failed"]

    silver = state.load(rs.SILVER)

    if _is_ok(silver):
        results.silver_file = silver["silver_file"]

    return results


# ---------------------------------------------------------------------
# 1. Initialize run
# ---------------------------------------------------------------------


def execute_init_run(
    state: RunState,
    meta: RunMetadata,
    retention_days: float = 3,
) -> dict:
    # Fail early and clearly if the container is not configured.
    from pipeline.egypt_media_vault.config.settings import settings  # noqa: F401

    state.ensure()

    state.save(
        rs.MANIFEST,
        {
            "run_id": meta.run_id,
            "dag_id": meta.dag_id,
            "airflow_run_id": meta.airflow_run_id,
            "run_type": meta.run_type,
            "logical_date": meta.logical_date,
            "started_at": meta.started_at,
            "scheduled_timestamp": meta.scheduled_timestamp,
        },
    )

    purged = state.purge_old_runs(retention_days)

    print(f"Pipeline Run ID: {meta.run_id}")
    print(f"Airflow run: {meta.airflow_run_id} ({meta.run_type})")
    print(f"Run state directory: {state.directory}")

    return {
        "run_id": meta.run_id,
        "run_type": meta.run_type,
        "purged_old_workspaces": len(purged),
    }


# ---------------------------------------------------------------------
# 2. Scraping
# ---------------------------------------------------------------------


def execute_scrape(
    state: RunState,
    meta: RunMetadata,
    scrapers: list | None = None,
) -> dict:
    """
    Source-level policy is the original one: a scraper that raises is recorded
    as a failed source and the run continues with the other sources. The task
    only fails when NO raw article was collected (the original "TEST STOPPED"
    case). The checkpoint (incl. every source's outcome) is written in both
    cases, because the operational facts are built from it.
    """

    from pipeline.egypt_media_vault.orchestration.ingestion import run_scraping

    previous = state.load(rs.SCRAPE)

    # Scraper invocations of an earlier attempt of this same run still count.
    prior_attempts = {
        source: values["attempt_count"]
        for source, values in (previous or {}).get("source_stats", {}).items()
    }

    state.begin_stage(rs.SCRAPE)

    results = create_pipeline_results(meta.run_id)
    results.started_at = meta.started_at

    run_scraping(results, scrapers)

    for source, stats in results.source_stats.items():
        stats.attempt_count += prior_attempts.get(source, 0)

    document = {
        "configured_sources": list(results.configured_sources),
        "source_errors": list(results.source_errors),
        "source_stats": _stats_slice(results, SCRAPE_STAT_FIELDS),
        "raw_count": len(results.raw_articles),
    }

    if not results.raw_articles:
        message = "No raw articles were collected."
        _save_failed(state, rs.SCRAPE, document, message)
        raise NonRetryableStageError(message)

    document["raw_articles"] = [asdict(a) for a in results.raw_articles]

    _save_ok(state, rs.SCRAPE, document)

    return {
        "raw_articles": len(results.raw_articles),
        "sources_configured": len(results.configured_sources),
        "sources_failed": len(results.source_errors),
        "per_source": {
            source: stats.scraped
            for source, stats in results.source_stats.items()
        },
    }


# ---------------------------------------------------------------------
# 3a. SQL staging (idempotent)
# ---------------------------------------------------------------------


def _adopt_existing_staging(run_id: str, raw_articles: list) -> list[int] | None:
    """
    insert_raw_articles() always INSERTs. If an earlier attempt already staged
    this run (for example the task died after the SQL commit but before its
    checkpoint was written), adopt those rows instead of inserting duplicates.
    """

    from pipeline.egypt_media_vault.warehouse.run_repository import (
        get_staging_records_for_run,
    )

    existing = get_staging_records_for_run(run_id)

    if not existing:
        return None

    existing_urls = [url for _, url in existing]
    expected_urls = [article.url for article in raw_articles]

    if existing_urls != expected_urls:
        raise NonRetryableStageError(
            f"SQL staging already holds {len(existing)} rows for run "
            f"{run_id} that differ from the {len(expected_urls)} articles "
            "just scraped (the scrape task was re-run after staging). "
            "Refusing to mix two different batches under one run ID; "
            "trigger a new DAG run instead."
        )

    return [staging_id for staging_id, _ in existing]


def execute_stage_raw(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.staging import (
        run_sql_staging_insert,
    )

    state.begin_stage(rs.STAGE_RAW)
    _require_ok(state, rs.SCRAPE)

    results = rebuild_results(state, meta, load_raw=True)

    adopted = _adopt_existing_staging(meta.run_id, results.raw_articles)

    if adopted is not None:
        staging_ids = adopted
        print(f"Adopted {len(staging_ids)} staging rows from an earlier attempt.")

    else:
        run_sql_staging_insert(results)

        if results.database_errors or len(results.staging_record_ids) != len(
            results.raw_articles
        ):
            raise PipelineStageError(
                "SQL staging insertion failed: "
                + "; ".join(results.database_errors or ["no staging ids returned"])
            )

        staging_ids = [
            results.staging_record_ids[id(article)]
            for article in results.raw_articles
        ]

    _save_ok(
        state,
        rs.STAGE_RAW,
        {
            "staging_record_ids": staging_ids,
            "adopted": adopted is not None,
        },
    )

    return {
        "staging_records": len(staging_ids),
        "adopted_existing_rows": adopted is not None,
    }


# ---------------------------------------------------------------------
# 3b. Bronze
# ---------------------------------------------------------------------


def execute_bronze(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.storage import run_bronze_storage

    state.begin_stage(rs.BRONZE)
    _require_ok(state, rs.SCRAPE)

    results = rebuild_results(state, meta, load_raw=True)

    run_bronze_storage(results)

    # run_bronze_storage() catches every exception and only records it.
    if results.storage_errors or not results.bronze_file:
        raise PipelineStageError(
            "Bronze storage failed: "
            + "; ".join(results.storage_errors or ["no file was uploaded"])
        )

    _save_ok(state, rs.BRONZE, {"bronze_file": results.bronze_file})

    return {
        "bronze_file": results.bronze_file,
        "articles": len(results.raw_articles),
    }


# ---------------------------------------------------------------------
# 4. Validation + normalization
# ---------------------------------------------------------------------


def execute_process(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.processing import (
        run_normalization,
        run_validation,
    )
    from pipeline.egypt_media_vault.warehouse.run_repository import (
        delete_validation_issues_for_run,
    )

    state.begin_stage(rs.PROCESS)
    _require_ok(state, rs.STAGE_RAW)

    results = rebuild_results(state, meta, load_raw=True)

    # insert_validation_issues() appends; remove an earlier attempt's rows.
    removed = delete_validation_issues_for_run(meta.run_id)

    if removed:
        print(f"Removed {removed} validation issue rows of an earlier attempt.")

    run_validation(results)

    if results.valid_raw_articles:
        run_normalization(results)

    seq_by_object = {id(a): i for i, a in enumerate(results.raw_articles)}

    document = {
        "source_stats": _stats_slice(results, PROCESS_STAT_FIELDS),
        "validation_issue_count": len(results.validation_issues),
    }

    if results.database_errors:
        message = "Validation/normalization SQL errors: " + "; ".join(
            results.database_errors
        )
        _save_failed(state, rs.PROCESS, document, message)
        raise PipelineStageError(message)

    document.update(
        {
            "valid_seqs": [seq_by_object[id(a)] for a in results.valid_raw_articles],
            "normalized": [
                {
                    "staging_record_id": results.normalized_staging_ids.get(
                        id(article)
                    ),
                    "article": asdict(article),
                }
                for article in results.normalized_articles
            ],
            "normalization_errors": list(results.normalization_errors),
        }
    )

    _save_ok(state, rs.PROCESS, document)

    return {
        "raw": len(results.raw_articles),
        "valid": len(results.valid_raw_articles),
        "rejected": len(results.raw_articles) - len(results.valid_raw_articles),
        "normalized": len(results.normalized_articles),
        "normalization_failures": len(results.normalization_errors),
        "validation_issues": len(results.validation_issues),
    }


# ---------------------------------------------------------------------
# 5. Deduplication
# ---------------------------------------------------------------------


def execute_dedup(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.processing import run_deduplication

    state.begin_stage(rs.DEDUP)
    _require_ok(state, rs.PROCESS)

    results = rebuild_results(state, meta)

    if results.normalized_articles:
        run_deduplication(results)

    position = {id(a): i for i, a in enumerate(results.normalized_articles)}

    document = {"source_stats": _stats_slice(results, DEDUP_STAT_FIELDS)}

    if results.database_errors:
        message = "Deduplication SQL errors: " + "; ".join(results.database_errors)
        _save_failed(state, rs.DEDUP, document, message)
        raise PipelineStageError(message)

    document.update(
        {
            "derived": [_derived(a) for a in results.normalized_articles],
            "unique_indices": [position[id(a)] for a in results.unique_articles],
            "duplicate_indices": [
                position[id(a)] for a in results.duplicate_articles
            ],
            "matches": {
                str(position[duplicate_id]): position[id(representative)]
                for duplicate_id, representative in results.duplicate_matches.items()
            },
        }
    )

    _save_ok(state, rs.DEDUP, document)

    return {
        "normalized": len(results.normalized_articles),
        "unique": len(results.unique_articles),
        "duplicates": len(results.duplicate_articles),
    }


# ---------------------------------------------------------------------
# 6. Story clustering
# ---------------------------------------------------------------------


def execute_cluster(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.processing import (
        run_story_clustering,
    )

    state.begin_stage(rs.CLUSTER)
    _require_ok(state, rs.DEDUP)

    results = rebuild_results(state, meta)

    # Story cluster IDs are random (story_<uuid4>), so clustering is NOT
    # repeatable: its output is persisted here once and every later task
    # reads it from the checkpoint instead of clustering again.
    if results.unique_articles:
        run_story_clustering(results)

    _save_ok(
        state,
        rs.CLUSTER,
        {
            "derived": [_derived(a) for a in results.normalized_articles],
            "clusters": [asdict(c) for c in results.clusters],
        },
    )

    return {
        "unique_articles": len(results.unique_articles),
        "clusters": len(results.clusters),
    }


# ---------------------------------------------------------------------
# 7. Story ID persistence + verification
# ---------------------------------------------------------------------


def execute_story_ids(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.story_ids import save_story_ids

    state.begin_stage(rs.STORY_IDS)
    _require_ok(state, rs.CLUSTER)

    results = rebuild_results(state, meta)

    if results.unique_articles:
        save_story_ids(results)

    # save_story_ids() records problems in counters / database_errors and
    # returns normally. Same conditions the integrity checks use.
    problems = []

    if results.database_errors:
        problems.extend(results.database_errors)

    if results.unique_articles:
        if results.story_ids_not_persisted:
            problems.append(
                f"{results.story_ids_not_persisted} Story IDs not persisted"
            )

        if results.story_ids_verification_failed:
            problems.append(
                f"{results.story_ids_verification_failed} Story IDs failed "
                "SQL read-back verification"
            )

        if len(results.expected_story_ids) != len(results.normalized_articles):
            problems.append(
                f"{len(results.expected_story_ids)} Story IDs expected for "
                f"{len(results.normalized_articles)} normalized articles"
            )

        if results.story_ids_verified != len(results.expected_story_ids):
            problems.append(
                f"{results.story_ids_verified} of "
                f"{len(results.expected_story_ids)} Story IDs verified"
            )

    if problems:
        raise PipelineStageError(
            "Story ID persistence/verification failed: " + "; ".join(problems)
        )

    _save_ok(
        state,
        rs.STORY_IDS,
        {
            "derived": [_derived(a) for a in results.normalized_articles],
            "expected_story_ids": {
                str(staging_id): story_id
                for staging_id, story_id in results.expected_story_ids.items()
            },
            "story_ids_persisted": results.story_ids_persisted,
            "story_ids_not_persisted": results.story_ids_not_persisted,
            "story_ids_verified": results.story_ids_verified,
            "story_ids_verification_failed": results.story_ids_verification_failed,
        },
    )

    return {
        "persisted": results.story_ids_persisted,
        "verified": results.story_ids_verified,
        "verification_failures": results.story_ids_verification_failed,
    }


# ---------------------------------------------------------------------
# 8. DWH loading
# ---------------------------------------------------------------------


def _verify_checkpoint_story_ids_against_sql(results: PipelineResults) -> None:
    """
    Guard against a checkpoint that diverged from SQL (for example a clustering
    task that was re-run after the Story IDs of an earlier attempt had already
    been persisted): the DWH may only receive Story IDs that SQL still holds.
    """

    from pipeline.egypt_media_vault.warehouse.article_repository import (
        get_story_ids_by_staging_ids,
    )

    staging_by_article = {
        id(article): results.normalized_staging_ids.get(id(article))
        for article in results.unique_articles
    }

    staging_ids = [sid for sid in staging_by_article.values() if sid is not None]

    persisted = get_story_ids_by_staging_ids(staging_ids)

    mismatched = [
        article.article_id
        for article in results.unique_articles
        if persisted.get(staging_by_article[id(article)]) != article.story_id
    ]

    if mismatched:
        raise NonRetryableStageError(
            f"{len(mismatched)} Story IDs in the checkpoint no longer match "
            "dbo.raw_articles. Clear persist_story_ids and run it again."
        )


def execute_dwh(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.dwh import run_dwh_loading

    state.begin_stage(rs.DWH)
    _require_ok(state, rs.STORY_IDS)

    results = rebuild_results(state, meta)

    if results.unique_articles:
        _verify_checkpoint_story_ids_against_sql(results)

    run_dwh_loading(results)

    # run_dwh_loading() catches every exception and only records it.
    if results.database_errors or results.dwh_articles_failed:
        raise PipelineStageError(
            "DWH loading failed: "
            + "; ".join(results.database_errors or ["articles failed to load"])
        )

    if results.dwh_articles_loaded != len(results.unique_articles):
        raise PipelineStageError(
            f"DWH loaded {results.dwh_articles_loaded} of "
            f"{len(results.unique_articles)} unique articles."
        )

    _save_ok(
        state,
        rs.DWH,
        {
            "dwh_articles_loaded": results.dwh_articles_loaded,
            "dwh_articles_failed": results.dwh_articles_failed,
        },
    )

    return {
        "unique_articles": len(results.unique_articles),
        "dwh_articles_loaded": results.dwh_articles_loaded,
    }


# ---------------------------------------------------------------------
# 9. Silver
# ---------------------------------------------------------------------


def execute_silver(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.storage import run_silver_storage

    state.begin_stage(rs.SILVER)
    _require_ok(state, rs.STORY_IDS)

    results = rebuild_results(state, meta)

    run_silver_storage(results)

    # run_silver_storage() catches every exception and only records it.
    if results.storage_errors or (
        results.unique_articles and not results.silver_file
    ):
        raise PipelineStageError(
            "Silver storage failed: "
            + "; ".join(results.storage_errors or ["no file was uploaded"])
        )

    _save_ok(state, rs.SILVER, {"silver_file": results.silver_file})

    return {
        "silver_file": results.silver_file,
        "articles": len(results.unique_articles),
    }


# ---------------------------------------------------------------------
# 10. Integrity checks
# ---------------------------------------------------------------------


def execute_integrity(state: RunState, meta: RunMetadata) -> dict:
    from pipeline.egypt_media_vault.orchestration.integrity import (
        run_integrity_checks,
    )
    from pipeline.egypt_media_vault.orchestration.reporting import (
        print_cluster_details,
        print_final_report,
        print_source_summary,
        print_story_coverage,
    )

    state.begin_stage(rs.INTEGRITY)
    _require_ok(state, rs.DWH, rs.SILVER, rs.BRONZE)

    results = rebuild_results(state, meta, load_raw=True)

    print_cluster_details(results)
    print_story_coverage(results)

    checks = run_integrity_checks(results)

    print_source_summary(results)

    # print_final_report() returns False for any failed check.
    if not print_final_report(results, checks):
        failed = [name for name, passed in checks.items() if not passed]

        raise PipelineStageError(
            "Integrity checks failed: " + ", ".join(failed or ["final report"])
        )

    _save_ok(state, rs.INTEGRITY, {"checks": checks})

    return {"checks": len(checks), "failed_checks": 0}


# ---------------------------------------------------------------------
# 13. Operational facts (finalization)
# ---------------------------------------------------------------------


def execute_operational_facts(
    state: RunState,
    meta: RunMetadata,
    finished_at: datetime,
    failure_summary: str | None = None,
) -> dict:
    """
    Record fact_pipeline_run / fact_source_collection for this run.

    Runs whether or not upstream tasks succeeded, so it tolerates missing
    checkpoints: a source whose scrape never ran is reported with the
    original "not invoked" semantics (NULL collected count).

    Safe to retry: the loader upserts on (run_id) and (run_id, source_key),
    and every input (run ID, start, scheduled time, end time, statistics) is
    deterministic for the DAG run.
    """

    from pipeline.egypt_media_vault.orchestration.operational_facts import (
        build_operational_facts,
        run_operational_fact_loading,
    )

    try:
        results = rebuild_results(state, meta)

    except rs.RunStateError as exc:
        # Never lose the operational fact because a checkpoint is unreadable.
        results = create_pipeline_results(meta.run_id)
        results.started_at = meta.started_at
        failure_summary = " ".join(
            part
            for part in (failure_summary, f"Checkpoint unreadable: {exc}")
            if part
        )

    results.finished_at = finished_at
    results.run_error = failure_summary

    loaded = run_operational_fact_loading(
        results,
        scheduled_timestamp=meta.scheduled_timestamp,
    )

    if not loaded:
        raise PipelineStageError(
            "Operational fact loading failed: "
            + "; ".join(results.database_errors or ["see task log"])
        )

    run, sources = build_operational_facts(
        results,
        scheduled_timestamp=meta.scheduled_timestamp,
    )

    return {
        "run_id": run.run_id,
        "run_status": run.run_status,
        "run_type": meta.run_type,
        "scheduled": run.scheduled_timestamp is not None,
        "sources": {
            source.source_id: source.collection_outcome for source in sources
        },
    }
