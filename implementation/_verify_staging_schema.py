from sqlalchemy import text
from pipeline.egypt_media_vault.warehouse.database import engine

expected = {
    "raw_articles": {
        "run_id", "source_id", "raw_title", "raw_source_name",
        "original_url", "canonical_url", "raw_publication_text",
        "raw_category_label", "raw_description", "raw_content",
        "raw_author", "raw_update_text", "title_hash",
        "publication_timestamp", "timestamp_validity",
        "standardized_source_name", "standardized_category_name",
        "processing_status", "staging_record_id",
    },
    "raw_article_issues": {
        "staging_record_id", "issue_seq", "issue_type",
        "field_name", "issue_description", "is_rejecting",
        "detected_at",
    },
}

with engine.connect() as connection:
    for table, required_columns in expected.items():
        print(f"\n========== dbo.{table} ==========")

        rows = connection.execute(
            text("""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """),
            {"table_name": table},
        ).mappings().all()

        actual_columns = {row["COLUMN_NAME"] for row in rows}

        for row in rows:
            length = row["CHARACTER_MAXIMUM_LENGTH"]
            length_text = f"({length})" if length is not None else ""
            print(
                f'{row["COLUMN_NAME"]:<35} '
                f'{row["DATA_TYPE"]}{length_text:<12} '
                f'NULL={row["IS_NULLABLE"]}'
            )

        missing = required_columns - actual_columns

        if missing:
            print("\nSCHEMA CHECK: FAILED")
            print("Missing columns:", sorted(missing))
        else:
            print("\nSCHEMA CHECK: PASSED")

engine.dispose()
