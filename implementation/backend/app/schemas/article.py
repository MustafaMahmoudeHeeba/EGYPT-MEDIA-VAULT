
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ArticleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    article_key: int
    article_id: str
    article_title: str | None = None
    original_url: str | None = None

    story_id: str | None = None
    story_title: str | None = None
    story_membership_status: str | None = None
    story_article_count: int | None = None
    story_source_count: int | None = None
    is_multi_source_story: bool | None = None

    source_id: str | None = None
    source_name: str | None = None
    category_key: int | None = None
    category_name: str | None = None
    author_name: str | None = None

    publication_timestamp: datetime | None = None
    has_publication_time: bool | None = None
    ingestion_timestamp: datetime
    article_updated_at: datetime | None = None

    has_content: bool | None = None
    has_description: bool | None = None
    has_image: bool | None = None

    article_description: str | None = None
    article_image_url: str | None = None
    link_availability: str | None = None


class ArticleDetail(ArticleListItem):
    author_key: int | None = None
    timestamp_validity: str | None = None
    syndication_indicator: str | None = None
    article_content: str | None = None


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


class ArticleFilters(BaseModel):
    search: str | None = None
    source_id: str | None = None
    category_name: str | None = None
    story_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
