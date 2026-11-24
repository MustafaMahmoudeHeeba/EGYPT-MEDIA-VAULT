-- Grain: run x source (one row per fact_source_collection row) with run status, outcome, source and run date attached.
-- Shared by the pipeline marts so outcome logic is defined once.
select
    sc.run_id,
    sc.source_key,
    src.source_id,
    src.source_name,
    sc.run_date_key,
    d.full_date as run_date,
    rs.run_status,
    co.collection_outcome,
    co.failed_step,
    {{ flag_to_bit('lower(co.collection_outcome) = ' ~ var_label('success_outcome_label')) }} as is_successful_collection,
    sc.attempt_count,
    {{ flag_to_bit('sc.attempt_count > 1') }} as is_retried,
    sc.articles_collected_count,
    sc.articles_rejected_count,
    sc.duplicate_record_count,
    sc.error_description,
    pr.scheduled_timestamp,
    pr.start_timestamp,
    pr.end_timestamp
from {{ ref('stg_fact_source_collection') }} sc
left join {{ ref('stg_fact_pipeline_run') }} pr on pr.run_id = sc.run_id
left join {{ ref('stg_dim_run_status') }} rs on rs.run_status_key = pr.run_status_key
left join {{ ref('stg_dim_collection_outcome') }} co on co.collection_outcome_key = sc.collection_outcome_key
left join {{ ref('stg_dim_source') }} src on src.source_key = sc.source_key
left join {{ ref('stg_dim_date') }} d on d.date_key = sc.run_date_key
