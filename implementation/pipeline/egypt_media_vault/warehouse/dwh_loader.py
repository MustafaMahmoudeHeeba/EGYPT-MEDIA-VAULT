
from __future__ import annotations

from contextlib import nullcontext
from typing import Any, Iterable

from pipeline.egypt_media_vault.warehouse.database import engine

from .dimension_loader import (
    ensure_authors,
    ensure_categories,
    ensure_unknown_author,
    upsert_dim_article,
    upsert_dim_story,
)
from .fact_loader import load_fact_news_articles


def _connection_scope(connection=None):
    """
    Use the provided SQLAlchemy connection when available.
    Otherwise, create one transaction-scoped connection.
    """
    if connection is not None:
        return nullcontext(connection)

    return engine.begin()


def _attach_story_ids(
    articles: list[Any],
    story_ids_by_article_id: dict[str, str] | None,
) -> None:
    """
    Attach verified Story IDs to article objects before DWH loading.
    """
    if not story_ids_by_article_id:
        raise RuntimeError(
            "Cannot load DWH without verified story IDs."
        )

    missing_story_ids: list[str] = []

    for article in articles:
        article_id = getattr(article, "article_id", None)

        if not article_id:
            missing_story_ids.append("<missing article_id>")
            continue

        story_id = story_ids_by_article_id.get(article_id)

        if not story_id:
            missing_story_ids.append(article_id)
            continue

        # Attach the already-persisted and verified Story ID.
        article.story_id = story_id

    if missing_story_ids:
        raise RuntimeError(
            "Cannot load DWH because Story IDs are missing for "
            f"{len(missing_story_ids)} articles: "
            f"{missing_story_ids}"
        )


def _validate_staging_record_ids(
    articles: list[Any],
    staging_record_ids_by_article_id: dict[str, int] | None,
) -> None:
    """
    Validate the mapping between article IDs and SQL staging records.

    Every article must map to exactly one existing staging record ID.
    Staging record IDs must be positive integers and unique within
    the current batch.
    """
    if not staging_record_ids_by_article_id:
        raise RuntimeError(
            "Cannot load DWH without staging_record_ids_by_article_id."
        )

    article_ids = []

    for article in articles:
        article_id = getattr(article, "article_id", None)

        if not article_id:
            raise RuntimeError(
                "Cannot validate staging mappings: "
                "an article is missing article_id."
            )

        article_ids.append(article_id)

    if len(article_ids) != len(set(article_ids)):
        raise RuntimeError(
            "Duplicate article_id values were supplied to DWH loading."
        )

    expected_article_ids = set(article_ids)
    supplied_article_ids = set(staging_record_ids_by_article_id)

    missing_article_ids = expected_article_ids - supplied_article_ids
    unexpected_article_ids = supplied_article_ids - expected_article_ids

    if missing_article_ids or unexpected_article_ids:
        raise RuntimeError(
            "Invalid article-to-staging mapping. "
            f"Missing article_ids: {sorted(missing_article_ids)}. "
            f"Unexpected article_ids: {sorted(unexpected_article_ids)}."
        )

    staging_ids = list(staging_record_ids_by_article_id.values())

    if any(
        not isinstance(staging_id, int)
        or isinstance(staging_id, bool)
        or staging_id <= 0
        for staging_id in staging_ids
    ):
        raise RuntimeError(
            "All staging_record_id values must be positive integers."
        )

    if len(staging_ids) != len(set(staging_ids)):
        raise RuntimeError(
            "Duplicate staging_record_id values were supplied."
        )


def load_articles_to_dwh(
    articles: Iterable[Any],
    story_ids_by_article_id: dict[str, str] | None = None,
    staging_record_ids_by_article_id: dict[str, int] | None = None,
    connection=None,
) -> dict[str, int]:
    """
    Load a batch of processed articles into the DWH.

    Loading order:

        1. Categories
        2. Authors
        3. Unknown author
        4. dim_article
        5. dim_story
        6. fact_news_articles

    Story IDs must already have been persisted and verified in SQL
    staging.

    Staging record IDs are used to retrieve authoritative publication
    and ingestion metadata from dbo.raw_articles.

    The complete DWH load uses one transaction when no external
    connection is supplied.
    """
    article_list = list(articles)

    if not article_list:
        return {
            "articles_received": 0,
            "articles_loaded_to_dim_article": 0,
            "stories_loaded_to_dim_story": 0,
            "categories_available": 0,
            "authors_available": 0,
            "facts_loaded": 0,
        }

    # -------------------------------------------------------------
    # 0. Attach verified Story IDs
    # -------------------------------------------------------------
    _attach_story_ids(
        article_list,
        story_ids_by_article_id,
    )

    # -------------------------------------------------------------
    # 0.1 Validate article-to-staging mappings
    # -------------------------------------------------------------
    _validate_staging_record_ids(
        article_list,
        staging_record_ids_by_article_id,
    )

    with _connection_scope(connection) as conn:
        # ---------------------------------------------------------
        # 1. Prepare category dimension
        # ---------------------------------------------------------
        category_keys = ensure_categories(
            (
                getattr(article, "category", None)
                for article in article_list
            ),
            connection=conn,
        )

        # ---------------------------------------------------------
        # 2. Prepare author dimension
        # ---------------------------------------------------------
        author_keys = ensure_authors(
            (
                getattr(article, "author", None)
                for article in article_list
            ),
            connection=conn,
        )

        # ---------------------------------------------------------
        # 3. Ensure Unknown author exists
        # ---------------------------------------------------------
        unknown_author_key = ensure_unknown_author(
            connection=conn
        )

        # ---------------------------------------------------------
        # 4. Load article dimension
        # ---------------------------------------------------------
        article_keys = upsert_dim_article(
            article_list,
            connection=conn,
        )

        # ---------------------------------------------------------
        # 5. Load story dimension
        # ---------------------------------------------------------
        story_keys = upsert_dim_story(
            article_list,
            connection=conn,
        )

        # ---------------------------------------------------------
        # 6. Load fact table
        # ---------------------------------------------------------
        facts_loaded = load_fact_news_articles(
            article_list,
            article_keys=article_keys,
            story_keys=story_keys,
            category_keys=category_keys,
            author_keys=author_keys,
            unknown_author_key=unknown_author_key,
            staging_record_ids_by_article_id=(
                staging_record_ids_by_article_id
            ),
            connection=conn,
        )

        return {
            "articles_received": len(article_list),
            "articles_loaded_to_dim_article": len(article_keys),
            "stories_loaded_to_dim_story": len(story_keys),
            "categories_available": len(category_keys),
            "authors_available": len(author_keys),
            "facts_loaded": facts_loaded,
        }
