"""
Bronze and Silver uploads to Azure Data Lake Storage, plus the JSON
serializers they use.
"""

from dataclasses import asdict
from datetime import datetime, timezone

from pipeline.egypt_media_vault.storage.adls_client import (
    AzureDataLakeStorage,
)

from pipeline.egypt_media_vault.orchestration.display import print_section
from pipeline.egypt_media_vault.orchestration.models import PipelineResults


def serialize_raw_article(raw_article) -> dict:
    article_data = asdict(raw_article)

    for field_name, value in article_data.items():
        if isinstance(value, datetime):
            article_data[field_name] = value.isoformat()

    return article_data


def serialize_article(article) -> dict:
    article_data = asdict(article)

    for field_name, value in article_data.items():
        if isinstance(value, datetime):
            article_data[field_name] = value.isoformat()

    return article_data


def run_bronze_storage(results: PipelineResults) -> None:
    print_section("BRONZE: AZURE DATA LAKE STORAGE")

    if not results.raw_articles:
        print("No raw articles available for Bronze storage.")
        return

    storage = None

    try:
        if not results.run_id:
            raise ValueError("Pipeline run ID is missing.")

        print("Connecting to Azure Data Lake Storage...")

        storage = AzureDataLakeStorage()

        ingestion_time = datetime.now(timezone.utc)

        payload = {
            "metadata": {
                "project": "EGYPT-MEDIA-VAULT",
                "layer": "bronze",
                "run_id": results.run_id,
                "ingested_at": ingestion_time.isoformat(),
                "total_articles": len(results.raw_articles),
            },
            "articles": [
                serialize_raw_article(article)
                for article in results.raw_articles
            ],
        }

        filename = f"raw_articles_{results.run_id}.json"

        uploaded_path = storage.upload_json(
            directory="bronze",
            filename=filename,
            data=payload,
        )

        results.bronze_file = uploaded_path

        print("\nBronze upload completed successfully!")
        print(f"Uploaded file: {uploaded_path}")
        print(f"Articles stored: {len(results.raw_articles)}")

    except Exception as exc:
        error_message = (
            f"Bronze storage failed: "
            f"{type(exc).__name__}: {exc}"
        )

        results.storage_errors.append(error_message)

        print("\nBRONZE STORAGE FAILED")
        print(f"Reason: {exc}")

    finally:
        if storage is not None:
            try:
                storage.close()
            except Exception as exc:
                error_message = (
                    f"Azure storage client closing failed: "
                    f"{type(exc).__name__}: {exc}"
                )

                results.storage_errors.append(error_message)
                print(error_message)


def run_silver_storage(results: PipelineResults) -> None:
    print_section("SILVER: AZURE DATA LAKE STORAGE")

    if not results.unique_articles:
        print("No unique articles available for Silver storage.")
        return

    storage = None

    try:
        if not results.run_id:
            raise ValueError("Pipeline run ID is missing.")

        print("Connecting to Azure Data Lake Storage...")

        storage = AzureDataLakeStorage()

        ingestion_time = datetime.now(timezone.utc)

        total_sources = len({
            article.source
            for article in results.unique_articles
        })

        payload = {
            "metadata": {
                "project": "EGYPT-MEDIA-VAULT",
                "layer": "silver",
                "run_id": results.run_id,
                "ingested_at": ingestion_time.isoformat(),
                "total_articles": len(results.unique_articles),
                "total_clusters": len(results.clusters),
                "total_sources": total_sources,
            },
            "articles": [
                serialize_article(article)
                for article in results.unique_articles
            ],
        }

        filename = f"cleaned_articles_{results.run_id}.json"

        uploaded_path = storage.upload_json(
            directory="silver",
            filename=filename,
            data=payload,
        )

        results.silver_file = uploaded_path

        print("\nSilver upload completed successfully!")
        print(f"Uploaded file: {uploaded_path}")
        print(f"Articles stored: {len(results.unique_articles)}")
        print(f"Clusters included: {len(results.clusters)}")
        print(f"Sources represented: {total_sources}")

    except Exception as exc:
        error_message = (
            f"Silver storage failed: "
            f"{type(exc).__name__}: {exc}"
        )

        results.storage_errors.append(error_message)

        print("\nSILVER STORAGE FAILED")
        print(f"Reason: {exc}")

    finally:
        if storage is not None:
            try:
                storage.close()
            except Exception as exc:
                error_message = (
                    f"Azure storage client closing failed: "
                    f"{type(exc).__name__}: {exc}"
                )

                results.storage_errors.append(error_message)
                print(error_message)
