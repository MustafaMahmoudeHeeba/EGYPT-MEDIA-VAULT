
"""
Builds the granular Egypt Media Vault DAG.

The same graph is used by

    egypt_media_vault_pipeline_v2   manual-only validation copy (side by side
                                    with the existing DAG)
    egypt_media_vault_pipeline      final cut-over file (schedule */15 * * * *)

Dependency graph
----------------

    init_run
       |
    scrape_sources ---------------------+
       |                                |
    stage_raw_articles              store_bronze
       |
    validate_and_normalize
       |
    deduplicate_articles
       |
    cluster_stories
       |
    persist_story_ids
       |        \\
    load_dwh   store_silver
       \\          |
        +----- run_integrity_checks
                   |
          record_operational_facts  (trigger_rule = all_done)
                   |
                 dbt_run
                   |
                 dbt_test
                   |
          assert_pipeline_succeeded (trigger_rule = all_done, leaf)

    dbt_run also requires run_integrity_checks to succeed.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from egypt_media_vault.tasks import pipeline_tasks
from egypt_media_vault.tasks.dbt_tasks import (
    create_dbt_run_task,
    create_dbt_test_task,
)

PRODUCTION_DAG_ID = "egypt_media_vault_pipeline"
PRODUCTION_SCHEDULE = "*/15 * * * *"

DOC_MD = """
### Egypt Media Vault pipeline

Granular version of the former three-task DAG. Article data moves between tasks
through the run checkpoint (`EMV_RUN_STATE_DIR`), Azure SQL staging and ADLS -
never through XCom. See the project README for the data-movement, failure and
idempotency rules.
"""


def _python_task(task_id: str, callable_, **kwargs) -> PythonOperator:
    return PythonOperator(
        task_id=task_id,
        python_callable=callable_,
        **kwargs,
    )


def build_pipeline_dag(
    dag_id: str,
    schedule: str | None,
    extra_tags: tuple[str, ...] = (),
) -> DAG:
    with DAG(
        dag_id=dag_id,
        description=(
            "Egypt Media Vault ETL: scraping, staging, Bronze/Silver, "
            "story clustering, DWH loading, dbt"
        ),
        start_date=pendulum.datetime(2026, 11, 21, tz="UTC"),
        schedule=schedule,
        catchup=False,
        max_active_runs=1,
        default_args={
            "retries": 1,
            "retry_delay": timedelta(minutes=2),
        },
        tags=[
            "egypt-media-vault",
            "python-pipeline",
            "dbt",
            "granular",
            *extra_tags,
        ],
        doc_md=DOC_MD,
    ) as dag:

        init_run = _python_task("init_run", pipeline_tasks.init_run)

        # Re-scraping on an automatic retry would hit the news sites again and
        # is not what the monolithic task did; a manual "clear" still works.
        scrape_sources = _python_task(
            "scrape_sources",
            pipeline_tasks.scrape_sources,
            retries=0,
        )

        stage_raw_articles = _python_task(
            "stage_raw_articles",
            pipeline_tasks.stage_raw_articles,
        )

        store_bronze = _python_task("store_bronze", pipeline_tasks.store_bronze)

        validate_and_normalize = _python_task(
            "validate_and_normalize",
            pipeline_tasks.validate_and_normalize,
        )

        deduplicate_articles = _python_task(
            "deduplicate_articles",
            pipeline_tasks.deduplicate_articles,
        )

        cluster_stories = _python_task(
            "cluster_stories",
            pipeline_tasks.cluster_stories,
        )

        persist_story_ids = _python_task(
            "persist_story_ids",
            pipeline_tasks.persist_story_ids,
        )

        load_dwh = _python_task("load_dwh", pipeline_tasks.load_dwh)

        store_silver = _python_task("store_silver", pipeline_tasks.store_silver)

        run_integrity_checks = _python_task(
            "run_integrity_checks",
            pipeline_tasks.run_integrity_checks,
        )

        # Unchanged DockerOperator factories (task ids: dbt_run, dbt_test).
        dbt_run = create_dbt_run_task()
        dbt_test = create_dbt_test_task()

        record_operational_facts = _python_task(
            "record_operational_facts",
            pipeline_tasks.record_operational_facts,
            trigger_rule=TriggerRule.ALL_DONE,
            retries=2,
        )

        assert_pipeline_succeeded = _python_task(
            "assert_pipeline_succeeded",
            pipeline_tasks.assert_pipeline_succeeded,
            trigger_rule=TriggerRule.ALL_DONE,
            retries=0,
        )

        # ---- dependencies ------------------------------------------------
        init_run >> scrape_sources
        scrape_sources >> [stage_raw_articles, store_bronze]

        (
            stage_raw_articles
            >> validate_and_normalize
            >> deduplicate_articles
            >> cluster_stories
            >> persist_story_ids
            >> [load_dwh, store_silver]
        )

        [load_dwh, store_silver, store_bronze] >> run_integrity_checks

        # Record operational facts after processing and integrity checks.
        # ALL_DONE allows recording even when an upstream task has failed.
        run_integrity_checks >> record_operational_facts

        # dbt starts only after both integrity checks and fact recording succeed.
        [run_integrity_checks, record_operational_facts] >> dbt_run

        dbt_run >> dbt_test >> assert_pipeline_succeeded

        # Keep the final assertion as the DAG's leaf task.
        record_operational_facts >> assert_pipeline_succeeded

    return dag
