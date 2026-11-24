-- Grain: publisher. Collection reliability across all runs.
--   success_rate_pct = successful collections / collection runs. A collection is successful when its outcome equals
--   var(success_outcome_label) (case-insensitive). With only a few runs the rate is indicative, not statistically meaningful.
--   failures_by_step = e.g. "Scrape: 2; Validate: 1" (NULL when there were no failures)
with agg as (

    select
        c.source_id,
        count(*) as collection_runs,
        sum(case when c.is_successful_collection = 1 then 1 else 0 end) as successful_collections,
        sum(c.attempt_count) as total_attempts,
        sum(case when c.attempt_count > 1 then 1 else 0 end) as retried_collections,
        sum(coalesce(c.articles_collected_count, 0)) as total_articles_collected,
        sum(c.articles_rejected_count) as total_articles_rejected,
        sum(c.duplicate_record_count) as total_duplicate_records,
        max(case when c.is_successful_collection = 1 then c.run_date end) as last_successful_run_date,
        max(case when c.is_successful_collection = 0 then c.run_date end) as last_failed_run_date
    from {{ ref('int_source_collection_enriched') }} c
    group by c.source_id

),

failures as (

    select
        c.source_id,
        c.failed_step,
        count(*) as failure_count
    from {{ ref('int_source_collection_enriched') }} c
    where c.is_successful_collection = 0
    group by c.source_id, c.failed_step

),

failure_text as (

    select
        f.source_id,
        string_agg(cast(concat(f.failed_step, ': ', f.failure_count) as nvarchar(400)), '; ')
            within group (order by f.failure_count desc, f.failed_step) as failures_by_step
    from failures f
    group by f.source_id

)

select
    a.source_id,
    src.source_name,
    a.collection_runs,
    a.successful_collections,
    a.collection_runs - a.successful_collections as failed_collections,
    {{ pct('a.successful_collections', 'a.collection_runs') }} as success_rate_pct,
    a.total_attempts,
    cast(1.0 * a.total_attempts / nullif(a.collection_runs, 0) as decimal(10, 2)) as avg_attempts_per_collection,
    a.retried_collections,
    a.total_articles_collected,
    cast(1.0 * a.total_articles_collected / nullif(a.collection_runs, 0) as decimal(18, 2)) as avg_articles_collected_per_run,
    a.total_articles_rejected,
    a.total_duplicate_records,
    a.last_successful_run_date,
    a.last_failed_run_date,
    ft.failures_by_step
from agg a
left join {{ ref('dim_sources') }} src on src.source_id = a.source_id
left join failure_text ft on ft.source_id = a.source_id
