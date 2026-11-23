"""
STEPS 2-5: validation, normalization, deduplication and story clustering stages.
"""

from datetime import datetime, timezone

from pipeline.egypt_media_vault.config.settings import settings

from pipeline.egypt_media_vault.domain.validation_issue import (
    ValidationIssue,
)

from pipeline.egypt_media_vault.processing.article_validator import (
    ArticleValidator,
)
from pipeline.egypt_media_vault.processing.article_normalizer import (
    ArticleNormalizer,
)
from pipeline.egypt_media_vault.processing.article_deduplicator import (
    ArticleDeduplicator,
)
from pipeline.egypt_media_vault.processing.story_clusterer import (
    StoryClusterer,
)

from pipeline.egypt_media_vault.orchestration.display import print_issue, print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults, get_source_stats
from pipeline.egypt_media_vault.orchestration.staging import (
    save_deduplication_results,
    save_normalization_result,
    save_validation_results,
    update_staging_record,
)


def run_validation(results: PipelineResults) -> None:
    print_section("STEP 2: VALIDATION")

    validator = ArticleValidator()

    for index, raw_article in enumerate(
        results.raw_articles,
        start=1,
    ):
        source = raw_article.source
        stats = get_source_stats(results, source)

        print(
            f"\n[{index}/{len(results.raw_articles)}] "
            f"{source}: {raw_article.title[:90]}"
        )

        try:
            issues = validator.validate(raw_article)

            results.validation_issues.extend(issues)

            is_valid = validator.is_valid(issues)

            persistence_success = save_validation_results(
                results,
                raw_article,
                issues,
                is_valid,
            )

            if is_valid:
                results.valid_raw_articles.append(raw_article)
                stats.valid += 1

                print("  VALID")

            else:
                stats.rejected += 1

                print("  REJECTED")

                for issue in issues:
                    print_issue(issue)

            if not persistence_success:
                print(
                    "  WARNING: Validation result was not fully saved to SQL."
                )

        except Exception as exc:
            stats.rejected += 1

            error_message = (
                f"{source} | {raw_article.url} | {exc}"
            )

            results.validation_issues.append(
                ValidationIssue(
                    field_name="validation",
                    issue_type="validation_exception",
                    message=str(exc),
                    severity="critical",
                    article_url=raw_article.url,
                    detected_at=datetime.now(timezone.utc),
                )
            )

            save_validation_results(
                results,
                raw_article,
                [results.validation_issues[-1]],
                False,
            )

            print(f"  VALIDATION ERROR: {error_message}")

    print("\nValidation Summary:")
    print(f"Articles checked: {len(results.raw_articles)}")
    print(f"Valid articles: {len(results.valid_raw_articles)}")

    rejected = (
        len(results.raw_articles)
        - len(results.valid_raw_articles)
    )

    print(f"Rejected articles: {rejected}")
    print(f"Total validation issues: {len(results.validation_issues)}")


def run_normalization(results: PipelineResults) -> None:
    print_section("STEP 3: NORMALIZATION")

    normalizer = ArticleNormalizer()

    for index, raw_article in enumerate(
        results.valid_raw_articles,
        start=1,
    ):
        stats = get_source_stats(
            results,
            raw_article.source,
        )

        try:
            article = normalizer.normalize(raw_article)

            results.normalized_articles.append(article)

            stats.normalized += 1

            save_normalization_result(
                results,
                raw_article,
                article,
            )

            print(
                f"[{index}] NORMALIZED: "
                f"{article.source} | "
                f"{article.title[:75]}"
            )

        except Exception as exc:
            stats.normalization_failed += 1

            error = {
                "source": raw_article.source,
                "url": raw_article.url,
                "error": str(exc),
            }

            results.normalization_errors.append(error)

            staging_id = results.staging_record_ids.get(
                id(raw_article)
            )

            update_staging_record(
                results,
                staging_id,
                "Normalization failure status update failed",
                processing_status="Failed",
            )

            print(
                f"[{index}] NORMALIZATION FAILED: "
                f"{raw_article.source}"
            )

            print(f"Reason: {exc}")

    print("\nNormalization Summary:")
    print(f"Input articles: {len(results.valid_raw_articles)}")
    print(
        f"Successfully normalized: "
        f"{len(results.normalized_articles)}"
    )
    print(
        f"Normalization failures: "
        f"{len(results.normalization_errors)}"
    )


def run_deduplication(results: PipelineResults) -> None:
    print_section("STEP 4: DEDUPLICATION")

    deduplicator = ArticleDeduplicator()

    (
        results.unique_articles,
        results.duplicate_articles,
    ) = deduplicator.deduplicate(
        results.normalized_articles
    )

    results.duplicate_matches = (
        deduplicator.duplicate_matches
    )

    unique_ids = {
        id(article)
        for article in results.unique_articles
    }

    duplicate_ids = {
        id(article)
        for article in results.duplicate_articles
    }

    for article in results.normalized_articles:
        stats = get_source_stats(
            results,
            article.source,
        )

        if id(article) in unique_ids:
            stats.unique += 1

        elif id(article) in duplicate_ids:
            stats.duplicates += 1

    save_deduplication_results(results)

    print(
        f"Before deduplication: "
        f"{len(results.normalized_articles)}"
    )
    print(
        f"Unique articles: "
        f"{len(results.unique_articles)}"
    )
    print(
        f"Duplicate articles: "
        f"{len(results.duplicate_articles)}"
    )

    print("\nDuplicate Details:")

    for article in results.duplicate_articles:
        print(
            f"- {article.source}: "
            f"{article.title[:100]}"
        )

    accounting_valid = (
        len(results.unique_articles)
        + len(results.duplicate_articles)
        == len(results.normalized_articles)
    )

    print(
        f"\nDeduplication accounting valid: "
        f"{accounting_valid}"
    )


def run_story_clustering(results: PipelineResults) -> None:
    print_section("STEP 5: STORY CLUSTERING")

    if not results.unique_articles:
        print(
            "No unique articles available for clustering."
        )
        return

    threshold = settings.story_similarity_threshold

    print(
        f"Configured similarity threshold: "
        f"{threshold}"
    )

    clusterer = StoryClusterer(
        similarity_threshold=threshold
    )

    results.clusters = clusterer.cluster(
        results.unique_articles
    )

    print(
        f"\nArticles submitted: "
        f"{len(results.unique_articles)}"
    )
    print(
        f"Clusters created: "
        f"{len(results.clusters)}"
    )
