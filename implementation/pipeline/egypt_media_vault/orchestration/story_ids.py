"""
STEP 5.1: Story ID persistence to SQL staging, SQL read-back verification,
and re-attachment of verified Story IDs to the unique Article objects.
"""

from pipeline.egypt_media_vault.warehouse.article_repository import (
    get_story_ids_by_staging_ids,
)

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults
from pipeline.egypt_media_vault.orchestration.staging import record_database_error, update_staging_record


def save_story_ids(results: PipelineResults) -> None:
    """
    Persist and verify Story IDs for every normalized article.

    Each normalized article must map to exactly one unique SQL
    staging record. Duplicate news articles inherit the Story ID
    of their unique representative, but retain their own staging IDs.

    After successful SQL read-back verification, the verified
    Story ID is assigned to the Article object using both:

        1. staging-record identity during persistence
        2. article_id as the stable business-key mapping

    The second mapping guarantees that the Article objects later
    consumed by DWH loading contain the verified Story ID even
    if the deduplication layer returns equivalent Article objects
    through a different object reference.
    """

    print_section("SQL STAGING: STORY ID PERSISTENCE")

    results.expected_story_ids.clear()
    results.story_ids_persisted = 0
    results.story_ids_not_persisted = 0
    results.story_ids_verified = 0
    results.story_ids_verification_failed = 0

    expected_story_ids = {}
    seen_staging_ids = {}

    # -----------------------------------------------------
    # Stable Article ID -> staging ID mapping.
    #
    # This mapping is intentionally based on article_id,
    # not Python object identity.
    # -----------------------------------------------------

    article_id_to_staging_id = {}

    # -----------------------------------------------------
    # 1. Resolve and validate every article mapping
    # -----------------------------------------------------

    for article in results.normalized_articles:

        article_object_id = id(article)

        if article_object_id in results.duplicate_matches:
            representative = (
                results.duplicate_matches[
                    article_object_id
                ]
            )

            story_id = (
                representative.story_cluster_id
            )

        else:
            story_id = article.story_cluster_id

        staging_id = (
            results.normalized_staging_ids.get(
                article_object_id
            )
        )

        if not story_id or staging_id is None:
            results.story_ids_not_persisted += 1

            print(
                f"[MISSING] Story ID or staging ID: "
                f"{article.title[:80]}"
            )

            continue

        if staging_id in seen_staging_ids:
            previous_article = (
                seen_staging_ids[staging_id]
            )

            results.story_ids_not_persisted += 1

            record_database_error(
                results,
                "Duplicate staging ID mapping",
                ValueError(
                    f"Staging ID {staging_id} is assigned "
                    f"to multiple normalized articles: "
                    f"'{previous_article.title[:60]}' "
                    f"and "
                    f"'{article.title[:60]}'."
                ),
            )

            continue

        # article_id should already have been generated
        # by the deduplication stage.
        if not article.article_id:
            results.story_ids_not_persisted += 1

            print(
                f"[MISSING] Article ID: "
                f"{article.title[:80]}"
            )

            continue

        if article.article_id in article_id_to_staging_id:
            previous_staging_id = (
                article_id_to_staging_id[
                    article.article_id
                ]
            )

            results.story_ids_not_persisted += 1

            record_database_error(
                results,
                "Duplicate article ID mapping",
                ValueError(
                    f"Article ID {article.article_id} "
                    f"is mapped to multiple staging records: "
                    f"{previous_staging_id} and {staging_id}."
                ),
            )

            continue

        seen_staging_ids[staging_id] = article

        expected_story_ids[staging_id] = story_id

        article_id_to_staging_id[
            article.article_id
        ] = staging_id

    results.expected_story_ids.update(
        expected_story_ids
    )

    print(
        f"\nNormalized articles: "
        f"{len(results.normalized_articles)}"
    )

    print(
        f"Valid staging mappings: "
        f"{len(expected_story_ids)}"
    )

    print(
        f"Missing or duplicate mappings: "
        f"{results.story_ids_not_persisted}"
    )

    # -----------------------------------------------------
    # 2. Persist Story IDs
    # -----------------------------------------------------

    for staging_id, story_id in (
        expected_story_ids.items()
    ):

        success = update_staging_record(
            results,
            staging_id,
            "Story ID persistence failed",
            story_id=story_id,
        )

        if success:
            results.story_ids_persisted += 1

        else:
            results.story_ids_not_persisted += 1

    print("\nStory ID Persistence Summary:")

    print(
        f"Successful updates: "
        f"{results.story_ids_persisted}"
    )

    print(
        f"Failed updates: "
        f"{results.story_ids_not_persisted}"
    )

    # -----------------------------------------------------
    # 3. Read back persisted values from SQL
    # -----------------------------------------------------

    if not expected_story_ids:
        print(
            "\nNo expected Story IDs available "
            "for verification."
        )
        return

    print(
        "\nReading persisted Story IDs from SQL..."
    )

    try:
        actual_story_ids = (
            get_story_ids_by_staging_ids(
                expected_story_ids.keys()
            )
        )

    except Exception as exc:
        record_database_error(
            results,
            "Story ID read-back verification failed",
            exc,
        )

        results.story_ids_verification_failed = (
            len(expected_story_ids)
        )

        return

    # -----------------------------------------------------
    # 4. Verify actual values against SQL
    # -----------------------------------------------------

    # Stable mapping:
    #
    #     article_id -> verified story_id
    #
    # This is the critical mapping used to make sure
    # results.unique_articles receives the verified value.
    # -----------------------------------------------------

    verified_story_ids_by_article_id = {}

    for (
        staging_id,
        expected_story_id,
    ) in expected_story_ids.items():

        actual_story_id = actual_story_ids.get(
            staging_id
        )

        if actual_story_id == expected_story_id:

            article = seen_staging_ids.get(
                staging_id
            )

            if article is None:
                results.story_ids_verification_failed += 1

                print(
                    f"[MISMATCH] Staging ID {staging_id} | "
                    f"Story ID verified in SQL but the "
                    f"corresponding Article object was not found."
                )

                continue

            # ---------------------------------------------
            # First assignment:
            # assign to the object associated with the
            # staging record.
            # ---------------------------------------------

            article.story_id = actual_story_id

            # ---------------------------------------------
            # Second assignment:
            # create a stable business-key mapping.
            # ---------------------------------------------

            if article.article_id:
                verified_story_ids_by_article_id[
                    article.article_id
                ] = actual_story_id

            results.story_ids_verified += 1

            print(
                f"[VERIFIED] Staging ID {staging_id} | "
                f"Story ID: {actual_story_id}"
            )

        else:
            results.story_ids_verification_failed += 1

            actual_description = (
                "RECORD NOT FOUND"
                if staging_id not in actual_story_ids
                else repr(actual_story_id)
            )

            print(
                f"[MISMATCH] Staging ID {staging_id} | "
                f"Expected: {expected_story_id} | "
                f"Actual: {actual_description}"
            )

    # -----------------------------------------------------
    # 5. Re-attach verified Story IDs to the actual
    #    unique_articles collection consumed by DWH.
    #
    # This intentionally uses article_id instead of id(article).
    # -----------------------------------------------------

    unique_articles_story_ids_attached = 0
    unique_articles_story_ids_missing = []

    for article in results.unique_articles:

        article_id = getattr(
            article,
            "article_id",
            None,
        )

        verified_story_id = (
            verified_story_ids_by_article_id.get(
                article_id
            )
        )

        if verified_story_id:
            article.story_id = verified_story_id

            unique_articles_story_ids_attached += 1

        else:
            unique_articles_story_ids_missing.append(
                {
                    "article_id": article_id,
                    "title": article.title,
                }
            )

    print(
        "\nVerified Story ID attachment to "
        "unique Article objects:"
    )

    print(
        f"Unique articles: "
        f"{len(results.unique_articles)}"
    )

    print(
        f"Story IDs attached: "
        f"{unique_articles_story_ids_attached}"
    )

    print(
        f"Story IDs missing: "
        f"{len(unique_articles_story_ids_missing)}"
    )

    if unique_articles_story_ids_missing:
        for missing in (
            unique_articles_story_ids_missing
        ):
            print(
                f"  [MISSING] "
                f"article_id={missing['article_id']} | "
                f"title={missing['title'][:80]}"
            )

    # -----------------------------------------------------
    # 6. Final verification summary
    # -----------------------------------------------------

    print(
        "\nStory ID Read-Back Verification Summary:"
    )

    print(
        f"Expected records: "
        f"{len(expected_story_ids)}"
    )

    print(
        f"Verified records: "
        f"{results.story_ids_verified}"
    )

    print(
        f"Verification failures: "
        f"{results.story_ids_verification_failed}"
    )
