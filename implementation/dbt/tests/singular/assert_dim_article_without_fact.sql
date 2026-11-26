-- WARN. dim_article rows with no fact_news_articles row.
-- The warehouse integrity check currently reports exactly 1 such row (dim_article_without_fact = 1). It is surfaced here, never hidden;
-- run this test with --store-failures or copy the query into SSMS to see which article it is.
{{ config(severity='warn') }}
select a.article_key, a.article_id, a.article_title, a.warehouse_created_at, a.warehouse_updated_at
from {{ ref('stg_dim_article') }} a
left join {{ ref('stg_fact_news_articles') }} f on f.article_key = a.article_key
where f.article_key is null
