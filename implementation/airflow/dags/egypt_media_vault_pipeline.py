"""
Egypt Media Vault - Production Pipeline.
Airflow DAG scheduled every 30 minutes.
"""

from egypt_media_vault.dag_factory import build_pipeline_dag

dag = build_pipeline_dag(
    dag_id="egypt_media_vault_pipeline",
    schedule="*/15 * * * *",
)