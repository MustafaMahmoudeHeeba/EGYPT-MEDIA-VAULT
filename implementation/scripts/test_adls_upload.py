
from pipeline.egypt_media_vault.storage.adls_client import (
    AzureDataLakeStorage,
)


def main():
    storage = AzureDataLakeStorage()

    test_article = {
        "title": "Azure Data Lake Upload Test",
        "source": "EGYPT-MEDIA-VAULT",
        "category": "Technology",
        "content": "This is a test article stored in Bronze.",
        "status": "upload_success"
    }

    try:
        uploaded_path = storage.upload_json(
            directory="bronze",
            filename="test_upload.json",
            data=test_article,
        )

        print("Upload completed successfully!")
        print(f"Uploaded file: {uploaded_path}")

    finally:
        storage.close()


if __name__ == "__main__":
    main()
