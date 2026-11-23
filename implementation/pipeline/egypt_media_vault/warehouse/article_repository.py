from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection

from pipeline.egypt_media_vault.warehouse.database import engine


# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_PROCESSING_STATUSES = {
    "Pending",
    "Validated",
    "Rejected",
    "Normalized",
    "Duplicate",
    "Updated",
    "Stored",
    "Failed",
}

ALLOWED_TIMESTAMP_VALIDITY = {
    "Valid",
    "Invalid",
    "Unknown",
}

ELIGIBLE_EXISTING_STATUSES = ("Stored", "Updated")

UNSET = object()


# =========================================================
# CONNECTION HELPER
# =========================================================

def _connection_scope(connection: Optional[Connection] = None):
    """
    Use a supplied connection without committing or closing it.

    If no connection is supplied, create a normal transaction
    owned by this repository operation.
    """

    if connection is not None:
        return nullcontext(connection)

    return engine.begin()


# =========================================================
# HELPERS
# =========================================================

def _normalize_source(source: str) -> str:
    return source.strip().lower()


def _to_utc_naive(
    value: Optional[datetime],
) -> Optional[datetime]:
    """
    Convert timezone-aware datetime to naive UTC.

    SQL Server DATETIME2 does not preserve timezone information.
    All timestamps are therefore stored as UTC without tzinfo.
    """

    if value is None:
        return None

    if not isinstance(value, datetime):
        raise TypeError("Expected a datetime value or None.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "Datetime must include timezone information."
        )

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _get_raw_article_value(
    article: Any,
    field: str,
) -> Any:
    return getattr(article, field, None)


def _timestamp_validity(
    publication_date: Optional[datetime],
    raw_publication_text: Optional[str],
) -> str:
    """
    Determine publication timestamp validity.
    """

    if publication_date is not None:
        if (
            isinstance(publication_date, datetime)
            and publication_date.tzinfo is not None
            and publication_date.utcoffset() is not None
        ):
            return "Valid"

        return "Invalid"

    if (
        isinstance(raw_publication_text, str)
        and raw_publication_text.strip()
    ):
        return "Invalid"

    return "Unknown"


# =========================================================
# RAW ARTICLE INSERTION
# =========================================================

def insert_raw_articles(
    raw_articles: Iterable[Any],
    run_id: str,
    connection: Optional[Connection] = None,
) -> list[int]:
    """
    Insert collected RawArticle objects into SQL staging.

    Returns staging_record_ids in the same order as input.

    If connection is supplied, the caller owns the transaction.
    Otherwise, this function manages its own transaction.
    """

    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id cannot be empty.")

    articles = list(raw_articles)

    if not articles:
        return []

    insert_statement = text("""
        INSERT INTO dbo.raw_articles
        (
            run_id,
            source_id,
            raw_title,
            raw_source_name,
            original_url,
            canonical_url,
            raw_publication_text,
            raw_category_label,
            raw_description,
            raw_content,
            raw_author,
            raw_update_text,
            image_url,
            title_hash,
            publication_timestamp,
            timestamp_validity,
            standardized_source_name,
            standardized_category_name,
            processing_status
        )
        OUTPUT INSERTED.staging_record_id
        VALUES
        (
            :run_id,
            :source_id,
            :raw_title,
            :raw_source_name,
            :original_url,
            NULL,
            :raw_publication_text,
            :raw_category_label,
            :raw_description,
            :raw_content,
            :raw_author,
            :raw_update_text,
            :image_url,
            NULL,
            :publication_timestamp,
            :timestamp_validity,
            NULL,
            NULL,
            N'Pending'
        );
    """)

    staging_record_ids: list[int] = []

    with _connection_scope(connection) as conn:
        for article in articles:
            source = _get_raw_article_value(article, "source")
            title = _get_raw_article_value(article, "title")
            url = _get_raw_article_value(article, "url")

            if not isinstance(source, str) or not source.strip():
                raise ValueError(
                    "Raw article source is required for SQL staging."
                )

            raw_publication_text = _get_raw_article_value(
                article,
                "raw_publication_text",
            )

            publication_date = _get_raw_article_value(
                article,
                "publication_date",
            )

            timestamp_validity = _timestamp_validity(
                publication_date,
                raw_publication_text,
            )

            publication_timestamp = (
                _to_utc_naive(publication_date)
                if timestamp_validity == "Valid"
                else None
            )

            parameters = {
                "run_id": run_id,
                "source_id": _normalize_source(source),
                "raw_title": title,
                "raw_source_name": source,
                "original_url": url,
                "raw_publication_text": raw_publication_text,
                "raw_category_label": _get_raw_article_value(
                    article,
                    "category",
                ),
                "raw_description": _get_raw_article_value(
                    article,
                    "description",
                ),
                "raw_content": _get_raw_article_value(
                    article,
                    "content",
                ),
                "raw_author": _get_raw_article_value(
                    article,
                    "author",
                ),
                "raw_update_text": _get_raw_article_value(
                    article,
                    "raw_update_text",
                ),
                "image_url": _get_raw_article_value(
                    article,
                    "image_url",
                ),
                "publication_timestamp": publication_timestamp,
                "timestamp_validity": timestamp_validity,
            }

            result = conn.execute(
                insert_statement,
                parameters,
            )

            staging_record_id = result.scalar_one()
            staging_record_ids.append(int(staging_record_id))

    return staging_record_ids


# =========================================================
# VALIDATION ISSUE INSERTION
# =========================================================

def insert_validation_issues(
    staging_record_id: int,
    issues: Iterable[Any],
    connection: Optional[Connection] = None,
) -> int:
    """
    Insert validation issues for one staging record.

    Warning issues are non-rejecting.
    Error and critical issues are rejecting.

    If connection is supplied, the caller owns the transaction.
    """

    issue_list = list(issues)

    if not issue_list:
        return 0

    insert_statement = text("""
        INSERT INTO dbo.raw_article_issues
        (
            staging_record_id,
            issue_seq,
            issue_type,
            field_name,
            issue_description,
            is_rejecting,
            detected_at
        )
        VALUES
        (
            :staging_record_id,
            :issue_seq,
            :issue_type,
            :field_name,
            :issue_description,
            :is_rejecting,
            :detected_at
        );
    """)

    with _connection_scope(connection) as conn:

        last_sequence = conn.execute(
            text("""
                SELECT COALESCE(MAX(issue_seq), 0)
                FROM dbo.raw_article_issues
                    WITH (UPDLOCK, HOLDLOCK)
                WHERE staging_record_id = :staging_record_id;
            """),
            {"staging_record_id": staging_record_id},
        ).scalar_one()

        parameters = []

        for sequence, issue in enumerate(
            issue_list,
            start=last_sequence + 1,
        ):
            severity = getattr(
                issue,
                "severity",
                "error",
            ).lower()

            detected_at = (
                issue.detected_at
                if issue.detected_at is not None
                else datetime.now(timezone.utc)
            )

            parameters.append({
                "staging_record_id": staging_record_id,
                "issue_seq": sequence,
                "issue_type": issue.issue_type,
                "field_name": issue.field_name,
                "issue_description": issue.message,
                "is_rejecting": severity in {"error", "critical"},
                "detected_at": _to_utc_naive(detected_at),
            })

        conn.execute(
            insert_statement,
            parameters,
        )

    return len(parameters)


# =========================================================
# PROCESSING METADATA UPDATE
# =========================================================

def update_processing_metadata(
    staging_record_id: int,
    processing_status: Any = UNSET,
    article_id: Any = UNSET,
    story_id: Any = UNSET,
    canonical_url_hash: Any = UNSET,
    title_hash: Any = UNSET,
    content_fingerprint: Any = UNSET,
    publication_timestamp: Any = UNSET,
    timestamp_validity: Any = UNSET,
    standardized_source_name: Any = UNSET,
    standardized_category_name: Any = UNSET,
    is_syndicated: Any = UNSET,
    connection: Optional[Connection] = None,
) -> None:
    """
    Update processing metadata only.

    UNSET:
        Keep the existing database value unchanged.

    None:
        Explicitly set the database value to SQL NULL.

    If connection is supplied, the caller owns the transaction.
    """

    if (
        processing_status is not UNSET
        and processing_status is not None
        and processing_status not in ALLOWED_PROCESSING_STATUSES
    ):
        raise ValueError(
            f"Unsupported processing status: {processing_status}"
        )

    if (
        timestamp_validity is not UNSET
        and timestamp_validity is not None
        and timestamp_validity not in ALLOWED_TIMESTAMP_VALIDITY
    ):
        raise ValueError(
            f"Unsupported timestamp validity: {timestamp_validity}"
        )

    updates = {
        "processing_status": processing_status,
        "article_id": article_id,
        "story_id": story_id,
        "canonical_url_hash": canonical_url_hash,
        "title_hash": title_hash,
        "content_fingerprint": content_fingerprint,
        "publication_timestamp": publication_timestamp,
        "timestamp_validity": timestamp_validity,
        "standardized_source_name": standardized_source_name,
        "standardized_category_name": standardized_category_name,
        "is_syndicated": is_syndicated,
    }

    updates = {
        key: value
        for key, value in updates.items()
        if value is not UNSET
    }

    if not updates:
        return

    if (
        "publication_timestamp" in updates
        and updates["publication_timestamp"] is not None
    ):
        updates["publication_timestamp"] = _to_utc_naive(
            updates["publication_timestamp"]
        )

    set_clause = ", ".join(
        f"{column} = :{column}"
        for column in updates
    )

    statement = text(f"""
        UPDATE dbo.raw_articles
        SET {set_clause}
        WHERE staging_record_id = :staging_record_id;
    """)

    parameters = {
        **updates,
        "staging_record_id": staging_record_id,
    }

    with _connection_scope(connection) as conn:
        result = conn.execute(statement, parameters)

        if result.rowcount == 0:
            raise LookupError(
                f"Staging record {staging_record_id} was not found."
            )


# =========================================================
# EXISTING ARTICLE LOOKUP
# =========================================================

def find_existing_articles(
    source_id: str,
    canonical_url_hash: Optional[str] = None,
    content_fingerprint: Optional[str] = None,
    exclude_staging_record_id: Optional[int] = None,
) -> list[dict]:
    """
    Find eligible previously stored records from the same source.

    Only Stored and Updated records with an assigned article_id
    can be used as historical deduplication references.
    """

    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id cannot be empty.")

    hash_conditions = []
    parameters: dict[str, Any] = {
        "source_id": _normalize_source(source_id),
        "stored_status": ELIGIBLE_EXISTING_STATUSES[0],
        "updated_status": ELIGIBLE_EXISTING_STATUSES[1],
    }

    if canonical_url_hash:
        hash_conditions.append(
            "canonical_url_hash = :canonical_url_hash"
        )
        parameters["canonical_url_hash"] = canonical_url_hash

    if content_fingerprint:
        hash_conditions.append(
            "content_fingerprint = :content_fingerprint"
        )
        parameters["content_fingerprint"] = content_fingerprint

    if not hash_conditions:
        return []

    conditions = [
        "source_id = :source_id",
        "processing_status IN (:stored_status, :updated_status)",
        "article_id IS NOT NULL",
        "(" + " OR ".join(hash_conditions) + ")",
    ]

    if exclude_staging_record_id is not None:
        conditions.append(
            "staging_record_id <> :exclude_staging_record_id"
        )
        parameters["exclude_staging_record_id"] = (
            exclude_staging_record_id
        )

    where_clause = " AND ".join(conditions)

    if canonical_url_hash:
        order_clause = """
            ORDER BY
                CASE
                    WHEN canonical_url_hash = :canonical_url_hash
                    THEN 0
                    ELSE 1
                END,
                ingestion_timestamp DESC,
                staging_record_id DESC
        """
    else:
        order_clause = """
            ORDER BY ingestion_timestamp DESC, staging_record_id DESC
        """

    statement = text(f"""
        SELECT
            staging_record_id,
            run_id,
            source_id,
            canonical_url_hash,
            title_hash,
            content_fingerprint,
            publication_timestamp,
            processing_status,
            article_id,
            ingestion_timestamp
        FROM dbo.raw_articles
        WHERE {where_clause}
        {order_clause};
    """)

    with engine.connect() as connection:
        result = connection.execute(statement, parameters)

        return [
            dict(row._mapping)
            for row in result
        ]


# =========================================================
# STAGING RECORD RETRIEVAL
# =========================================================

def get_article_by_staging_id(
    staging_record_id: int,
) -> Optional[dict]:
    """
    Retrieve one staging record by its generated identifier.
    """

    statement = text("""
        SELECT *
        FROM dbo.raw_articles
        WHERE staging_record_id = :staging_record_id;
    """)

    with engine.connect() as connection:
        result = connection.execute(
            statement,
            {"staging_record_id": staging_record_id},
        )

        row = result.fetchone()

        return dict(row._mapping) if row else None


# =========================================================
# STORY ID READ-BACK VERIFICATION
# =========================================================

def get_story_ids_by_staging_ids(
    staging_record_ids: Iterable[int],
) -> dict[int, Optional[str]]:
    """
    Retrieve persisted Story IDs for multiple staging records.

    Returns:
        {
            staging_record_id: story_id,
            ...
        }

    Records with SQL NULL story_id are included.

    A missing staging record is not included in the returned
    dictionary, allowing the caller to detect missing records.

    This function performs SELECT only and does not modify data.
    """

    ids = list(dict.fromkeys(staging_record_ids))

    if not ids:
        return {}

    if any(
        not isinstance(staging_id, int) or staging_id <= 0
        for staging_id in ids
    ):
        raise ValueError(
            "All staging_record_ids must be positive integers."
        )

    parameters = {
        f"staging_id_{index}": staging_id
        for index, staging_id in enumerate(ids)
    }

    placeholders = ", ".join(
        f":staging_id_{index}"
        for index in range(len(ids))
    )

    statement = text(f"""
        SELECT
            staging_record_id,
            story_id
        FROM dbo.raw_articles
        WHERE staging_record_id IN ({placeholders});
    """)

    with engine.connect() as connection:
        result = connection.execute(
            statement,
            parameters,
        )

        return {
            int(row.staging_record_id): row.story_id
            for row in result
        }