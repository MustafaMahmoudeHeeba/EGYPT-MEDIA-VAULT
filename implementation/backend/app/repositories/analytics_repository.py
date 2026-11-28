from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_analytics_overview(db: Session):
    query = text("""
        SELECT
            sk.total_stories,
            sk.multi_source_stories,
            sk.single_source_stories,
            sk.multi_source_story_pct,
            sk.avg_publishers_per_story,
            sk.total_articles_in_stories,
            (SELECT COUNT(*) FROM analytics.mart_source_summary) AS total_sources,
            (SELECT COALESCE(SUM(total_articles), 0)
             FROM analytics.mart_source_summary) AS total_articles,
            (SELECT COALESCE(SUM(run_count), 0)
             FROM analytics.mart_pipeline_status_summary
             WHERE run_status = 'Success') AS successful_pipeline_runs,
            (SELECT COALESCE(SUM(run_count), 0)
             FROM analytics.mart_pipeline_status_summary) AS total_pipeline_runs
        FROM analytics.mart_story_kpis AS sk
        WHERE sk.kpi_scope = 'overall'
    """)
    result = db.execute(query).mappings().first()
    return dict(result) if result else None


def get_pipeline_status_summary(db: Session):
    query = text("""
        SELECT
            run_status,
            run_count,
            share_of_runs_pct,
            avg_duration_minutes,
            articles_collected_total,
            articles_rejected_total,
            duplicate_records_total,
            first_run_started_at,
            last_run_started_at
        FROM analytics.mart_pipeline_status_summary
        ORDER BY run_count DESC, run_status
    """)
    return [dict(row) for row in db.execute(query).mappings().all()]


def get_pipeline_runs(
    db: Session,
    *,
    page: int,
    page_size: int,
    date_from: date | None,
    date_to: date | None,
    run_status: str | None,
):
    filters = []
    params = {
        "offset": (page - 1) * page_size,
        "page_size": page_size,
    }

    if date_from is not None:
        filters.append("run_date >= :date_from")
        params["date_from"] = date_from

    if date_to is not None:
        filters.append("run_date <= :date_to")
        params["date_to"] = date_to

    if run_status:
        filters.append("run_status = :run_status")
        params["run_status"] = run_status

    where_clause = " WHERE " + " AND ".join(filters) if filters else ""

    count_query = text(
        "SELECT COUNT(*) FROM analytics.mart_pipeline_runs" + where_clause
    )
    total = db.execute(count_query, params).scalar_one()

    data_query = text("""
        SELECT
            run_id,
            run_date,
            run_status,
            status_definition,
            is_successful_run,
            is_missed,
            missed_reason,
            scheduled_timestamp,
            start_timestamp,
            end_timestamp,
            duration_seconds,
            duration_minutes,
            sources_attempted,
            sources_succeeded,
            sources_failed,
            total_collection_attempts,
            articles_collected_total,
            articles_rejected_total,
            duplicate_records_total
        FROM analytics.mart_pipeline_runs
    """ + where_clause + """
        ORDER BY COALESCE(start_timestamp, scheduled_timestamp) DESC
        OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
    """)

    items = db.execute(data_query, params).mappings().all()

    return {
        "items": [dict(row) for row in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def get_source_daily_activity(
    db: Session,
    *,
    date_from: date | None,
    date_to: date | None,
    source_id: str | None,
):
    filters = []
    params = {}

    if date_from is not None:
        filters.append("publication_date >= :date_from")
        params["date_from"] = date_from

    if date_to is not None:
        filters.append("publication_date <= :date_to")
        params["date_to"] = date_to

    if source_id:
        filters.append("source_id = :source_id")
        params["source_id"] = source_id

    where_clause = " WHERE " + " AND ".join(filters) if filters else ""

    query = text("""
        SELECT
            publication_date,
            source_id,
            source_name,
            article_count,
            story_count,
            category_count,
            total_articles_on_date,
            share_of_date_pct,
            activity_rank_on_date,
            cumulative_articles
        FROM analytics.mart_source_daily
    """ + where_clause + """
        ORDER BY publication_date DESC, activity_rank_on_date, source_name
    """)

    return [dict(row) for row in db.execute(query, params).mappings().all()]


def get_source_reliability(db: Session):
    query = text("""
        SELECT
            source_id,
            source_name,
            collection_runs,
            successful_collections,
            failed_collections,
            success_rate_pct,
            total_attempts,
            avg_attempts_per_collection,
            retried_collections,
            total_articles_collected,
            avg_articles_collected_per_run,
            total_articles_rejected,
            total_duplicate_records,
            last_successful_run_date,
            last_failed_run_date,
            failures_by_step
        FROM analytics.mart_source_reliability
        ORDER BY success_rate_pct DESC, source_name
    """)
    return [dict(row) for row in db.execute(query).mappings().all()]


def get_category_daily_activity(
    db: Session,
    *,
    date_from: date | None,
    date_to: date | None,
    source_id: str | None,
    category_key: int | None,
):
    filters = []
    params = {}

    if date_from is not None:
        filters.append("publication_date >= :date_from")
        params["date_from"] = date_from

    if date_to is not None:
        filters.append("publication_date <= :date_to")
        params["date_to"] = date_to

    if source_id:
        filters.append("source_id = :source_id")
        params["source_id"] = source_id

    if category_key is not None:
        filters.append("category_key = :category_key")
        params["category_key"] = category_key

    where_clause = " WHERE " + " AND ".join(filters) if filters else ""

    query = text("""
        SELECT
            publication_date,
            category_key,
            category_name,
            source_id,
            source_name,
            article_count,
            share_of_source_day_pct
        FROM analytics.mart_category_daily
    """ + where_clause + """
        ORDER BY publication_date DESC, article_count DESC, category_name
    """)

    return [dict(row) for row in db.execute(query, params).mappings().all()]


def get_time_activity(
    db: Session,
    *,
    date_from: date | None,
    date_to: date | None,
    source_id: str | None,
):
    filters = []
    params = {}

    if date_from is not None:
        filters.append("publication_date >= :date_from")
        params["date_from"] = date_from

    if date_to is not None:
        filters.append("publication_date <= :date_to")
        params["date_to"] = date_to

    if source_id:
        filters.append("source_id = :source_id")
        params["source_id"] = source_id

    where_clause = " WHERE " + " AND ".join(filters) if filters else ""

    query = text("""
        SELECT
            publication_date,
            publication_hour,
            source_id,
            publication_day_name,
            publication_iso_day_of_week,
            publication_day_period,
            publication_is_weekend,
            article_count
        FROM analytics.mart_time_activity
    """ + where_clause + """
        ORDER BY publication_date DESC, publication_hour, source_id
    """)

    return [dict(row) for row in db.execute(query, params).mappings().all()]
