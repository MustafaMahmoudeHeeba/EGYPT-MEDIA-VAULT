-- Grain: one row per pipeline run. Run status, duration and collection totals.
--   duration_seconds/minutes  only when start and end exist and end >= start; otherwise NULL (never guessed)
--   is_missed                 the pipeline recorded a missed_reason
--   articles_*_total          summed over the runs source rows (a NULL collected count counts as 0 and is tallied in
--                             sources_with_unknown_collected_count)
-- Runs without any fact_source_collection rows are kept, with zero totals.
with collection as (

    select
        c.run_id,
        count(*) as sources_attempted,
        sum(case when c.is_successful_collection = 1 then 1 else 0 end) as sources_succeeded,
        sum(c.attempt_count) as total_collection_attempts,
        sum(coalesce(c.articles_collected_count, 0)) as articles_collected_total,
        sum(c.articles_rejected_count) as articles_rejected_total,
        sum(c.duplicate_record_count) as duplicate_records_total,
        sum(case when c.articles_collected_count is null then 1 else 0 end) as sources_with_unknown_collected_count
    from {{ ref('int_source_collection_enriched') }} c
    group by c.run_id

)

select
    r.run_id,
    r.run_date,
    r.run_status,
    r.status_definition,
    {{ flag_to_bit('lower(r.run_status) = ' ~ var_label('success_run_status_label')) }} as is_successful_run,
    {{ flag_to_bit('r.missed_reason is not null') }} as is_missed,
    r.missed_reason,
    r.scheduled_timestamp,
    r.start_timestamp,
    r.end_timestamp,
    case when r.start_timestamp is not null and r.end_timestamp is not null and r.end_timestamp >= r.start_timestamp
         then datediff_big(second, r.start_timestamp, r.end_timestamp) end as duration_seconds,
    case when r.start_timestamp is not null and r.end_timestamp is not null and r.end_timestamp >= r.start_timestamp
         then {{ minutes_between('r.start_timestamp', 'r.end_timestamp') }} end as duration_minutes,
    coalesce(c.sources_attempted, 0) as sources_attempted,
    coalesce(c.sources_succeeded, 0) as sources_succeeded,
    coalesce(c.sources_attempted, 0) - coalesce(c.sources_succeeded, 0) as sources_failed,
    coalesce(c.total_collection_attempts, 0) as total_collection_attempts,
    coalesce(c.articles_collected_total, 0) as articles_collected_total,
    coalesce(c.articles_rejected_total, 0) as articles_rejected_total,
    coalesce(c.duplicate_records_total, 0) as duplicate_records_total,
    coalesce(c.sources_with_unknown_collected_count, 0) as sources_with_unknown_collected_count
from {{ ref('int_pipeline_runs_enriched') }} r
left join collection c on c.run_id = r.run_id
