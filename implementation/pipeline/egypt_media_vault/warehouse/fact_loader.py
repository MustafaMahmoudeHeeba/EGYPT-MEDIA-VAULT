
from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone
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


def _to_utc_naive(value: datetime | None) -> datetime | None:
    """
    Convert an aware datetime to UTC and remove timezone information.

    SQL Server datetime2 stores a naive datetime value.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        return value

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _get_article_source_id(article: Any) -> str | None:
    """
    Resolve the operational source identifier from an Article.
    """
    source_id = (
        getattr(article, "source_id", None)
        or getattr(article, "source", None)
    )

    if source_id is None:
        return None

    normalized_source_id = str(source_id).strip()

    return normalized_source_id or None


def _load_staging_metadata(
    staging_record_ids: Iterable[int],
    connection,
) -> dict[int, dict[str, Any]]:
    """
    Load authoritative ingestion and publication metadata
    from dbo.raw_articles for the supplied staging records.
    """
    staging_ids = list(staging_record_ids)

    if not staging_ids:
        return {}

    if any(
        not isinstance(staging_id, int) or staging_id <= 0
        for staging_id in staging_ids
    ):
        raise RuntimeError(
            "All staging_record_ids must be positive integers."
        )

    if len(staging_ids) != len(set(staging_ids)):
        raise RuntimeError(
            "Duplicate staging_record_id values were supplied."
        )

    parameters = {
        f"staging_id_{index}": staging_id
        for index, staging_id in enumerate(staging_ids)
    }

    placeholders = ", ".join(
        f":staging_id_{index}"
        for index in range(len(staging_ids))
    )

    result = connection.execute(
        text(
            f"""
            SELECT
                staging_record_id,
                publication_timestamp,
                timestamp_validity,
                is_syndicated,
                ingestion_timestamp
            FROM dbo.raw_articles
            WHERE staging_record_id IN ({placeholders})
            """
        ),
        parameters,
    )

    metadata_by_staging_id = {}

    for row in result.fetchall():
        row_data = row._mapping
        staging_id = int(row_data["staging_record_id"])

        metadata_by_staging_id[staging_id] = {
            "publication_timestamp": row_data["publication_timestamp"],
            "timestamp_validity": row_data["timestamp_validity"],
            "is_syndicated": row_data["is_syndicated"],
            "ingestion_timestamp": row_data["ingestion_timestamp"],
        }

    missing_ids = set(staging_ids) - set(metadata_by_staging_id)

    if missing_ids:
        raise RuntimeError(
            "Staging metadata could not be found for "
            f"staging_record_ids={sorted(missing_ids)}."
        )

    return metadata_by_staging_id


def _get_article_flag_key(
    timestamp_validity: str,
    is_syndicated: bool,
    connection,
) -> int:
    """
    Resolve article_flag_key using authoritative staging metadata.
    """
    allowed_validity_values = {
        "Valid",
        "Invalid",
        "Unknown",
    }

    if timestamp_validity not in allowed_validity_values:
        raise RuntimeError(
            "Invalid timestamp_validity value in staging metadata: "
            f"{timestamp_validity!r}."
        )

    syndication_indicator = (
        "Syndicated"
        if bool(is_syndicated)
        else "Not syndicated"
    )

    row = connection.execute(
        text(
            """
            SELECT TOP 1
                article_flag_key
            FROM dbo.dim_article_flag
            WHERE timestamp_validity = :timestamp_validity
              AND syndication_indicator = :syndication_indicator
            """
        ),
        {
            "timestamp_validity": timestamp_validity,
            "syndication_indicator": syndication_indicator,
        },
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "No matching article_flag_key found for "
            f"timestamp_validity={timestamp_validity!r}, "
            f"syndication_indicator={syndication_indicator!r}."
        )

    return int(row.article_flag_key)


def _get_publication_timestamp(
    staging_metadata: dict[str, Any],
) -> datetime | None:
    """
    Use publication_timestamp only when staging marks it as Valid.
    """
    timestamp_validity = staging_metadata["timestamp_validity"]
    publication_timestamp = staging_metadata["publication_timestamp"]

    if timestamp_validity != "Valid":
        return None

    if publication_timestamp is None:
        raise RuntimeError(
            "Staging metadata is inconsistent: timestamp_validity "
            "is 'Valid' but publication_timestamp is NULL."
        )

    return _to_utc_naive(publication_timestamp)


def _get_date_key(
    timestamp: datetime | None,
    connection,
) -> int:
    """
    Resolve date_key from dim_date.

    Returns 0 when publication timestamp is unavailable.
    """
    if timestamp is None:
        return 0

    row = connection.execute(
        text(
            """
            SELECT TOP 1
                date_key
            FROM dbo.dim_date
            WHERE full_date = CAST(:timestamp AS date)
            """
        ),
        {"timestamp": timestamp},
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"No dim_date row found for date {timestamp.date()}."
        )

    return int(row.date_key)


def _get_time_key(
    timestamp: datetime | None,
    connection,
) -> int:
    """
    Resolve time_key from dim_time_of_day.

    Returns 0 when publication timestamp is unavailable.
    """
    if timestamp is None:
        return 0

    row = connection.execute(
        text(
            """
            SELECT TOP 1
                time_key
            FROM dbo.dim_time_of_day
            WHERE full_time = CAST(:timestamp AS time)
            """
        ),
        {"timestamp": timestamp},
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "No dim_time_of_day row found for time "
            f"{timestamp.time()}."
        )

    return int(row.time_key)


def _get_source_key(
    source_id: str | None,
    connection,
) -> int:
    """
    Resolve source_key from dim_source.
    """
    if not source_id:
        raise RuntimeError(
            "Cannot load fact_news_articles without source_id."
        )

    row = connection.execute(
        text(
            """
            SELECT TOP 1
                source_key
            FROM dbo.dim_source
            WHERE source_id = :source_id
              AND is_current = 1
            ORDER BY source_key
            """
        ),
        {"source_id": source_id},
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"No current dim_source row found for source_id={source_id!r}."
        )

    return int(row.source_key)


def _get_category_key(
    category_name: str | None,
    category_keys: dict[str, int],
) -> int:
    """
    Resolve category_key from the dimension-loader mapping.
    """
    if not category_name:
        raise RuntimeError(
            "Cannot load fact_news_articles without category_name."
        )

    category_key = category_keys.get(category_name)

    if category_key is None:
        raise RuntimeError(
            f"No dim_category key found for category={category_name!r}."
        )

    return int(category_key)


def _get_author_key(
    author_name: str | None,
    author_keys: dict[str, int],
    unknown_author_key: int,
) -> int:
    """
    Resolve author_key.

    NULL/empty authors use the Unknown author surrogate key.
    """
    if not author_name:
        return unknown_author_key

    author_key = author_keys.get(author_name)

    if author_key is None:
        raise RuntimeError(
            f"No dim_author key found for author={author_name!r}."
        )

    return int(author_key)


def _get_story_key(
    story_id: str | None,
    story_keys: dict[str, int],
) -> int:
    """
    Resolve story_key.
    """
    if not story_id:
        raise RuntimeError(
            "Cannot load fact_news_articles without story_id."
        )

    story_key = story_keys.get(story_id)

    if story_key is None:
        raise RuntimeError(
            f"No dim_story key found for story_id={story_id!r}."
        )

    return int(story_key)


def _get_article_key(
    article_id: str | None,
    article_keys: dict[str, int],
) -> int:
    """
    Resolve article_key.
    """
    if not article_id:
        raise RuntimeError(
            "Cannot load fact_news_articles without article_id."
        )

    article_key = article_keys.get(article_id)

    if article_key is None:
        raise RuntimeError(
            f"No dim_article key found for article_id={article_id!r}."
        )

    return int(article_key)


def _get_ingestion_date_key(
    ingestion_timestamp: datetime | None,
    connection,
) -> int:
    """
    Resolve ingestion_date_key from the SQL landing timestamp.
    """
    if ingestion_timestamp is None:
        raise RuntimeError(
            "Cannot load fact_news_articles without ingestion_timestamp."
        )

    return _get_date_key(ingestion_timestamp, connection)


def load_fact_news_articles(
    articles: Iterable[Any],
    article_keys: dict[str, int],
    story_keys: dict[str, int],
    category_keys: dict[str, int],
    author_keys: dict[str, int],
    unknown_author_key: int,
    staging_record_ids_by_article_id: dict[str, int],
    connection=None,
) -> int:
    """
    Insert or update fact_news_articles rows.

    Grain:
        One valid article.

    Staging metadata is the authoritative source for:
        - publication_timestamp
        - timestamp_validity
        - is_syndicated
        - ingestion_timestamp

    article_key is the fact primary key, making reruns idempotent.

    Returns:
        Number of fact rows processed.
    """
    article_list = list(articles)

    if not article_list:
        return 0

    if not staging_record_ids_by_article_id:
        raise RuntimeError(
            "Cannot load facts without staging_record_ids_by_article_id."
        )

    article_ids = [
        getattr(article, "article_id", None)
        for article in article_list
    ]

    if any(not article_id for article_id in article_ids):
        raise RuntimeError(
            "Cannot load fact_news_articles: an article_id is missing."
        )

    if len(article_ids) != len(set(article_ids)):
        raise RuntimeError(
            "Duplicate article_id values were supplied to fact loading."
        )

    missing_mappings = (
        set(article_ids) - set(staging_record_ids_by_article_id)
    )

    if missing_mappings:
        raise RuntimeError(
            "Missing staging record mappings for article_ids="
            f"{sorted(missing_mappings)}."
        )

    staging_ids = [
        staging_record_ids_by_article_id[article_id]
        for article_id in article_ids
    ]

    processed_count = 0

    with _connection_scope(connection) as conn:
        staging_metadata_by_id = _load_staging_metadata(
            staging_ids,
            conn,
        )

        for article in article_list:
            article_id = article.article_id
            staging_id = staging_record_ids_by_article_id[article_id]
            staging_metadata = staging_metadata_by_id[staging_id]

            article_key = _get_article_key(
                article_id,
                article_keys,
            )

            story_key = _get_story_key(
                getattr(article, "story_id", None),
                story_keys,
            )

            source_id = _get_article_source_id(article)

            source_key = _get_source_key(
                source_id,
                conn,
            )

            category_key = _get_category_key(
                getattr(article, "category", None),
                category_keys,
            )

            author_key = _get_author_key(
                getattr(article, "author", None),
                author_keys,
                unknown_author_key,
            )

            article_flag_key = _get_article_flag_key(
                staging_metadata["timestamp_validity"],
                staging_metadata["is_syndicated"],
                conn,
            )

            publication_timestamp = _get_publication_timestamp(
                staging_metadata
            )

            publication_date_key = _get_date_key(
                publication_timestamp,
                conn,
            )

            publication_time_of_day_key = _get_time_key(
                publication_timestamp,
                conn,
            )

            ingestion_timestamp = _to_utc_naive(
                staging_metadata["ingestion_timestamp"]
            )

            if ingestion_timestamp is None:
                raise RuntimeError(
                    f"Staging record {staging_id} for article "
                    f"{article_id!r} has no ingestion_timestamp."
                )

            ingestion_date_key = _get_ingestion_date_key(
                ingestion_timestamp,
                conn,
            )

            existing = conn.execute(
                text(
                    """
                    SELECT
                        ingestion_timestamp
                    FROM dbo.fact_news_articles
                    WHERE article_key = :article_key
                    """
                ),
                {"article_key": article_key},
            ).fetchone()

            if existing is None:
                conn.execute(
                    text(
                        """
                        INSERT INTO dbo.fact_news_articles (
                            article_key,
                            source_key,
                            story_key,
                            category_key,
                            author_key,
                            article_flag_key,
                            publication_date_key,
                            publication_time_of_day_key,
                            ingestion_date_key,
                            article_count,
                            publication_timestamp,
                            ingestion_timestamp
                        )
                        VALUES (
                            :article_key,
                            :source_key,
                            :story_key,
                            :category_key,
                            :author_key,
                            :article_flag_key,
                            :publication_date_key,
                            :publication_time_of_day_key,
                            :ingestion_date_key,
                            1,
                            :publication_timestamp,
                            :ingestion_timestamp
                        )
                        """
                    ),
                    {
                        "article_key": article_key,
                        "source_key": source_key,
                        "story_key": story_key,
                        "category_key": category_key,
                        "author_key": author_key,
                        "article_flag_key": article_flag_key,
                        "publication_date_key": publication_date_key,
                        "publication_time_of_day_key": (
                            publication_time_of_day_key
                        ),
                        "ingestion_date_key": ingestion_date_key,
                        "publication_timestamp": publication_timestamp,
                        "ingestion_timestamp": ingestion_timestamp,
                    },
                )
            else:
                # Preserve the original ingestion timestamp/date.
                # The fact grain is one article, not one raw snapshot.
                conn.execute(
                    text(
                        """
                        UPDATE dbo.fact_news_articles
                        SET
                            source_key = :source_key,
                            story_key = :story_key,
                            category_key = :category_key,
                            author_key = :author_key,
                            article_flag_key = :article_flag_key,
                            publication_date_key = :publication_date_key,
                            publication_time_of_day_key =
                                :publication_time_of_day_key,
                            publication_timestamp =
                                :publication_timestamp,
                            article_count = 1
                        WHERE article_key = :article_key
                        """
                    ),
                    {
                        "article_key": article_key,
                        "source_key": source_key,
                        "story_key": story_key,
                        "category_key": category_key,
                        "author_key": author_key,
                        "article_flag_key": article_flag_key,
                        "publication_date_key": publication_date_key,
                        "publication_time_of_day_key": (
                            publication_time_of_day_key
                        ),
                        "publication_timestamp": publication_timestamp,
                    },
                )

            processed_count += 1

    return processed_count
