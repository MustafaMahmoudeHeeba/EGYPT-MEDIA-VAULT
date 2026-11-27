from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.analytics_repository import (
    get_analytics_overview,
    get_pipeline_status_summary,
    get_pipeline_runs,
    get_source_daily_activity,
    get_source_reliability,
    get_category_daily_activity,
    get_time_activity,
)


def retrieve_analytics_overview(db: Session):
    result = get_analytics_overview(db)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analytics overview is not available.",
        )

    return result


def retrieve_pipeline_status_summary(db: Session):
    return get_pipeline_status_summary(db)


def list_pipeline_runs(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    run_status: str | None = None,
):
    if page < 1 or not 1 <= page_size <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid pagination parameters.",
        )

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be later than date_to.",
        )

    return get_pipeline_runs(
        db,
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        run_status=run_status,
    )


def list_source_daily_activity(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    source_id: str | None = None,
):
    _validate_date_range(date_from, date_to)
    return get_source_daily_activity(
        db,
        date_from=date_from,
        date_to=date_to,
        source_id=source_id,
    )


def list_source_reliability(db: Session):
    return get_source_reliability(db)


def list_category_daily_activity(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    source_id: str | None = None,
    category_key: int | None = None,
):
    _validate_date_range(date_from, date_to)

    if category_key is not None and category_key < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="category_key must be greater than or equal to 1.",
        )

    return get_category_daily_activity(
        db,
        date_from=date_from,
        date_to=date_to,
        source_id=source_id,
        category_key=category_key,
    )


def list_time_activity(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    source_id: str | None = None,
):
    _validate_date_range(date_from, date_to)
    return get_time_activity(
        db,
        date_from=date_from,
        date_to=date_to,
        source_id=source_id,
    )


def _validate_date_range(
    date_from: date | None,
    date_to: date | None,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be later than date_to.",
        )
