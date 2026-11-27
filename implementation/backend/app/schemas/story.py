from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import APIResponse


class StoryResponse(APIResponse):
    story_id: str | None
    story_key: int
    story_title: str | None
    article_count: int | None
    source_count: int | None
    is_multi_source: bool | None
    publisher_ids: str | None
    publisher_names: str | None
    first_published_at: datetime | None
    last_published_at: datetime | None
    coverage_gap_minutes: Decimal | None
    first_source_id: str | None
    first_source_name: str | None
    articles_missing_publication_time: int | None
    coverage_rank: int | None


class StoryTimelineResponse(APIResponse):
    story_id: str | None
    story_key: int
    story_title: str | None
    source_id: str | None
    source_name: str | None
    story_source_count: int | None
    article_count: int | None
    articles_missing_publication_time: int | None
    first_published_at: datetime | None
    last_published_at: datetime | None
    story_first_published_at: datetime | None
    minutes_after_story_first_publication: Decimal | None
    publication_order: int | None
    is_first_source: bool | None


class StoryKPIsResponse(APIResponse):
    kpi_scope: str | None
    total_stories: int | None
    multi_source_stories: int | None
    single_source_stories: int | None
    multi_source_story_pct: Decimal | None
    avg_publishers_per_story: Decimal | None
    max_publishers_per_story: int | None
    total_articles_in_stories: int | None
    avg_articles_per_story: Decimal | None
    avg_coverage_gap_minutes_multi_source: Decimal | None
    stories_without_articles: int | None
    unknown_sentinel_stories: int | None
    stories_in_dimension: int | None
    generated_at_utc: datetime | None
