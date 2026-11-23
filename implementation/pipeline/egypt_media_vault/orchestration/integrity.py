"""
STEP 8: final integrity checks (plus the clusterer_id helper shared with reporting).
"""

import hashlib

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults


def clusterer_id(article):
    if article.canonical_url_hash:
        return article.canonical_url_hash

    return hashlib.sha256(
        article.effective_canonical_url.encode(
            "utf-8"
        )
    ).hexdigest()


def run_integrity_checks(
    results: PipelineResults,
) -> dict:
    print_section("STEP 8: FINAL INTEGRITY CHECKS")

    checks = {}

    # -----------------------------------------------------
    # 1. Deduplication accounting
    # -----------------------------------------------------

    checks["Deduplication accounting"] = (
        len(results.unique_articles)
        + len(results.duplicate_articles)
        == len(results.normalized_articles)
    )

    # -----------------------------------------------------
    # 2. Unique articles have Story IDs
    # -----------------------------------------------------

    checks["All unique articles assigned"] = all(
        article.story_cluster_id
        for article in results.unique_articles
    )

    # -----------------------------------------------------
    # 3. Story ID update operations
    # -----------------------------------------------------

    checks[
        "All normalized article Story IDs persisted"
    ] = (
        results.story_ids_persisted
        == len(results.normalized_articles)
        and results.story_ids_not_persisted == 0
    )

    # -----------------------------------------------------
    # 4. Actual SQL Story ID read-back verification
    # -----------------------------------------------------

    checks[
        "All persisted Story IDs match expected values"
    ] = (
        len(results.expected_story_ids)
        == len(results.normalized_articles)
        and results.story_ids_verified
        == len(results.expected_story_ids)
        and results.story_ids_verification_failed == 0
    )

    # -----------------------------------------------------
    # 5. Duplicate-to-representative relationships
    # -----------------------------------------------------

    expected_duplicate_ids = {
        id(article)
        for article in results.duplicate_articles
    }

    actual_duplicate_ids = set(
        results.duplicate_matches.keys()
    )

    duplicate_mapping_complete = (
        expected_duplicate_ids
        == actual_duplicate_ids
    )

    unique_object_ids = {
        id(article)
        for article in results.unique_articles
    }

    duplicate_representatives_valid = all(
        id(representative) in unique_object_ids
        and bool(representative.story_cluster_id)
        for representative
        in results.duplicate_matches.values()
    )

    checks[
        "Duplicate mappings are complete"
    ] = duplicate_mapping_complete

    checks[
        "Duplicate representatives have valid Story IDs"
    ] = duplicate_representatives_valid

    # -----------------------------------------------------
    # 6. Cluster IDs must be unique
    # -----------------------------------------------------

    cluster_ids = [
        cluster.cluster_id
        for cluster in results.clusters
    ]

    checks["Cluster IDs unique"] = (
        len(cluster_ids)
        == len(set(cluster_ids))
    )

    # -----------------------------------------------------
    # 7. All cluster article IDs must exist
    # -----------------------------------------------------

    known_article_ids = {
        clusterer_id(article)
        for article in results.unique_articles
    }

    cluster_article_ids = [
        article_id
        for cluster in results.clusters
        for article_id in cluster.articles
    ]

    checks[
        "All cluster article IDs exist"
    ] = all(
        article_id in known_article_ids
        for article_id in cluster_article_ids
    )

    # -----------------------------------------------------
    # 8. No article appears in multiple clusters
    # -----------------------------------------------------

    checks[
        "No article appears in multiple clusters"
    ] = (
        len(cluster_article_ids)
        == len(set(cluster_article_ids))
    )

    # -----------------------------------------------------
    # 9. All unique articles must be accounted for
    # -----------------------------------------------------

    checks[
        "All unique articles accounted for"
    ] = (
        len(cluster_article_ids)
        == len(results.unique_articles)
        and set(cluster_article_ids)
        == known_article_ids
    )

    # -----------------------------------------------------
    # 10. Article Story IDs must match cluster membership
    # -----------------------------------------------------

    article_cluster_lookup = {
        clusterer_id(article):
            article.story_cluster_id
        for article in results.unique_articles
    }

    membership_matches = True

    for cluster in results.clusters:
        for article_id in cluster.articles:
            if (
                article_cluster_lookup.get(
                    article_id
                )
                != cluster.cluster_id
            ):
                membership_matches = False

    checks[
        "Article cluster IDs match membership"
    ] = membership_matches

    # -----------------------------------------------------
    # 11. DWH loading
    # -----------------------------------------------------

    checks[
        "All unique articles loaded into DWH"
    ] = (
        results.dwh_articles_loaded
        == len(results.unique_articles)
        and results.dwh_articles_failed == 0
    )

    # -----------------------------------------------------
    # Print results
    # -----------------------------------------------------

    for check_name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(
            f"[{status}] {check_name}"
        )

    return checks
