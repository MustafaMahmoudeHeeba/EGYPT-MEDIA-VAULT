
from azure.core.exceptions import AzureError

from pipeline.egypt_media_vault.storage.adls_client import (
    AzureDataLakeStorage,
)


def main():
    storage = None

    try:
        print("=" * 55)
        print("AZURE DATA LAKE CONNECTION TEST")
        print("=" * 55)

        storage = AzureDataLakeStorage()

        print("\nConnection established successfully!")

        paths = storage.list_paths()

        print(f"\nTotal paths found: {len(paths)}")

        for path in paths:
            item_type = (
                "Directory" if path.is_directory else "File"
            )

            print(f"[{item_type}] {path.name}")

        print("\nAzure Data Lake connection test completed.")

    except (AzureError, ValueError) as error:
        print(f"\nAzure Data Lake connection failed: {error}")
        raise

    finally:
        if storage is not None:
            storage.close()


if __name__ == "__main__":
    main()
