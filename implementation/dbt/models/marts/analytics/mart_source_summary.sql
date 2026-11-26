-- Grain: publisher (source_id). All-time totals, including articles without a publication timestamp.
-- Answers: total articles per source, source contribution to overall coverage, most active sources.
-- stories_shared_with_other_sources counts ACTIVE stories this publisher covers together with at least one other publisher.
with per_source as (

    select
        e.source_id,
        count(*) as total_articles,
        count(e.publication_timestamp) as articles_with_publication_time,
        count(distinct e.category_key) as distinct_categories,
        min(e.publication_timestamp) as first_published_at,
        max(e.publication_timestamp) as last_published_at,
        max(e.ingestion_timestamp) as last_ingested_at
    from {{ ref('int_articles_enriched') }} e
    group by e.source_id

),

stories_per_source as (

    select
        cv.source_id,
        count(*) as stories_covered,
        sum(case when s.source_count > 1 then 1 else 0 end) as stories_shared_with_other_sources,
        sum(case when s.source_count = 1 then 1 else 0 end) as stories_exclusive
    from {{ ref('int_story_source_coverage') }} cv
    join {{ ref('dim_stories') }} s on s.story_key = cv.story_key
    where s.story_membership_status = 'active'
    group by cv.source_id

)

select
    p.source_id,
    src.source_name,
    p.total_articles,
    {{ pct('p.total_articles', 'sum(p.total_articles) over ()') }} as share_of_total_articles_pct,
    rank() over (order by p.total_articles desc) as activity_rank,
    p.articles_with_publication_time,
    p.distinct_categories,
    coalesce(sp.stories_covered, 0) as stories_covered,
    coalesce(sp.stories_shared_with_other_sources, 0) as stories_shared_with_other_sources,
    coalesce(sp.stories_exclusive, 0) as stories_exclusive,
    p.first_published_at,
    p.last_published_at,
    p.last_ingested_at
from per_source p
left join {{ ref('dim_sources') }} src on src.source_id = p.source_id
left join stories_per_source sp on sp.source_id = p.source_id
