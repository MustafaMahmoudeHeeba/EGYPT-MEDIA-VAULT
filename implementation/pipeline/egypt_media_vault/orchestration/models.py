"""
Shared pipeline state.

PipelineResults is the single object passed explicitly between stages.
Several maps inside it are keyed by id(obj); they are only valid inside one
process and must never be copied, serialized or rebuilt between stages.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourceStats:
    scraped: int = 0
    valid: int = 0
    rejected: int = 0
    normalized: int = 0
    normalization_failed: int = 0
    duplicates: int = 0
    unique: int = 0
    errors: list[str] = field(default_factory=list)

    # Scraper-call tracking used by the operational fact tables.
    # attempt_count: how many times the scraper was invoked in this run.
    # scrape_succeeded: True = scraper returned (even zero articles),
    #                   False = scraper raised, None = not completed.
    # scrape_error: scraper exception text when scrape_succeeded is False.
    attempt_count: int = 0
    scrape_succeeded: bool | None = None
    scrape_error: str | None = None


@dataclass
class PipelineResults:
    raw_articles: list = field(default_factory=list)
    valid_raw_articles: list = field(default_factory=list)
    normalized_articles: list = field(default_factory=list)
    unique_articles: list = field(default_factory=list)
    duplicate_articles: list = field(default_factory=list)
    clusters: list = field(default_factory=list)

    validation_issues: list = field(default_factory=list)
    normalization_errors: list = field(default_factory=list)
    source_errors: list = field(default_factory=list)
    storage_errors: list = field(default_factory=list)
    database_errors: list = field(default_factory=list)

    source_stats: dict = field(default_factory=dict)

    # Original RawArticle identity -> SQL staging_record_id.
    staging_record_ids: dict = field(default_factory=dict)

    # Normalized Article identity -> SQL staging_record_id.
    normalized_staging_ids: dict = field(default_factory=dict)

    # Duplicate Article identity -> matching unique Article.
    duplicate_matches: dict = field(default_factory=dict)

    # Story ID persistence tracking.
    story_ids_persisted: int = 0
    story_ids_not_persisted: int = 0

    # Expected Story IDs keyed by staging_record_id.
    expected_story_ids: dict = field(default_factory=dict)

    # Actual SQL read-back verification tracking.
    story_ids_verified: int = 0
    story_ids_verification_failed: int = 0

    # DWH loading tracking.
    dwh_articles_loaded: int = 0
    dwh_articles_failed: int = 0

    run_id: str | None = None
    bronze_file: str | None = None
    silver_file: str | None = None

    # Operational fact tracking (plain, serializable values only).
    # started_at / finished_at are timezone-aware UTC datetimes.
    started_at: datetime | None = None
    finished_at: datetime | None = None

    # Source names the scraping stage was asked to run, in order.
    configured_sources: list = field(default_factory=list)

    # Exception text when the run ended through an uncaught exception.
    run_error: str | None = None


def get_source_stats(results, source):
    if source not in results.source_stats:
        results.source_stats[source] = SourceStats()

    return results.source_stats[source]
