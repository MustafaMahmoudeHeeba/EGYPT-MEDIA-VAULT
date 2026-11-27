from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.article import (
    ArticleDetail,
    ArticleListItem,
)
from app.schemas.common import PaginatedResponse
from app.services.article_service import (
    list_articles,
    retrieve_article,
)


router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


@router.get(
    "",
    response_model=PaginatedResponse[ArticleListItem],
    summary="List news articles",
)
def get_articles_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=300),
    source_id: str | None = Query(default=None),
    category_name: str | None = Query(default=None),
    story_id: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    sort_by: str = Query(default="publication_timestamp"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
):
    return list_articles(
        db,
        page=page,
        page_size=page_size,
        search=search,
        source_id=source_id,
        category_name=category_name,
        story_id=story_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{article_id}",
    response_model=ArticleDetail,
    summary="Get article details",
)
def get_article_endpoint(
    article_id: str,
    db: Session = Depends(get_db),
):
    return retrieve_article(db, article_id)