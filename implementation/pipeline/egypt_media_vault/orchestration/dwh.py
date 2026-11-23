"""
STEP 5.2: dimensional warehouse (star schema) loading.
"""

from pipeline.egypt_media_vault.warehouse.dwh_loader import (
    load_articles_to_dwh,
)

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults
from pipeline.egypt_media_vault.orchestration.staging import record_database_error


def run_dwh_loading(results: PipelineResults) -> None:
    """
    Load unique, processed articles into the dimensional warehouse.

    Story IDs must already be persisted in SQL staging and verified
    through SQL read-back.

    Every unique Article must also be mapped to its original
    SQL staging_record_id so the fact loader can retrieve the
    authoritative publication and ingestion metadata.
    """

    print_section("DWH: DIMENSION AND FACT LOADING")

    if not results.unique_articles:
        print("No unique articles available for DWH loading.")
        return

    try:
        # -----------------------------------------------------
        # 1. Build the verified Article ID -> Story ID mapping
        # -----------------------------------------------------

        story_ids_by_article_id = {}
        missing_story_ids = []

        for article in results.unique_articles:
            article_id = getattr(article, "article_id", None)
            story_id = getattr(article, "story_id", None)

            if not article_id or not story_id:
                missing_story_ids.append(
                    {
                        "article_id": article_id,
                        "story_id": story_id,
                        "title": article.title[:80],
                    }
                )
                continue

            if article_id in story_ids_by_article_id:
                raise RuntimeError(
                    "Duplicate article_id detected while "
                    "building the verified Story ID mapping: "
                    f"{article_id}"
                )

            story_ids_by_article_id[article_id] = story_id

        if missing_story_ids:
            raise RuntimeError(
                "Cannot load DWH because verified Story IDs "
                "are missing from "
                f"{len(missing_story_ids)} unique articles: "
                f"{missing_story_ids}"
            )

        if len(story_ids_by_article_id) != len(results.unique_articles):
            raise RuntimeError(
                "Story ID mapping count does not match "
                "the number of unique articles."
            )

        print("\nVerified Story ID mapping prepared:")
        print(f"Unique articles: {len(results.unique_articles)}")
        print(f"Verified Story IDs: {len(story_ids_by_article_id)}")

        # -----------------------------------------------------
        # 2. Build Article ID -> SQL staging_record_id mapping
        #
        # normalized_staging_ids maps:
        #     id(Article object) -> staging_record_id
        #
        # Deduplication preserves the original Article objects,
        # so their object identities remain valid here.
        # -----------------------------------------------------

        staging_record_ids_by_article_id = {}
        seen_staging_ids = set()
        missing_staging_records = []

        for article in results.unique_articles:
            article_id = getattr(article, "article_id", None)

            staging_id = results.normalized_staging_ids.get(
                id(article)
            )

            if not article_id or staging_id is None:
                missing_staging_records.append(
                    {
                        "article_id": article_id,
                        "staging_record_id": staging_id,
                        "title": article.title[:80],
                    }
                )
                continue

            if (
                not isinstance(staging_id, int)
                or isinstance(staging_id, bool)
                or staging_id <= 0
            ):
                raise RuntimeError(
                    "Invalid staging_record_id for "
                    f"article_id={article_id!r}: {staging_id!r}."
                )

            if article_id in staging_record_ids_by_article_id:
                raise RuntimeError(
                    "Duplicate article_id detected while "
                    "building the staging mapping: "
                    f"{article_id}"
                )

            if staging_id in seen_staging_ids:
                raise RuntimeError(
                    "Duplicate staging_record_id detected "
                    "while building the DWH mapping: "
                    f"{staging_id}"
                )

            staging_record_ids_by_article_id[
                article_id
            ] = staging_id

            seen_staging_ids.add(staging_id)

        # -----------------------------------------------------
        # 3. Validate that every unique article has exactly
        #    one SQL staging record.
        # -----------------------------------------------------

        if missing_staging_records:
            raise RuntimeError(
                "Cannot load DWH because SQL staging records "
                "are missing for "
                f"{len(missing_staging_records)} unique articles: "
                f"{missing_staging_records}"
            )

        if (
            len(staging_record_ids_by_article_id)
            != len(results.unique_articles)
        ):
            raise RuntimeError(
                "Staging record mapping count does not match "
                "the number of unique articles."
            )

        print("\nSQL staging mapping prepared:")
        print(f"Unique articles: {len(results.unique_articles)}")
        print(
            "Staging records mapped: "
            f"{len(staging_record_ids_by_article_id)}"
        )

        # -----------------------------------------------------
        # 4. Load the complete DWH batch.
        #
        # Both mappings are required:
        #     article_id -> verified story_id
        #     article_id -> staging_record_id
        # -----------------------------------------------------

        summary = load_articles_to_dwh(
            articles=results.unique_articles,
            story_ids_by_article_id=story_ids_by_article_id,
            staging_record_ids_by_article_id=(
                staging_record_ids_by_article_id
            ),
        )

        # -----------------------------------------------------
        # 5. DWH result tracking
        # -----------------------------------------------------

        results.dwh_articles_loaded = summary[
            "articles_loaded_to_dim_article"
        ]

        results.dwh_articles_failed = 0

        print("\nDWH loading completed successfully.")

        print(
            f"Articles received: "
            f"{summary['articles_received']}"
        )

        print(
            f"dim_article rows processed: "
            f"{summary['articles_loaded_to_dim_article']}"
        )

        print(
            f"dim_story rows processed: "
            f"{summary['stories_loaded_to_dim_story']}"
        )

        print(
            f"Categories available: "
            f"{summary['categories_available']}"
        )

        print(
            f"Authors available: "
            f"{summary['authors_available']}"
        )

        print(
            f"fact_news_articles rows loaded: "
            f"{summary['facts_loaded']}"
        )

    except Exception as exc:
        results.dwh_articles_failed = (
            len(results.unique_articles)
        )

        record_database_error(
            results,
            "DWH star schema loading failed",
            exc,
        )

        print("\nDWH LOADING FAILED")

        print(
            f"Articles submitted: "
            f"{len(results.unique_articles)}"
        )

        print(
            f"Articles loaded: "
            f"{results.dwh_articles_loaded}"
        )

        print(
            f"Articles failed: "
            f"{results.dwh_articles_failed}"
        )

        print(f"Reason: {exc}")
