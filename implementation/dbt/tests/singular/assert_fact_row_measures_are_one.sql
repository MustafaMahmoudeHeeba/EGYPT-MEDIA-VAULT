-- WARN. fact_news_articles.article_count and fact_pipeline_run.run_count are row-level measures expected to be 1.
-- Story-level article counts in this project use COUNT(*) of rows, so these columns are never summed.
{{ config(severity='warn') }}
select 'fact_news_articles' as fact_table, cast(article_key as nvarchar(100)) as row_key, article_count as measure_value
from {{ ref('stg_fact_news_articles') }}
where article_count <> 1
union all
select 'fact_pipeline_run', run_id, run_count
from {{ ref('stg_fact_pipeline_run') }}
where run_count <> 1
