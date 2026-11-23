
"""
Operational facts stage: fact_pipeline_run and fact_source_collection.

This is the thin orchestration layer (like dwh.py for the article DWH). It
turns PipelineResults into plain fact dataclasses, derives the statuses and
calls the warehouse loader. The SQL lives in
warehouse/operational_fact_loader.py.

Status policy (scraper-call outcome only; downstream failures such as SQL
staging, Bronze, Silver or DWH loading never change it):

    source outcome
        scraper call returned (including zero articles)   -> Succeeded
        scraper raised / never completed / never invoked  -> Failed (Scraping)

    run status
        every configured source succeeded                 -> Success
        some, but not all, sources succeeded              -> Partial
        no source succeeded                               -> Failed

run_operational_fact_loading() never raises and never changes the pipeline
result. A failure is printed and recorded in results.database_errors.
"""

from datetime import datetime

from pipeline.egypt_media_vault.scrapers.source_registry import (
    SCRAPER_REGISTRY,
)
from pipeline.egypt_media_vault.warehouse.operational_fact_loader import (
    OUTCOME_FAILED_SCRAPING,
    OUTCOME_SUCCEEDED,
    RUN_STATUS_FAILED,
    RUN_STATUS_PARTIAL,
    RUN_STATUS_SUCCESS,
    PipelineRunFact,
    SourceCollectionFact,
    load_operational_facts,
)

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults
from pipeline.egypt_media_vault.orchestration.staging import (
    record_database_error,
)


def _configured_source_ids(results: PipelineResults) -> list[str]:
    """
    Sources the run was configured with, in order.

    run_scraping() records them. When it never got that far (for example
    create_scrapers() raised), fall back to the registry so every configured
    source still gets a row.
    """
    configured = results.configured_sources or list(SCRAPER_REGISTRY)

    return list(dict.fromkeys(configured))


def _build_source_fact(
    source_id: str,
    results: PipelineResults,
) -> SourceCollectionFact:
    stats = results.source_stats.get(source_id)

    # Never invoked: the run ended before this scraper was called.
    if stats is None or stats.attempt_count == 0:
        message = (
            "Scraper was not invoked: the pipeline run ended before "
            "this source was scraped."
        )

        if results.run_error:
            message = f"{message} Run error: {results.run_error}"

        return SourceCollectionFact(
            source_id=source_id,
            collection_outcome=OUTCOME_FAILED_SCRAPING[0],
            failed_step=OUTCOME_FAILED_SCRAPING[1],
            attempt_count=0,
            articles_collected_count=None,
            articles_rejected_count=0,
            duplicate_record_count=0,
            error_description=message,
        )

    if stats.scrape_succeeded is True:
        return SourceCollectionFact(
            source_id=source_id,
            collection_outcome=OUTCOME_SUCCEEDED[0],
            failed_step=OUTCOME_SUCCEEDED[1],
            attempt_count=stats.attempt_count,
            # Zero is a real, known count for a successful scraper call.
            articles_collected_count=stats.scraped,
            articles_rejected_count=stats.rejected,
            duplicate_record_count=stats.duplicates,
            error_description=None,
        )

    # Invoked, but the scraper raised or never completed. The collected
    # count is unknown, so it is NULL rather than 0.
    error_description = stats.scrape_error

    if not error_description:
        error_description = "Scraper did not complete."

        if results.run_error:
            error_description = (
                f"{error_description} Run error: {results.run_error}"
            )

    return SourceCollectionFact(
        source_id=source_id,
        collection_outcome=OUTCOME_FAILED_SCRAPING[0],
        failed_step=OUTCOME_FAILED_SCRAPING[1],
        attempt_count=stats.attempt_count,
        articles_collected_count=None,
        articles_rejected_count=stats.rejected,
        duplicate_record_count=stats.duplicates,
        error_description=error_description,
    )


def derive_run_status(sources: list[SourceCollectionFact]) -> str:
    """Run status from the source scraper outcomes."""
    if not sources:
        raise ValueError(
            "Cannot derive a run status without any configured source."
        )

    succeeded = sum(
        1
        for source in sources
        if (source.collection_outcome, source.failed_step)
        == OUTCOME_SUCCEEDED
    )

    if succeeded == len(sources):
        return RUN_STATUS_SUCCESS

    if succeeded == 0:
        return RUN_STATUS_FAILED

    return RUN_STATUS_PARTIAL


def build_operational_facts(
    results: PipelineResults,
    scheduled_timestamp: datetime | None = None,
) -> tuple[PipelineRunFact, list[SourceCollectionFact]]:
    """
    Build the run fact and one source fact per configured source.

    scheduled_timestamp is populated for scheduled Airflow runs.
    It remains None for manual runs and the local pipeline runner.
    """
    if not results.run_id:
        raise RuntimeError("PipelineResults.run_id is not set.")

    if results.started_at is None:
        raise RuntimeError("PipelineResults.started_at is not set.")

    sources = [
        _build_source_fact(source_id, results)
        for source_id in _configured_source_ids(results)
    ]

    run = PipelineRunFact(
        run_id=results.run_id,
        run_status=derive_run_status(sources),
        start_timestamp=results.started_at,
        end_timestamp=results.finished_at,
        run_count=1,
        scheduled_timestamp=scheduled_timestamp,
        missed_reason=None,
    )

    return run, sources


def run_operational_fact_loading(
    results: PipelineResults,
    scheduled_timestamp: datetime | None = None,
) -> bool:
    """
    Load fact_pipeline_run and fact_source_collection for this run.

    Returns True when loaded and False when loading failed. Never raises
    and never changes the pipeline result.
    """
    print_section("OPERATIONAL FACTS: PIPELINE RUN AND SOURCE COLLECTION")

    try:
        run, sources = build_operational_facts(
            results,
            scheduled_timestamp=scheduled_timestamp,
        )

        summary = load_operational_facts(run, sources)

        print(f"fact_pipeline_run status: {run.run_status}")
        print(
            "fact_pipeline_run rows loaded: "
            f"{summary['pipeline_run_rows']}"
        )
        print(
            "fact_source_collection rows loaded: "
            f"{summary['source_collection_rows']}"
        )

        return True

    except Exception as exc:
        print("\nOPERATIONAL FACT LOADING FAILED")
        print(f"Run ID: {results.run_id}")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print(
            "The pipeline result is unchanged; the article DWH load "
            "is not affected."
        )

        try:
            record_database_error(
                results,
                "Operational fact loading failed",
                exc,
            )
        except Exception as recording_error:
            print(
                "Could not record the operational fact failure: "
                f"{recording_error}"
            )

        return False
