from datetime import date
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.story_repository import (
    get_stories,
    get_story_by_id,
    get_story_timeline,
    get_story_kpis,
)


ALLOWED_SORT_COLUMNS = {
    "story_title",
    "article_count",
    "source_count",
    "first_published_at",
    "last_published_at",
    "coverage_gap_minutes",
    "coverage_rank",
}


def list_stories(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    multi_source_only: bool = False,
    min_sources: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "last_published_at",
    sort_order: str = "desc",
) -> dict[str, Any]:

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

    if min_sources is not None and min_sources < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_sources must be greater than or equal to 1.",
        )

    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "sort_by must be one of: "
                f"{', '.join(sorted(ALLOWED_SORT_COLUMNS))}."
            ),
        )

    if sort_order.lower() not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="sort_order must be 'asc' or 'desc'.",
        )

    return get_stories(
        db,
        page=page,
        page_size=page_size,
        search=search,
        multi_source_only=multi_source_only,
        min_sources=min_sources,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def retrieve_story(
    db: Session,
    story_id: str,
) -> dict[str, Any]:

    story = get_story_by_id(db, story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found.",
        )

    return story


def retrieve_story_timeline(
    db: Session,
    story_id: str,
) -> list[dict[str, Any]]:

    # Verify that the requested story exists before retrieving its timeline.
    retrieve_story(db, story_id)

    return get_story_timeline(db, story_id)


def retrieve_story_kpis(
    db: Session,
) -> dict[str, Any]:

    kpis = get_story_kpis(db)

    if kpis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story KPIs are not available.",
        )

    return kpis
