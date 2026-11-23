"""
Stage order and gating for the full EGYPT-MEDIA-VAULT pipeline.

run_pipeline() is the former main(): it contains the execution order and the
gating decisions, and nothing else. All business logic lives in the stage
modules. Airflow tasks can import and call the same stage functions
individually.

run_pipeline() wraps the stage sequence (_run_stages) so that the operational
facts (fact_pipeline_run / fact_source_collection) are written for every run,
including runs that stop early or end through an exception.
"""

from datetime import datetime, timezone

from pipeline.egypt_media_vault.config.settings import settings

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.dwh import run_dwh_loading
from pipeline.egypt_media_vault.orchestration.ingestion import run_scraping
from pipeline.egypt_media_vault.orchestration.integrity import run_integrity_checks
from pipeline.egypt_media_vault.orchestration.models import PipelineResults
from pipeline.egypt_media_vault.orchestration.operational_facts import (
    run_operational_fact_loading,
)
from pipeline.egypt_media_vault.orchestration.processing import (
    run_deduplication,
    run_normalization,
    run_story_clustering,
    run_validation,
)
from pipeline.egypt_media_vault.orchestration.reporting import (
    print_cluster_details,
    print_final_report,
    print_source_summary,
    print_story_coverage,
)
from pipeline.egypt_media_vault.orchestration.staging import run_sql_staging_insert
from pipeline.egypt_media_vault.orchestration.story_ids import save_story_ids
from pipeline.egypt_media_vault.orchestration.storage import run_bronze_storage, run_silver_storage


def _run_stages(results: PipelineResults) -> bool:
    """
    Run every stage in the original order.

    results.run_id must already be set (see run_context.create_pipeline_results).
    Returns True when the final report passes, False otherwise.
    """

    print_section(
        "EGYPT-MEDIA-VAULT - "
        "FULL PIPELINE INTEGRATION TEST"
    )

    print(
        "Environment:",
        settings.app_env,
    )

    print(
        "Application:",
        settings.app_name,
    )

    print(
        "Similarity threshold:",
        settings.story_similarity_threshold,
    )

    print(
        "Pipeline Run ID:",
        results.run_id,
    )

    # -----------------------------------------------------
    # STEP 1: SCRAPING
    # -----------------------------------------------------

    run_scraping(results)

    if not results.raw_articles:
        print_section("TEST STOPPED")
        print(
            "No raw articles were collected."
        )
        return False

    # -----------------------------------------------------
    # STEP 1.5: SQL STAGING
    # -----------------------------------------------------

    run_sql_staging_insert(results)

    # -----------------------------------------------------
    # STEP 1.6: BRONZE STORAGE
    # -----------------------------------------------------

    run_bronze_storage(results)

    # -----------------------------------------------------
    # STEP 2: VALIDATION
    # -----------------------------------------------------

    run_validation(results)

    # -----------------------------------------------------
    # STEP 3: NORMALIZATION
    # -----------------------------------------------------

    if results.valid_raw_articles:
        run_normalization(results)

    # -----------------------------------------------------
    # STEP 4: DEDUPLICATION
    # -----------------------------------------------------

    if results.normalized_articles:
        run_deduplication(results)

    # -----------------------------------------------------
    # STEP 5: STORY CLUSTERING
    # -----------------------------------------------------

    if results.unique_articles:
        run_story_clustering(results)

        # -------------------------------------------------
        # STEP 5.1: PERSIST AND VERIFY STORY IDs
        # -------------------------------------------------

        save_story_ids(results)

        # -------------------------------------------------
        # STEP 5.2: LOAD DATA WAREHOUSE
        # -------------------------------------------------

        run_dwh_loading(results)

        # -------------------------------------------------
        # STEP 5.5: SILVER STORAGE
        # -------------------------------------------------

        run_silver_storage(results)

    # -----------------------------------------------------
    # STEP 6: CLUSTER DETAILS
    # -----------------------------------------------------

    print_cluster_details(results)

    # -----------------------------------------------------
    # STEP 7: STORY COVERAGE
    # -----------------------------------------------------

    print_story_coverage(results)

    # -----------------------------------------------------
    # STEP 8: INTEGRITY CHECKS
    # -----------------------------------------------------

    checks = run_integrity_checks(results)

    # -----------------------------------------------------
    # STEP 9: SOURCE SUMMARY
    # -----------------------------------------------------

    print_source_summary(results)

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    return print_final_report(
        results,
        checks,
    )


def run_pipeline(results: PipelineResults) -> bool:
    """
    Run the full pipeline and record its operational facts.

    The stage sequence and its return value are exactly those of
    _run_stages(). Afterwards, in a finally block (so early stops and
    uncaught exceptions are covered as well), the UTC end timestamp is
    recorded and fact_pipeline_run / fact_source_collection are loaded.

    Operational fact loading never raises and never changes the pipeline
    result: a failure there is printed and recorded in
    results.database_errors only.
    """

    if results.started_at is None:
        results.started_at = datetime.now(timezone.utc)

    try:
        return _run_stages(results)

    except BaseException as exc:
        results.run_error = f"{type(exc).__name__}: {exc}"
        raise

    finally:
        results.finished_at = datetime.now(timezone.utc)

        run_operational_fact_loading(results)
