
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


STORY_FROM = """
    FROM analytics.mart_story_coverage AS s
    WHERE
        (:search IS NULL OR s.story_title LIKE '%' + :search + '%')
        AND (
            :multi_source_only = 0
            OR s.is_multi_source = 1
        )
        AND (
            :min_sources IS NULL
            OR s.source_count >= :min_sources
        )
        AND (
            :date_from IS NULL
            OR s.last_published_at >= :date_from
        )
        AND (
            :date_to IS NULL
            OR s.first_published_at < DATEADD(day, 1, :date_to)
        )
"""


def _build_filters(
    *,
    search: str | None = None,
    multi_source_only: bool = False,
    min_sources: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, Any]:
    return {
        "search": search.strip() if search and search.strip() else None,
        "multi_source_only": multi_source_only,
        "min_sources": min_sources,
        "date_from": date_from,
        "date_to": date_to,
    }


def get_stories(
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
    """Return a paginated list of stories from the coverage mart."""

    filters = _build_filters(
        search=search,
        multi_source_only=multi_source_only,
        min_sources=min_sources,
        date_from=date_from,
        date_to=date_to,
    )

    allowed_sort_columns = {
        "story_title": "s.story_title",
        "article_count": "s.article_count",
        "source_count": "s.source_count",
        "first_published_at": "s.first_published_at",
        "last_published_at": "s.last_published_at",
        "coverage_gap_minutes": "s.coverage_gap_minutes",
        "coverage_rank": "s.coverage_rank",
    }

    sort_column = allowed_sort_columns.get(
        sort_by, "s.last_published_at"
    )
    sort_direction = (
        "ASC" if sort_order.lower() == "asc" else "DESC"
    )

    total = db.execute(
        text(f"SELECT COUNT(*) {STORY_FROM}"),
        filters,
    ).scalar_one()

    offset = (page - 1) * page_size

    query = text(
        f"""
        SELECT
            s.story_id,
            s.story_key,
            s.story_title,
            s.article_count,
            s.source_count,
            s.is_multi_source,
            s.publisher_ids,
            s.publisher_names,
            s.first_published_at,
            s.last_published_at,
            s.coverage_gap_minutes,
            s.first_source_id,
            s.first_source_name,
            s.articles_missing_publication_time,
            s.coverage_rank
        {STORY_FROM}
        ORDER BY {sort_column} {sort_direction}, s.story_key DESC
        OFFSET :offset ROWS
        FETCH NEXT :page_size ROWS ONLY
        """
    )

    rows = db.execute(
        query,
        {
            **filters,
            "offset": offset,
            "page_size": page_size,
        },
    ).mappings().all()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def get_story_by_id(
    db: Session,
    story_id: str,
) -> dict[str, Any] | None:
    """Return coverage information for one story."""

    query = text(
        """
        SELECT
            story_id,
            story_key,
            story_title,
            article_count,
            source_count,
            is_multi_source,
            publisher_ids,
            publisher_names,
            first_published_at,
            last_published_at,
            coverage_gap_minutes,
            first_source_id,
            first_source_name,
            articles_missing_publication_time,
            coverage_rank
        FROM analytics.mart_story_coverage
        WHERE story_id = :story_id
        """
    )

    row = db.execute(
        query,
        {"story_id": story_id},
    ).mappings().first()

    return dict(row) if row else None


def get_story_timeline(
    db: Session,
    story_id: str,
) -> list[dict[str, Any]]:
    """Return the publication timeline of a story across news sources."""

    query = text(
        """
        SELECT
            story_id,
            story_key,
            story_title,
            source_id,
            source_name,
            story_source_count,
            article_count,
            articles_missing_publication_time,
            first_published_at,
            last_published_at,
            story_first_published_at,
            minutes_after_story_first_publication,
            publication_order,
            is_first_source
        FROM analytics.mart_story_source_timeline
        WHERE story_id = :story_id
        ORDER BY publication_order ASC, source_id ASC
        """
    )

    rows = db.execute(
        query,
        {"story_id": story_id},
    ).mappings().all()

    return [dict(row) for row in rows]


def get_story_kpis(db: Session) -> dict[str, Any] | None:
    """Return the precomputed story KPIs from the analytics mart."""

    query = text(
        """
        SELECT
            kpi_scope,
            total_stories,
            multi_source_stories,
            single_source_stories,
            multi_source_story_pct,
            avg_publishers_per_story,
            max_publishers_per_story,
            total_articles_in_stories,
            avg_articles_per_story,
            avg_coverage_gap_minutes_multi_source,
            stories_without_articles,
            unknown_sentinel_stories,
            stories_in_dimension,
            generated_at_utc
        FROM analytics.mart_story_kpis
        """
    )

    row = db.execute(query).mappings().first()

    return dict(row) if row else None
