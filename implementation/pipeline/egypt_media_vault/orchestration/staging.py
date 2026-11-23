"""
SQL staging persistence helpers (dbo.raw_articles / dbo.raw_article_issues).

Leaf module used by the processing, story-ID and DWH stages. It must not
import any stage module.
"""

from datetime import datetime

from pipeline.egypt_media_vault.warehouse.database import engine

from pipeline.egypt_media_vault.warehouse.article_repository import (
    insert_raw_articles,
    insert_validation_issues,
    update_processing_metadata,
)

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults


def get_timestamp_validity(raw_article) -> str:
    publication_date = raw_article.publication_date
    raw_publication_text = raw_article.raw_publication_text

    if publication_date is not None:
        if (
            isinstance(publication_date, datetime)
            and publication_date.tzinfo is not None
            and publication_date.utcoffset() is not None
        ):
            return "Valid"

        return "Invalid"

    if (
        isinstance(raw_publication_text, str)
        and raw_publication_text.strip()
    ):
        return "Invalid"

    return "Unknown"


def record_database_error(
    results: PipelineResults,
    operation: str,
    exc: Exception,
) -> None:
    message = (
        f"{operation}: {type(exc).__name__}: {exc}"
    )

    results.database_errors.append(message)

    print(f"\nDATABASE ERROR: {message}")


def run_sql_staging_insert(results: PipelineResults) -> None:
    """
    Insert every scraped RawArticle into SQL staging.

    The returned IDs are associated with the original objects,
    preserving their relationship through later pipeline stages.
    """

    print_section("SQL STAGING: RAW ARTICLE INSERTION")

    if not results.raw_articles:
        print("No raw articles available for SQL staging.")
        return

    try:
        staging_ids = insert_raw_articles(
            raw_articles=results.raw_articles,
            run_id=results.run_id,
        )

        if len(staging_ids) != len(results.raw_articles):
            raise RuntimeError(
                "SQL returned a different number of staging IDs "
                "than the number of submitted articles."
            )

        results.staging_record_ids = {
            id(article): staging_id
            for article, staging_id in zip(
                results.raw_articles,
                staging_ids,
            )
        }

        print("SQL staging insertion completed successfully.")
        print(f"Run ID: {results.run_id}")
        print(f"Inserted records: {len(staging_ids)}")

    except Exception as exc:
        record_database_error(
            results,
            "Raw article staging insertion failed",
            exc,
        )

        results.staging_record_ids.clear()


def update_staging_record(
    results: PipelineResults,
    staging_record_id: int | None,
    operation: str,
    **metadata,
) -> bool:
    """
    Update one staging record.

    The repository manages the transaction for this individual update.
    """

    if staging_record_id is None:
        return False

    try:
        update_processing_metadata(
            staging_record_id=staging_record_id,
            **metadata,
        )

        return True

    except Exception as exc:
        record_database_error(
            results,
            f"{operation} (staging ID {staging_record_id})",
            exc,
        )

        return False


def save_validation_results(
    results: PipelineResults,
    raw_article,
    issues: list,
    is_valid: bool,
) -> bool:
    """
    Atomically save validation issues and update processing status.

    Both operations use the same SQL connection and transaction.
    If either operation fails, both operations are rolled back.
    """

    staging_id = results.staging_record_ids.get(
        id(raw_article)
    )

    if staging_id is None:
        return False

    try:
        with engine.begin() as connection:

            if issues:
                inserted_count = insert_validation_issues(
                    staging_record_id=staging_id,
                    issues=issues,
                    connection=connection,
                )

                print(
                    f"  SQL validation issues saved: {inserted_count}"
                )

            update_processing_metadata(
                staging_record_id=staging_id,
                processing_status=(
                    "Validated" if is_valid else "Rejected"
                ),
                connection=connection,
            )

        return True

    except Exception as exc:
        record_database_error(
            results,
            "Atomic validation persistence failed",
            exc,
        )

        return False


def save_normalization_result(
    results: PipelineResults,
    raw_article,
    article,
) -> None:
    """
    Associate the normalized Article with its original
    SQL staging record and save normalized metadata.
    """

    staging_id = results.staging_record_ids.get(
        id(raw_article)
    )

    if staging_id is None:
        return

    results.normalized_staging_ids[id(article)] = staging_id

    update_staging_record(
        results,
        staging_id,
        "Normalization metadata update failed",
        processing_status="Normalized",
        publication_timestamp=article.publication_date,
        timestamp_validity=get_timestamp_validity(raw_article),
        standardized_source_name=article.source,
        standardized_category_name=article.category,
    )


def save_deduplication_results(
    results: PipelineResults,
) -> None:
    """
    Persist hashes and identifiers generated by
    ArticleDeduplicator.

    Current-batch duplicates receive Duplicate status.
    Unique articles remain Normalized.

    Historical deduplication is not performed here.
    """

    print_section("SQL STAGING: DEDUPLICATION METADATA")

    duplicate_ids = {
        id(article)
        for article in results.duplicate_articles
    }

    updated_count = 0

    for article in results.normalized_articles:
        staging_id = results.normalized_staging_ids.get(
            id(article)
        )

        if staging_id is None:
            continue

        status = (
            "Duplicate"
            if id(article) in duplicate_ids
            else "Normalized"
        )

        success = update_staging_record(
            results,
            staging_id,
            "Deduplication metadata update failed",
            processing_status=status,
            article_id=article.article_id,
            canonical_url_hash=article.canonical_url_hash,
            title_hash=article.title_hash,
            content_fingerprint=article.content_fingerprint,
        )

        if success:
            updated_count += 1

    print(
        f"Deduplication metadata records updated: "
        f"{updated_count}"
    )
