-- Grain: publication_date x category x publisher. Category trends over time (articles with a known publication date only).
-- share_of_source_day_pct = category share of that publishers articles on that day.
with daily as (

    select
        e.publication_date,
        e.category_key,
        e.category_name,
        e.source_id,
        count(*) as article_count
    from {{ ref('int_articles_enriched') }} e
    where e.publication_date is not null
    group by e.publication_date, e.category_key, e.category_name, e.source_id

)

select
    d.publication_date,
    d.category_key,
    d.category_name,
    d.source_id,
    src.source_name,
    d.article_count,
    {{ pct('d.article_count', 'sum(d.article_count) over (partition by d.publication_date, d.source_id)') }} as share_of_source_day_pct
from daily d
left join {{ ref('dim_sources') }} src on src.source_id = d.source_id
