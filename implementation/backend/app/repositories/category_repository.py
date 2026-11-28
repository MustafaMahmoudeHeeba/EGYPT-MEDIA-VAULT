from sqlalchemy import text
from sqlalchemy.orm import Session


def get_categories(db: Session):
    query = text("""
        WITH CategorySummary AS (
            SELECT
                category_key,
                MAX(category_total_articles) AS total_articles,
                COUNT(DISTINCT source_id) AS source_count
            FROM analytics.mart_category_summary
            GROUP BY category_key
        ),
        RankedCategories AS (
            SELECT
                category_key,
                total_articles,
                source_count,
                RANK() OVER (
                    ORDER BY total_articles DESC
                ) AS activity_rank
            FROM CategorySummary
        )
        SELECT
            c.category_key,
            c.category_name,
            COALESCE(rc.total_articles, 0) AS total_articles,
            COALESCE(rc.source_count, 0) AS source_count,
            rc.activity_rank
        FROM dbo.dim_category AS c
        LEFT JOIN RankedCategories AS rc
            ON c.category_key = rc.category_key
        ORDER BY
            CASE WHEN rc.activity_rank IS NULL THEN 1 ELSE 0 END,
            rc.activity_rank,
            c.category_name
    """)

    categories = db.execute(query).mappings().all()

    results = []

    for category in categories:
        category_data = dict(category)

        category_data["sources"] = get_category_sources(
            db,
            category_data["category_key"],
        )

        results.append(category_data)

    return results


def get_category_sources(db: Session, category_key: int):
    query = text("""
        SELECT
            source_id,
            source_name,
            article_count,
            share_of_source_pct,
            source_share_of_category_pct
        FROM analytics.mart_category_summary
        WHERE category_key = :category_key
        ORDER BY article_count DESC, source_name
    """)

    result = db.execute(
        query,
        {"category_key": category_key},
    ).mappings().all()

    return [dict(row) for row in result]


def get_category_by_id(db: Session, category_key: int):
    query = text("""
        WITH CategorySummary AS (
            SELECT
                category_key,
                MAX(category_total_articles) AS total_articles,
                COUNT(DISTINCT source_id) AS source_count
            FROM analytics.mart_category_summary
            GROUP BY category_key
        ),
        RankedCategories AS (
            SELECT
                category_key,
                total_articles,
                source_count,
                RANK() OVER (
                    ORDER BY total_articles DESC
                ) AS activity_rank
            FROM CategorySummary
        )
        SELECT
            c.category_key,
            c.category_name,
            COALESCE(rc.total_articles, 0) AS total_articles,
            COALESCE(rc.source_count, 0) AS source_count,
            rc.activity_rank
        FROM dbo.dim_category AS c
        LEFT JOIN RankedCategories AS rc
            ON c.category_key = rc.category_key
        WHERE c.category_key = :category_key
    """)

    category = db.execute(
        query,
        {"category_key": category_key},
    ).mappings().first()

    if category is None:
        return None

    category_data = dict(category)

    category_data["sources"] = get_category_sources(
        db,
        category_key,
    )

    return category_data