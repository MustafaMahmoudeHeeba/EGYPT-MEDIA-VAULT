-- One row per publisher (source_id), described by its current version (or, if none is flagged current,
-- the most recent version). source_key here is that versions surrogate key and is informational only:
-- join to facts through source_id.
with ranked as (

    select
        s.source_id,
        s.source_key,
        s.source_name,
        s.enabled_status,
        s.version_effective_from,
        s.is_current,
        row_number() over (
            partition by s.source_id
            order by s.is_current desc, s.version_effective_from desc, s.source_key desc
        ) as version_rank,
        count(*) over (partition by s.source_id) as version_count
    from {{ ref('stg_dim_source') }} s

)

select
    r.source_id,
    r.source_key,
    r.source_name,
    r.enabled_status as is_enabled,
    r.is_current as is_current_version,
    r.version_effective_from,
    r.version_count
from ranked r
where r.version_rank = 1
