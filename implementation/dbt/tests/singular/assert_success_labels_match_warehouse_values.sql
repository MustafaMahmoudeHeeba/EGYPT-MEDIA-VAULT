-- WARN. Detects a wrong success label: rows exist but none matches var(success_outcome_label) / var(success_run_status_label).
-- If this fires, set the vars in dbt_project.yml to the exact words stored in dim_collection_outcome / dim_run_status.
{{ config(severity='error') }}
select 'success_outcome_label matches no collection outcome' as issue
where exists (select 1 from {{ ref('int_source_collection_enriched') }})
  and not exists (select 1 from {{ ref('int_source_collection_enriched') }} where is_successful_collection = 1)
union all
select 'success_run_status_label matches no run status'
where exists (select 1 from {{ ref('mart_pipeline_runs') }})
  and not exists (select 1 from {{ ref('mart_pipeline_runs') }} where is_successful_run = 1)
