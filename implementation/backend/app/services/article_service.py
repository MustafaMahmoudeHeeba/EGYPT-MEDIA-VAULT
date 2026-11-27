
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.article_repository import (
    get_article_by_id,
    get_articles,
)


def list_articles(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    source_id: str | None = None,
    category_name: str | None = None,
    story_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "publication_timestamp",
    sort_order: str = "desc",
) -> dict:
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page must be greater than or equal to 1.",
        )

    if not 1 <= page_size <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page size must be between 1 and 100.",
        )

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be later than date_to.",
        )

    allowed_sort_columns = {
        "publication_timestamp",
        "ingestion_timestamp",
        "article_title",
    }

    if sort_by not in allowed_sort_columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"sort_by must be one of: {', '.join(sorted(allowed_sort_columns))}.",
        )

    if sort_order.lower() not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="sort_order must be 'asc' or 'desc'.",
        )

    return get_articles(
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


def retrieve_article(
    db: Session,
    article_id: str,
) -> dict:
    article = get_article_by_id(db, article_id)

    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    return article
