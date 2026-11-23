"""
Run-scoped SQL helpers that make Airflow task retries safe.

These are the only NEW SQL statements introduced by the Airflow redesign. They
touch existing tables only (dbo.raw_articles, dbo.raw_article_issues), need no
schema change, and never modify the existing repository module.

    get_staging_records_for_run()
        Read-only. Lets the staging task ADOPT rows a previous attempt already
        inserted instead of inserting the same articles a second time
        (insert_raw_articles() always INSERTs; there is no unique key on
        run_id + url).

    delete_validation_issues_for_run()
        insert_validation_issues() appends issue_seq = MAX + 1, so re-running
        validation would duplicate every issue row. The validation stage calls
        this once at its start so a retry starts from a clean slate.
"""

from __future__ import annotations

from sqlalchemy import text

from pipeline.egypt_media_vault.warehouse.database import engine


def get_staging_records_for_run(run_id: str) -> list[tuple[int, str | None]]:
    """(staging_record_id, original_url) of a run, in insertion order."""

    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id cannot be empty.")

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    staging_record_id,
                    original_url
                FROM dbo.raw_articles
                WHERE run_id = :run_id
                ORDER BY staging_record_id;
                """
            ),
            {"run_id": run_id},
        ).fetchall()

    return [(int(row.staging_record_id), row.original_url) for row in rows]


def delete_validation_issues_for_run(run_id: str) -> int:
    """Remove the validation issue rows of one run; returns rows deleted."""

    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id cannot be empty.")

    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                DELETE issue
                FROM dbo.raw_article_issues AS issue
                INNER JOIN dbo.raw_articles AS article
                    ON article.staging_record_id = issue.staging_record_id
                WHERE article.run_id = :run_id;
                """
            ),
            {"run_id": run_id},
        )

        return int(result.rowcount or 0)
