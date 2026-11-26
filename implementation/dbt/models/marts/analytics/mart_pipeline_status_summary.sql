-- Grain: run status. Run counts and share per status (Success / Partial / Failed / ... as recorded in dim_run_status),
-- with average duration (runs lacking valid start/end are ignored by the average) and article totals.
select
    p.run_status,
    count(*) as run_count,
    {{ pct('count(*)', 'sum(count(*)) over ()') }} as share_of_runs_pct,
    cast(avg(p.duration_minutes) as decimal(18, 2)) as avg_duration_minutes,
    sum(p.articles_collected_total) as articles_collected_total,
    sum(p.articles_rejected_total) as articles_rejected_total,
    sum(p.duplicate_records_total) as duplicate_records_total,
    min(p.start_timestamp) as first_run_started_at,
    max(p.start_timestamp) as last_run_started_at
from {{ ref('mart_pipeline_runs') }} p
group by p.run_status
