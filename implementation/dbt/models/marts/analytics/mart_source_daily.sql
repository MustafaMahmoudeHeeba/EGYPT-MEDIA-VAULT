-- Grain: publication_date x publisher. Publication trends per source (articles with a known publication date only).
-- share_of_date_pct = the publishers share of that days articles; activity_rank_on_date = 1 for the most active publisher that day;
-- cumulative_articles = running total per publisher.
with daily as (

    select
        e.publication_date,
        e.source_id,
        count(*) as article_count,
        count(distinct e.story_id) as story_count,
        count(distinct e.category_key) as category_count
    from {{ ref('int_articles_enriched') }} e
    where e.publication_date is not null
    group by e.publication_date, e.source_id

)

select
    d.publication_date,
    d.source_id,
    src.source_name,
    d.article_count,
    d.story_count,
    d.category_count,
    sum(d.article_count) over (partition by d.publication_date) as total_articles_on_date,
    {{ pct('d.article_count', 'sum(d.article_count) over (partition by d.publication_date)') }} as share_of_date_pct,
    rank() over (partition by d.publication_date order by d.article_count desc) as activity_rank_on_date,
    sum(d.article_count) over (partition by d.source_id order by d.publication_date rows unbounded preceding) as cumulative_articles
from daily d
left join {{ ref('dim_sources') }} src on src.source_id = d.source_id
