
import json

from azure.storage.filedatalake import DataLakeServiceClient

from pipeline.egypt_media_vault.config.settings import settings


class AzureDataLakeStorage:
    """Client for Azure Data Lake Storage Gen2."""

    def __init__(self):
        account_name = settings.azure_storage_account_name
        account_key = settings.azure_storage_account_key
        container_name = settings.azure_storage_container_name

        if not account_name or not account_key or not container_name:
            raise ValueError(
                "Azure Storage configuration is incomplete."
            )

        account_url = (
            f"https://{account_name}.dfs.core.windows.net"
        )

        self.service_client = DataLakeServiceClient(
            account_url=account_url,
            credential=account_key,
        )

        self.file_system_client = (
            self.service_client.get_file_system_client(
                file_system=container_name
            )
        )

    def list_paths(self):
        return list(self.file_system_client.get_paths())

    def upload_json(self, directory: str, filename: str, data: dict):
        """Upload a JSON document to a Data Lake directory."""

        directory_client = (
            self.file_system_client.get_directory_client(directory)
        )

        file_client = directory_client.get_file_client(filename)

        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=4,
        )

        file_client.upload_data(
            content.encode("utf-8"),
            overwrite=True,
        )

        return f"{directory}/{filename}"

    def close(self):
        self.service_client.close()
