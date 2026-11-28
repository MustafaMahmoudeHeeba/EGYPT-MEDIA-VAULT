
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


ARTICLE_FROM = """
    FROM core.fct_articles AS f
    LEFT JOIN dbo.dim_article AS d
        ON f.article_id = d.article_id
    WHERE
        (:search IS NULL OR f.article_title LIKE '%' + :search + '%')
        AND (:source_id IS NULL OR f.source_id = :source_id)
        AND (:category_name IS NULL OR f.category_name = :category_name)
        AND (:story_id IS NULL OR f.story_id = :story_id)
        AND (:date_from IS NULL OR f.publication_timestamp >= :date_from)
        AND (
            :date_to IS NULL
            OR f.publication_timestamp < DATEADD(day, 1, :date_to)
        )
"""


def _build_filters(
    search: str | None = None,
    source_id: str | None = None,
    category_name: str | None = None,
    story_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, Any]:
    return {
        "search": search.strip() if search and search.strip() else None,
        "source_id": source_id,
        "category_name": category_name,
        "story_id": story_id,
        "date_from": date_from,
        "date_to": date_to,
    }


def get_articles(
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
) -> dict[str, Any]:
    """Return a paginated list of articles without loading full content."""

    filters = _build_filters(
        search=search,
        source_id=source_id,
        category_name=category_name,
        story_id=story_id,
        date_from=date_from,
        date_to=date_to,
    )

    allowed_sort_columns = {
        "publication_timestamp": "f.publication_timestamp",
        "ingestion_timestamp": "f.ingestion_timestamp",
        "article_title": "f.article_title",
    }

    sort_column = allowed_sort_columns.get(
        sort_by, "f.publication_timestamp"
    )
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"

    count_query = text(
        f"""
        SELECT COUNT(*)
        {ARTICLE_FROM}
        """
    )

    total = db.execute(count_query, filters).scalar_one()

    offset = (page - 1) * page_size

    articles_query = text(
        f"""
        SELECT
            f.article_key,
            f.article_id,
            f.article_title,
            f.original_url,
            f.story_id,
            f.story_title,
            f.story_membership_status,
            f.story_article_count,
            f.story_source_count,
            f.is_multi_source_story,
            f.source_id,
            f.source_name,
            f.category_key,
            f.category_name,
            f.author_name,
            f.publication_timestamp,
            f.has_publication_time,
            f.ingestion_timestamp,
            f.article_updated_at,
            f.has_content,
            f.has_description,
            f.has_image,
            d.article_description,
            d.article_image_url,
            f.link_availability
        {ARTICLE_FROM}
        ORDER BY {sort_column} {sort_direction}, f.article_key DESC
        OFFSET :offset ROWS
        FETCH NEXT :page_size ROWS ONLY
        """
    )

    rows = db.execute(
        articles_query,
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


def get_article_by_id(
    db: Session,
    article_id: str,
) -> dict[str, Any] | None:
    """Return one article including its full description and content."""

    query = text(
        """
        SELECT
            f.article_key,
            f.article_id,
            COALESCE(d.article_title, f.article_title) AS article_title,
            f.original_url,
            f.story_id,
            f.story_title,
            f.story_membership_status,
            f.story_article_count,
            f.story_source_count,
            f.is_multi_source_story,
            f.source_id,
            f.source_name,
            f.category_key,
            f.category_name,
            f.author_key,
            f.author_name,
            f.publication_timestamp,
            f.has_publication_time,
            f.timestamp_validity,
            f.syndication_indicator,
            f.ingestion_timestamp,
            f.article_updated_at,
            d.article_description,
            d.article_content,
            d.article_image_url,
            f.link_availability,
            f.has_content,
            f.has_description,
            f.has_image
        FROM core.fct_articles AS f
        LEFT JOIN dbo.dim_article AS d
            ON f.article_id = d.article_id
        WHERE f.article_id = :article_id
        """
    )

    row = db.execute(
        query,
        {"article_id": article_id},
    ).mappings().first()

    return dict(row) if row else None

