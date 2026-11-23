"""
STEPS 6, 7, 9 and the final pipeline report (console output only).
"""

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.integrity import clusterer_id
from pipeline.egypt_media_vault.orchestration.models import PipelineResults


def print_cluster_details(
    results: PipelineResults,
) -> None:
    print_section("STEP 6: CLUSTER DETAILS")

    articles_by_id = {
        clusterer_id(article): article
        for article in results.unique_articles
    }

    for index, cluster in enumerate(
        results.clusters,
        start=1,
    ):
        cluster_articles = [
            articles_by_id[article_id]
            for article_id in cluster.articles
            if article_id in articles_by_id
        ]

        sources = sorted({
            article.source
            for article in cluster_articles
        })

        print(f"\nCLUSTER {index}")
        print("-" * 75)
        print(f"ID: {cluster.cluster_id}")
        print(
            f"Representative: "
            f"{cluster.representative_title}"
        )
        print(
            f"Articles: "
            f"{cluster.article_count}"
        )
        print(
            f"Sources ({len(sources)}): "
            f"{', '.join(sources)}"
        )

        for article in cluster_articles:
            print(
                f"  - [{article.source}] "
                f"{article.title}"
            )


def print_story_coverage(
    results: PipelineResults,
) -> None:
    print_section("STEP 7: STORY COVERAGE")

    articles_by_id = {
        clusterer_id(article): article
        for article in results.unique_articles
    }

    for cluster in results.clusters:
        cluster_articles = [
            articles_by_id[article_id]
            for article_id in cluster.articles
            if article_id in articles_by_id
        ]

        sources = {
            article.source
            for article in cluster_articles
        }

        publication_dates = [
            article.publication_date
            for article in cluster_articles
            if article.publication_date is not None
        ]

        earliest_date = (
            min(publication_dates)
            if publication_dates
            else None
        )

        latest_date = (
            max(publication_dates)
            if publication_dates
            else None
        )

        print(
            f"\nStory: "
            f"{cluster.representative_title}"
        )

        print(
            f"Publishing websites: "
            f"{len(sources)}"
        )

        print(
            f"Sources: "
            f"{', '.join(sorted(sources))}"
        )

        print(
            f"Articles: "
            f"{len(cluster_articles)}"
        )

        print(
            f"Earliest publication: "
            f"{earliest_date}"
        )

        print(
            f"Latest publication: "
            f"{latest_date}"
        )


def print_source_summary(
    results: PipelineResults,
) -> None:
    print_section("STEP 9: SOURCE SUMMARY")

    print(
        f"{'SOURCE':<20}"
        f"{'SCRAPED':>10}"
        f"{'VALID':>10}"
        f"{'REJECTED':>11}"
        f"{'NORMALIZED':>13}"
        f"{'UNIQUE':>10}"
        f"{'DUPLICATES':>12}"
    )

    print("-" * 86)

    for source, stats in (
        results.source_stats.items()
    ):
        print(
            f"{source:<20}"
            f"{stats.scraped:>10}"
            f"{stats.valid:>10}"
            f"{stats.rejected:>11}"
            f"{stats.normalized:>13}"
            f"{stats.unique:>10}"
            f"{stats.duplicates:>12}"
        )


def print_final_report(
    results: PipelineResults,
    checks: dict,
) -> bool:
    print_section("FINAL PIPELINE REPORT")

    print(
        f"Pipeline Run ID: "
        f"{results.run_id}"
    )

    print(
        f"Raw articles: "
        f"{len(results.raw_articles)}"
    )

    print(
        f"SQL staging records: "
        f"{len(results.staging_record_ids)}"
    )

    print(
        f"Valid articles: "
        f"{len(results.valid_raw_articles)}"
    )

    print(
        f"Normalized articles: "
        f"{len(results.normalized_articles)}"
    )

    print(
        f"Unique articles: "
        f"{len(results.unique_articles)}"
    )

    print(
        f"Duplicates: "
        f"{len(results.duplicate_articles)}"
    )

    print(
        f"Story clusters: "
        f"{len(results.clusters)}"
    )

    print(
        f"Story IDs persisted: "
        f"{results.story_ids_persisted}"
    )

    print(
        f"Story IDs not persisted: "
        f"{results.story_ids_not_persisted}"
    )

    print(
        f"Story IDs verified: "
        f"{results.story_ids_verified}"
    )

    print(
        f"Story ID verification failures: "
        f"{results.story_ids_verification_failed}"
    )

    print(
        f"DWH articles loaded: "
        f"{results.dwh_articles_loaded}"
    )

    print(
        f"DWH articles failed: "
        f"{results.dwh_articles_failed}"
    )

    print(
        f"Source failures: "
        f"{len(results.source_errors)}"
    )

    print(
        f"Normalization failures: "
        f"{len(results.normalization_errors)}"
    )

    print(
        f"Database failures: "
        f"{len(results.database_errors)}"
    )

    print(
        f"Bronze file: "
        f"{results.bronze_file or 'NOT UPLOADED'}"
    )

    print(
        f"Silver file: "
        f"{results.silver_file or 'NOT UPLOADED'}"
    )

    print(
        f"Storage failures: "
        f"{len(results.storage_errors)}"
    )

    for error in results.database_errors:
        print(f"DATABASE: {error}")

    for error in results.storage_errors:
        print(f"STORAGE: {error}")

    failed_checks = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    if failed_checks:
        print("\nRESULT: FAILED")

        for name in failed_checks:
            print(f"- {name}")

        return False

    if (
        results.database_errors
        or results.storage_errors
    ):
        print(
            "\nRESULT: FAILED - "
            "DATABASE OR STORAGE ERROR"
        )

        return False

    if (
        results.source_errors
        or results.normalization_errors
    ):
        print(
            "\nRESULT: PASSED WITH WARNINGS"
        )

    elif any(
        stats.rejected > 0
        for stats in results.source_stats.values()
    ):
        print(
            "\nRESULT: PASSED WITH "
            "DATA QUALITY REJECTIONS"
        )

    else:
        print("\nRESULT: PASSED")

    print_section(
        "FULL PIPELINE TEST COMPLETED"
    )

    return True
