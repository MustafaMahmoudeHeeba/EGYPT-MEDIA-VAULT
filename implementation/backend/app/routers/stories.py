from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.story import (
    StoryResponse,
    StoryTimelineResponse,
    StoryKPIsResponse,
)
from app.services.story_service import (
    list_stories,
    retrieve_story,
    retrieve_story_timeline,
    retrieve_story_kpis,
)


router = APIRouter(
    prefix="/stories",
    tags=["Stories"],
)


@router.get(
    "",
    response_model=PaginatedResponse[StoryResponse],
    summary="List stories",
)
def read_stories(
    db: Session = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    multi_source_only: bool = False,
    min_sources: Annotated[int | None, Query(ge=1)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "last_published_at",
    sort_order: str = "desc",
):
    return list_stories(
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


@router.get(
    "/kpis",
    response_model=StoryKPIsResponse,
    summary="Get story coverage KPIs",
)
def read_story_kpis(
    db: Session = Depends(get_db),
):
    return retrieve_story_kpis(db)


@router.get(
    "/{story_id}",
    response_model=StoryResponse,
    summary="Get story details",
)
def read_story(
    story_id: str,
    db: Session = Depends(get_db),
):
    return retrieve_story(db, story_id)


@router.get(
    "/{story_id}/timeline",
    response_model=list[StoryTimelineResponse],
    summary="Get story publication timeline",
)
def read_story_timeline(
    story_id: str,
    db: Session = Depends(get_db),
):
    return retrieve_story_timeline(db, story_id)
