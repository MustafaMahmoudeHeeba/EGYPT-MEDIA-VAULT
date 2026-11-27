from sqlalchemy import text
from sqlalchemy.orm import Session


def get_sources(db: Session):
    query = text("""
        SELECT
            -- Basic Source Information
            s.source_id,
            s.source_key,
            s.source_name,
            s.is_enabled,
            s.is_current_version,
            s.version_effective_from,
            s.version_count,

            -- Source Activity Summary
            summary.total_articles,
            summary.share_of_total_articles_pct,
            summary.activity_rank,
            summary.articles_with_publication_time,
            summary.distinct_categories,
            summary.stories_covered,
            summary.stories_shared_with_other_sources,
            summary.stories_exclusive,
            summary.first_published_at,
            summary.last_published_at,
            summary.last_ingested_at,

            -- Source Collection Reliability
            reliability.collection_runs,
            reliability.successful_collections,
            reliability.failed_collections,
            reliability.success_rate_pct,
            reliability.total_attempts,
            reliability.avg_attempts_per_collection,
            reliability.retried_collections,
            reliability.total_articles_collected,
            reliability.avg_articles_collected_per_run,
            reliability.total_articles_rejected,
            reliability.total_duplicate_records,
            reliability.last_successful_run_date,
            reliability.last_failed_run_date,
            reliability.failures_by_step

        FROM core.dim_sources AS s

        LEFT JOIN analytics.mart_source_summary AS summary
            ON s.source_id = summary.source_id

        LEFT JOIN analytics.mart_source_reliability AS reliability
            ON s.source_id = reliability.source_id

        WHERE s.is_current_version = 1

        ORDER BY
            CASE
                WHEN summary.activity_rank IS NULL THEN 1
                ELSE 0
            END,
            summary.activity_rank,
            s.source_name
    """)

    result = db.execute(query).mappings().all()

    return [dict(row) for row in result]


def get_source_by_id(db: Session, source_id: str):
    query = text("""
        SELECT
            -- Basic Source Information
            s.source_id,
            s.source_key,
            s.source_name,
            s.is_enabled,
            s.is_current_version,
            s.version_effective_from,
            s.version_count,

            -- Source Activity Summary
            summary.total_articles,
            summary.share_of_total_articles_pct,
            summary.activity_rank,
            summary.articles_with_publication_time,
            summary.distinct_categories,
            summary.stories_covered,
            summary.stories_shared_with_other_sources,
            summary.stories_exclusive,
            summary.first_published_at,
            summary.last_published_at,
            summary.last_ingested_at,

            -- Source Collection Reliability
            reliability.collection_runs,
            reliability.successful_collections,
            reliability.failed_collections,
            reliability.success_rate_pct,
            reliability.total_attempts,
            reliability.avg_attempts_per_collection,
            reliability.retried_collections,
            reliability.total_articles_collected,
            reliability.avg_articles_collected_per_run,
            reliability.total_articles_rejected,
            reliability.total_duplicate_records,
            reliability.last_successful_run_date,
            reliability.last_failed_run_date,
            reliability.failures_by_step

        FROM core.dim_sources AS s

        LEFT JOIN analytics.mart_source_summary AS summary
            ON s.source_id = summary.source_id

        LEFT JOIN analytics.mart_source_reliability AS reliability
            ON s.source_id = reliability.source_id

        WHERE
            s.source_id = :source_id
            AND s.is_current_version = 1
    """)

    result = db.execute(
        query,
        {"source_id": source_id},
    ).mappings().first()

    return dict(result) if result else None