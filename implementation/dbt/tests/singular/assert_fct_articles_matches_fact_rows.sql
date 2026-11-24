-- ERROR. The article mart must neither lose nor duplicate articles relative to the warehouse fact.
select m.mart_rows, f.fact_rows
from (select count(*) as mart_rows from {{ ref('fct_articles') }}) m
cross join (select count(*) as fact_rows from {{ ref('stg_fact_news_articles') }}) f
where m.mart_rows <> f.fact_rows
