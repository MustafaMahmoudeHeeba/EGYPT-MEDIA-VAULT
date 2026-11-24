-- Grain: category x publisher, all articles (including those without a publication timestamp).
-- Answers: articles by category, categories by source, category distribution per source.
with counts as (

    select
        e.category_key,
        e.category_name,
        e.source_id,
        count(*) as article_count
    from {{ ref('int_articles_enriched') }} e
    group by e.category_key, e.category_name, e.source_id

)

select
    c.category_key,
    c.category_name,
    c.source_id,
    src.source_name,
    c.article_count,
    {{ pct('c.article_count', 'sum(c.article_count) over (partition by c.source_id)') }} as share_of_source_pct,
    sum(c.article_count) over (partition by c.category_key) as category_total_articles,
    {{ pct('c.article_count', 'sum(c.article_count) over (partition by c.category_key)') }} as source_share_of_category_pct
from counts c
left join {{ ref('dim_sources') }} src on src.source_id = c.source_id
