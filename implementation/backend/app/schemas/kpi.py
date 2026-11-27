from datetime import date, datetime
from decimal import Decimal

from app.schemas.common import APIResponse


class AnalyticsOverview(APIResponse):
    total_stories: int = 0
    multi_source_stories: int = 0
    single_source_stories: int = 0
    multi_source_story_pct: Decimal | None = None
    avg_publishers_per_story: Decimal | None = None
    total_articles_in_stories: int = 0
    total_sources: int = 0
    total_articles: int = 0
    successful_pipeline_runs: int = 0
    total_pipeline_runs: int = 0


class PipelineStatusSummary(APIResponse):
    run_status: str
    run_count: int = 0
    share_of_runs_pct: Decimal | None = None
    avg_duration_minutes: Decimal | None = None
    articles_collected_total: int | None = None
    articles_rejected_total: int | None = None
    duplicate_records_total: int | None = None
    first_run_started_at: datetime | None = None
    last_run_started_at: datetime | None = None


class PipelineRunItem(APIResponse):
    run_id: str
    run_date: date | None = None
    run_status: str | None = None
    status_definition: str | None = None
    is_successful_run: bool | None = None
    is_missed: bool | None = None
    missed_reason: str | None = None
    scheduled_timestamp: datetime | None = None
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    duration_seconds: int | None = None
    duration_minutes: Decimal | None = None
    sources_attempted: int | None = None
    sources_succeeded: int | None = None
    sources_failed: int | None = None
    total_collection_attempts: int | None = None
    articles_collected_total: int | None = None
    articles_rejected_total: int | None = None
    duplicate_records_total: int | None = None


class SourceDailyActivity(APIResponse):
    publication_date: date
    source_id: str
    source_name: str
    article_count: int = 0
    story_count: int = 0
    category_count: int = 0
    total_articles_on_date: int = 0
    share_of_date_pct: Decimal | None = None
    activity_rank_on_date: int | None = None
    cumulative_articles: int = 0


class SourceReliability(APIResponse):
    source_id: str
    source_name: str
    collection_runs: int = 0
    successful_collections: int = 0
    failed_collections: int = 0
    success_rate_pct: Decimal | None = None
    total_attempts: int = 0
    avg_attempts_per_collection: Decimal | None = None
    retried_collections: int = 0
    total_articles_collected: int = 0
    avg_articles_collected_per_run: Decimal | None = None
    total_articles_rejected: int = 0
    total_duplicate_records: int = 0
    last_successful_run_date: date | None = None
    last_failed_run_date: date | None = None
    failures_by_step: str | None = None


class CategoryDailyActivity(APIResponse):
    publication_date: date
    category_key: int
    category_name: str
    source_id: str
    source_name: str
    article_count: int = 0
    share_of_source_day_pct: Decimal | None = None


class TimeActivityItem(APIResponse):
    publication_date: date
    publication_hour: int
    source_id: str
    publication_day_name: str | None = None
    publication_iso_day_of_week: int | None = None
    publication_day_period: str | None = None
    publication_is_weekend: bool | int | None = None
    article_count: int = 0
