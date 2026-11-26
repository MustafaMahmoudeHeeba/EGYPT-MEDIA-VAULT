-- Grain: one row per pipeline run (fact_pipeline_run) with run status and run date attached.
-- Kept in the intermediate layer so the pipeline marts never read staging directly.
select
    pr.run_id,
    pr.run_date_key,
    d.full_date as run_date,
    rs.run_status,
    rs.status_definition,
    pr.run_count,
    pr.scheduled_timestamp,
    pr.start_timestamp,
    pr.end_timestamp,
    pr.missed_reason
from {{ ref('stg_fact_pipeline_run') }} pr
left join {{ ref('stg_dim_run_status') }} rs on rs.run_status_key = pr.run_status_key
left join {{ ref('stg_dim_date') }} d on d.date_key = pr.run_date_key
