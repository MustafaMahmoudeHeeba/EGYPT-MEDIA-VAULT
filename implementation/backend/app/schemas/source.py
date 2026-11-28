from datetime import date, datetime
from decimal import Decimal

from app.schemas.common import APIResponse


class SourceResponse(APIResponse):
    # Basic Source Information
    source_id: str
    source_key: int
    source_name: str

    is_enabled: bool | None = None
    is_current_version: bool | None = None
    version_effective_from: datetime | None = None
    version_count: int | None = None

    # Source Activity Summary
    total_articles: int | None = None
    share_of_total_articles_pct: Decimal | None = None
    activity_rank: int | None = None

    articles_with_publication_time: int | None = None
    distinct_categories: int | None = None

    stories_covered: int | None = None
    stories_shared_with_other_sources: int | None = None
    stories_exclusive: int | None = None

    first_published_at: datetime | None = None
    last_published_at: datetime | None = None
    last_ingested_at: datetime | None = None

    # Source Collection Reliability
    collection_runs: int | None = None
    successful_collections: int | None = None
    failed_collections: int | None = None
    success_rate_pct: Decimal | None = None

    total_attempts: int | None = None
    avg_attempts_per_collection: Decimal | None = None
    retried_collections: int | None = None

    total_articles_collected: int | None = None
    avg_articles_collected_per_run: Decimal | None = None
    total_articles_rejected: int | None = None
    total_duplicate_records: int | None = None

    last_successful_run_date: date | None = None
    last_failed_run_date: date | None = None
    failures_by_step: str | None = None