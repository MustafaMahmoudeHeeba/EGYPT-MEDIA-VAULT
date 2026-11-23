from __future__ import annotations

from contextlib import nullcontext
from typing import Any, Iterable

from sqlalchemy import text

from pipeline.egypt_media_vault.warehouse.database import engine


def _connection_scope(connection=None):
    """
    Use the provided SQLAlchemy connection when available.
    Otherwise, create a new transaction-scoped connection.
    """
    if connection is not None:
        return nullcontext(connection)

    return engine.begin()


def _unique_non_empty(values: Iterable[Any]) -> list[str]:
    """
    Return unique, non-empty string values while preserving order.
    """
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if value is None:
            continue

        normalized = str(value).strip()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


def ensure_categories(
    category_names: Iterable[str | None],
    connection=None,
) -> dict[str, int]:
    """
    Ensure all required categories exist in dim_category.

    Returns:
        Mapping:
            category_name -> category_key
    """
    categories = _unique_non_empty(category_names)

    if not categories:
        return {}

    with _connection_scope(connection) as conn:
        for category_name in categories:
            conn.execute(
                text(
                    """
                    IF NOT EXISTS (
                        SELECT 1
                        FROM dbo.dim_category
                        WHERE category_name = :category_name
                    )
                    BEGIN
                        INSERT INTO dbo.dim_category (
                            category_name
                        )
                        VALUES (
                            :category_name
                        )
                    END
                    """
                ),
                {"category_name": category_name},
            )

        rows = conn.execute(
            text(
                """
                SELECT
                    category_key,
                    category_name
                FROM dbo.dim_category
                WHERE category_name IN (
                    SELECT value
                    FROM STRING_SPLIT(:category_names, '|')
                )
                """
            ),
            {"category_names": "|".join(categories)},
        ).fetchall()

    return {
        str(row.category_name): int(row.category_key)
        for row in rows
    }


def ensure_unknown_author(connection=None) -> int:
    """
    Ensure an Unknown author exists.

    This is required because fact_news_articles.author_key
    is NOT NULL, while some articles may have no author.
    """
    with _connection_scope(connection) as conn:
        row = conn.execute(
            text(
                """
                SELECT TOP 1
                    author_key
                FROM dbo.dim_author
                WHERE author_name = N'Unknown'
                ORDER BY author_key
                """
            )
        ).fetchone()

        if row is not None:
            return int(row.author_key)

        result = conn.execute(
            text(
                """
                INSERT INTO dbo.dim_author (
                    author_name
                )
                OUTPUT INSERTED.author_key
                VALUES (
                    N'Unknown'
                )
                """
            )
        ).fetchone()

        if result is None:
            raise RuntimeError(
                "Failed to create Unknown author in dim_author."
            )

        return int(result.author_key)


def ensure_authors(
    author_names: Iterable[str | None],
    connection=None,
) -> dict[str, int]:
    """
    Ensure all non-empty authors exist in dim_author.

    NULL/empty authors are not inserted here.
    They are handled through the Unknown author key.
    """
    authors = _unique_non_empty(author_names)

    if not authors:
        return {}

    with _connection_scope(connection) as conn:
        for author_name in authors:
            conn.execute(
                text(
                    """
                    IF NOT EXISTS (
                        SELECT 1
                        FROM dbo.dim_author
                        WHERE author_name = :author_name
                    )
                    BEGIN
                        INSERT INTO dbo.dim_author (
                            author_name
                        )
                        VALUES (
                            :author_name
                        )
                    END
                    """
                ),
                {"author_name": author_name},
            )

        rows = conn.execute(
            text(
                """
                SELECT
                    author_key,
                    author_name
                FROM dbo.dim_author
                WHERE author_name IN (
                    SELECT value
                    FROM STRING_SPLIT(:author_names, '|')
                )
                """
            ),
            {"author_names": "|".join(authors)},
        ).fetchall()

    return {
        str(row.author_name): int(row.author_key)
        for row in rows
    }


def upsert_dim_article(
    articles: Iterable[Any],
    connection=None,
) -> dict[str, int]:
    """
    Insert new articles into dim_article and return
    article_id -> article_key mapping.

    Existing articles are not duplicated.
    """
    article_list = [
        article
        for article in articles
        if getattr(article, "article_id", None)
    ]

    if not article_list:
        return {}

    with _connection_scope(connection) as conn:
        for article in article_list:
            conn.execute(
                text(
                    """
                    IF NOT EXISTS (
                        SELECT 1
                        FROM dbo.dim_article
                        WHERE article_id = :article_id
                    )
                    BEGIN
                        INSERT INTO dbo.dim_article (
                            article_id,
                            article_title,
                            original_url,
                            canonical_url_hash,
                            article_description,
                            article_content,
                            article_image_url,
                            link_availability,
                            warehouse_created_at,
                            warehouse_updated_at
                        )
                        VALUES (
                            :article_id,
                            :article_title,
                            :original_url,
                            :canonical_url_hash,
                            :article_description,
                            :article_content,
                            :article_image_url,
                            :link_availability,
                            SYSUTCDATETIME(),
                            SYSUTCDATETIME()
                        )
                    END
                    """
                ),
                {
                    "article_id": article.article_id,
                    "article_title": article.title or "",
                    "original_url": getattr(
                        article,
                        "url",
                        None,
                    ),
                    "canonical_url_hash": getattr(
                        article,
                        "canonical_url_hash",
                        None,
                    ),
                    "article_description": getattr(
                        article,
                        "description",
                        None,
                    ),
                    "article_content": getattr(
                        article,
                        "content",
                        None,
                    ),
                    "article_image_url": getattr(
                        article,
                        "image_url",
                        None,
                    ),
                    "link_availability": "Available",
                },
            )

        rows = conn.execute(
            text(
                """
                SELECT
                    article_key,
                    article_id
                FROM dbo.dim_article
                WHERE article_id IN (
                    SELECT value
                    FROM STRING_SPLIT(:article_ids, '|')
                )
                """
            ),
            {
                "article_ids": "|".join(
                    article.article_id
                    for article in article_list
                )
            },
        ).fetchall()

    return {
        str(row.article_id): int(row.article_key)
        for row in rows
    }


def upsert_dim_story(
    articles: Iterable[Any],
    connection=None,
) -> dict[str, int]:
    """
    Insert new stories into dim_story and return
    story_id -> story_key mapping.

    Existing stories are not duplicated.
    """
    story_pairs: dict[str, str] = {}

    for article in articles:
        story_id = getattr(article, "story_id", None)

        if not story_id:
            continue

        title = getattr(article, "title", None) or ""

        if story_id not in story_pairs:
            story_pairs[story_id] = title

    if not story_pairs:
        return {}

    with _connection_scope(connection) as conn:
        for story_id, representative_title in story_pairs.items():
            conn.execute(
                text(
                    """
                    IF NOT EXISTS (
                        SELECT 1
                        FROM dbo.dim_story
                        WHERE story_id = :story_id
                    )
                    BEGIN
                        INSERT INTO dbo.dim_story (
                            story_id,
                            representative_title,
                            warehouse_created_at,
                            warehouse_updated_at
                        )
                        VALUES (
                            :story_id,
                            :representative_title,
                            SYSUTCDATETIME(),
                            SYSUTCDATETIME()
                        )
                    END
                    """
                ),
                {
                    "story_id": story_id,
                    "representative_title": representative_title,
                },
            )

        rows = conn.execute(
            text(
                """
                SELECT
                    story_key,
                    story_id
                FROM dbo.dim_story
                WHERE story_id IN (
                    SELECT value
                    FROM STRING_SPLIT(:story_ids, '|')
                )
                """
            ),
            {
                "story_ids": "|".join(story_pairs.keys())
            },
        ).fetchall()

    return {
        str(row.story_id): int(row.story_key)
        for row in rows
    }