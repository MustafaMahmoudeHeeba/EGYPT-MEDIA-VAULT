-- Diagnostic (compiled by dbt, never materialized): the dim_article row(s) with no fact_news_articles row.
-- The warehouse integrity check reports dim_article_without_fact = 1. Compare warehouse_created_at with your run times:
-- a row created at the very start of a run suggests a dimension load whose fact load did not complete or was rolled back.
select
    a.article_key,
    a.article_id,
    a.article_title,
    a.original_url,
    a.link_availability,
    a.warehouse_created_at,
    a.warehouse_updated_at
from {{ ref('stg_dim_article') }} a
left join {{ ref('stg_fact_news_articles') }} f on f.article_key = a.article_key
where f.article_key is null
order by a.warehouse_created_at
