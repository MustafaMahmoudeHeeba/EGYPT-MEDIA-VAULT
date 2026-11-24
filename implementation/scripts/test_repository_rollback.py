
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import text

from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.warehouse.database import engine

from pipeline.egypt_media_vault.warehouse.article_repository import (
    insert_raw_articles,
    insert_validation_issues,
    update_processing_metadata,
)


def test_repository_rollback():
    run_id = f"ROLLBACK_TEST_{uuid4().hex}"

    article = RawArticle(
        title="Rollback Test Article",
        source="test_source",
        url="https://example.com/rollback-test",
        publication_date=datetime.now(timezone.utc),
        raw_publication_text="Test publication date",
        category="Test",
        author="Test Author",
        description="Temporary rollback test",
        content="This article must not remain in the database.",
    )

    issue = SimpleNamespace(
        field_name="publication_date",
        issue_type="TEST_WARNING",
        message="Temporary rollback test issue",
        severity="warning",
        detected_at=datetime.now(timezone.utc),
    )

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            # 1. Insert a temporary staging record.
            staging_ids = insert_raw_articles(
                [article],
                run_id,
                connection=connection,
            )

            assert len(staging_ids) == 1

            staging_id = staging_ids[0]

            # 2. Insert a temporary validation issue.
            inserted_issues = insert_validation_issues(
                staging_id,
                [issue],
                connection=connection,
            )

            assert inserted_issues == 1

            # 3. Update the staging record.
            update_processing_metadata(
                staging_id,
                processing_status="Validated",
                connection=connection,
            )

            # 4. Verify all operations inside the transaction.
            article_row = connection.execute(
                text("""
                    SELECT processing_status
                    FROM dbo.raw_articles
                    WHERE staging_record_id = :staging_id
                      AND run_id = :run_id;
                """),
                {
                    "staging_id": staging_id,
                    "run_id": run_id,
                },
            ).fetchone()

            issue_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM dbo.raw_article_issues
                    WHERE staging_record_id = :staging_id;
                """),
                {"staging_id": staging_id},
            ).scalar_one()

            assert article_row is not None
            assert article_row.processing_status == "Validated"
            assert issue_count == 1

            print("INSERT: PASSED")
            print("VALIDATION ISSUE INSERT: PASSED")
            print("UPDATE: PASSED")
            print("TRANSACTION VERIFICATION: PASSED")

        finally:
            # Never commit this test.
            transaction.rollback()

    # 5. Verify that the test article no longer exists.
    with engine.connect() as verification_connection:
        remaining_count = verification_connection.execute(
            text("""
                SELECT COUNT(*)
                FROM dbo.raw_articles
                WHERE run_id = :run_id;
            """),
            {"run_id": run_id},
        ).scalar_one()

        assert remaining_count == 0

    print("ROLLBACK: PASSED")
    print("DATABASE CLEANUP: PASSED")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    test_repository_rollback()
