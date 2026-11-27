from decimal import Decimal

from pydantic import Field

from app.schemas.common import APIResponse


class CategorySourceBreakdown(APIResponse):
    source_id: str
    source_name: str

    article_count: int | None = None

    share_of_source_pct: Decimal | None = None
    source_share_of_category_pct: Decimal | None = None


class CategoryResponse(APIResponse):
    category_key: int
    category_name: str

    total_articles: int = 0
    source_count: int = 0
    activity_rank: int | None = None

    sources: list[CategorySourceBreakdown] = Field(
        default_factory=list
    )