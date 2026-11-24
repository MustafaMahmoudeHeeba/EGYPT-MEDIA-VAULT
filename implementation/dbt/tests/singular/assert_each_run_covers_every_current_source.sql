-- WARN. Each run should have exactly one collection row per distinct source, and cover every current, enabled source.
-- Runs that pre-date a newly added source will warn; that is informative, not an error.
{{ config(severity='warn') }}
select
    r.run_id,
    count(*) as source_rows,
    count(distinct r.source_id) as distinct_sources
from {{ ref('int_source_collection_enriched') }} r
group by r.run_id
having count(*) <> count(distinct r.source_id)
    or count(distinct r.source_id) <> (
        select count(distinct s.source_id)
        from {{ ref('stg_dim_source') }} s
        where s.is_current = 1 and s.enabled_status = 1
    )
