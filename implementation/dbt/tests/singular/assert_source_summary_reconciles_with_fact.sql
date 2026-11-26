-- ERROR. Total articles across publishers in the summary must equal the rows of fact_news_articles.
select s.summary_articles, f.fact_articles
from (select coalesce(sum(total_articles), 0) as summary_articles from {{ ref('mart_source_summary') }}) s
cross join (select count(*) as fact_articles from {{ ref('stg_fact_news_articles') }}) f
where s.summary_articles <> f.fact_articles
