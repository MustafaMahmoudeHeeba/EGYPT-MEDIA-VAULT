-- ERROR. dim_stories.article_count must equal the number of fact_news_articles rows pointing at the story
-- (stories without rows must show 0). Counted from the staging view, independent of the intermediate models.
select
    s.story_key,
    s.story_id,
    s.article_count,
    coalesce(x.fact_rows, 0) as fact_rows
from {{ ref('dim_stories') }} s
left join (
    select story_key, count(*) as fact_rows
    from {{ ref('stg_fact_news_articles') }}
    group by story_key
) x on x.story_key = s.story_key
where s.article_count <> coalesce(x.fact_rows, 0)
