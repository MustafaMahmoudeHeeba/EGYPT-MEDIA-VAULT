
import os

from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


DBT_IMAGE = "egypt-media-vault-dbt:1.0"
DBT_WORKING_DIR = "/usr/app/dbt"
DBT_PROFILES_DIR = "/root/.dbt"


def get_dbt_mounts():
    """
    Configure host-to-container bind mounts for the dbt project
    and its read-only profiles file.
    """

    project_path = os.environ.get("DBT_PROJECT_HOST_PATH")
    profiles_path = os.environ.get("DBT_PROFILES_HOST_PATH")

    if not project_path:
        raise ValueError("DBT_PROJECT_HOST_PATH is not configured.")

    if not profiles_path:
        raise ValueError("DBT_PROFILES_HOST_PATH is not configured.")

    return [
        Mount(
            source=project_path,
            target=DBT_WORKING_DIR,
            type="bind",
        ),
        Mount(
            source=profiles_path,
            target=f"{DBT_PROFILES_DIR}/profiles.yml",
            type="bind",
            read_only=True,
        ),
    ]


def get_dbt_environment():
    """
    Retrieve Azure SQL credentials from the Airflow Connection
    at task execution time, without hardcoding secrets in the DAG.
    """

    return {
        "DBT_PROFILES_DIR": DBT_PROFILES_DIR,
        "DBT_SQLSERVER_HOST": "{{ conn.azure_sql_dbt.host }}",
        "DBT_SQLSERVER_DATABASE": "{{ conn.azure_sql_dbt.schema }}",
        "DBT_SQLSERVER_USER": "{{ conn.azure_sql_dbt.login }}",
        "DBT_SQLSERVER_PASSWORD": "{{ conn.azure_sql_dbt.password }}",
        "DBT_SQLSERVER_SCHEMA": "dbt",
        "DBT_SQLSERVER_AUTH": "sql",
    }


def create_dbt_run_task():
    """
    Build all dbt models.
    """

    return DockerOperator(
        task_id="dbt_run",
        image=DBT_IMAGE,
        command="dbt run",
        working_dir=DBT_WORKING_DIR,
        docker_url="unix://var/run/docker.sock",
        mounts=get_dbt_mounts(),
        environment=get_dbt_environment(),
        mount_tmp_dir=False,
        auto_remove="success",
    )


def create_dbt_test_task():
    """
    Execute dbt data quality tests after dbt run succeeds.
    """

    return DockerOperator(
        task_id="dbt_test",
        image=DBT_IMAGE,
        command="dbt test",
        working_dir=DBT_WORKING_DIR,
        docker_url="unix://var/run/docker.sock",
        mounts=get_dbt_mounts(),
        environment=get_dbt_environment(),
        mount_tmp_dir=False,
        auto_remove="success",
    )
