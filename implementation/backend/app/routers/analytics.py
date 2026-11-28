from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.kpi import (
    AnalyticsOverview,
    PipelineStatusSummary,
    PipelineRunItem,
    SourceDailyActivity,
    SourceReliability,
    CategoryDailyActivity,
    TimeActivityItem,
)
from app.services.analytics_service import (
    retrieve_analytics_overview,
    retrieve_pipeline_status_summary,
    list_pipeline_runs,
    list_source_daily_activity,
    list_source_reliability,
    list_category_daily_activity,
    list_time_activity,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(db: Session = Depends(get_db)):
    return retrieve_analytics_overview(db)


@router.get("/pipeline/status", response_model=list[PipelineStatusSummary])
def get_pipeline_status(db: Session = Depends(get_db)):
    return retrieve_pipeline_status_summary(db)


@router.get("/pipeline/runs", response_model=PaginatedResponse[PipelineRunItem])
def get_pipeline_runs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    run_status: str | None = Query(None, min_length=1),
    db: Session = Depends(get_db),
):
    return list_pipeline_runs(
        db, page=page, page_size=page_size,
        date_from=date_from, date_to=date_to,
        run_status=run_status,
    )


@router.get("/sources/daily", response_model=list[SourceDailyActivity])
def get_source_daily(
    date_from: date | None = None,
    date_to: date | None = None,
    source_id: str | None = None,
    db: Session = Depends(get_db),
):
    return list_source_daily_activity(
        db, date_from=date_from, date_to=date_to, source_id=source_id
    )


@router.get("/sources/reliability", response_model=list[SourceReliability])
def get_source_reliability(db: Session = Depends(get_db)):
    return list_source_reliability(db)


@router.get("/categories/daily", response_model=list[CategoryDailyActivity])
def get_category_daily(
    date_from: date | None = None,
    date_to: date | None = None,
    source_id: str | None = None,
    category_key: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    return list_category_daily_activity(
        db, date_from=date_from, date_to=date_to,
        source_id=source_id, category_key=category_key,
    )


@router.get("/time-activity", response_model=list[TimeActivityItem])
def get_time_activity(
    date_from: date | None = None,
    date_to: date | None = None,
    source_id: str | None = None,
    db: Session = Depends(get_db),
):
    return list_time_activity(
        db, date_from=date_from, date_to=date_to, source_id=source_id
    )

