"""
STEP 1: scraping of all registered sources.
"""

from pipeline.egypt_media_vault.scrapers.source_registry import (
    create_scrapers,
)

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults, get_source_stats


def run_scraping(
    results: PipelineResults,
    scrapers: list | None = None,
) -> None:
    print_section("STEP 1: SCRAPING")

    # The registry is built when the stage runs (it used to be built at
    # import time as the module-level SCRAPERS). Callers may inject their
    # own (source_name, scraper) list; the default is the registry order.
    if scrapers is None:
        scrapers = create_scrapers()

    # Remember which sources were configured for this run so the
    # operational facts can emit one row per configured source.
    results.configured_sources = [
        source_name for source_name, _ in scrapers
    ]

    for source_name, scraper in scrapers:
        stats = get_source_stats(results, source_name)

        print(f"\nSource: {source_name}")
        print("-" * 60)

        stats.attempt_count += 1

        try:
            scraped_articles = scraper.scrape()

            if scraped_articles is None:
                scraped_articles = []

            results.raw_articles.extend(scraped_articles)

            stats.scraped = len(scraped_articles)
            stats.scrape_succeeded = True

            print(
                f"Scraping completed: {stats.scraped} articles"
            )

        except Exception as exc:
            error_message = (
                f"{source_name}: {type(exc).__name__}: {exc}"
            )

            results.source_errors.append(error_message)
            stats.errors.append(error_message)
            stats.scrape_succeeded = False
            stats.scrape_error = error_message

            print("SCRAPING FAILED")
            print(f"Reason: {exc}")

    print("\nScraping Summary:")

    for source_name, stats in results.source_stats.items():
        print(f"{source_name}: {stats.scraped} articles")

    print(f"\nTotal raw articles: {len(results.raw_articles)}")
