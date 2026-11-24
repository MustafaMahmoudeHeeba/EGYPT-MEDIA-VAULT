-- Grain: ACTIVE story x publisher. Compares publication times across publishers of the same story.
--   minutes_after_story_first_publication  how long after the storys earliest article this publisher first published (0 for the first)
--   publication_order                      1 = first publisher; publishers without a timestamp are ranked last
--   is_first_source                        1 only for the publisher of the earliest timestamped article
-- Publisher times stay at article/source level: first/last per publisher plus article_count for that publisher.
with active_stories as (

    select
        s.story_key,
        s.story_id,
        s.story_title,
        s.source_count,
        s.first_published_at as story_first_published_at
    from {{ ref('dim_stories') }} s
    where s.story_membership_status = 'active'

),

timeline as (

    select
        a.story_id,
        a.story_key,
        a.story_title,
        a.source_count,
        cv.source_id,
        src.source_name,
        cv.article_count,
        cv.articles_missing_publication_time,
        cv.first_published_at,
        cv.last_published_at,
        a.story_first_published_at,
        row_number() over (
            partition by a.story_key
            order by case when cv.first_published_at is null then 1 else 0 end, cv.first_published_at, cv.source_id
        ) as publication_order
    from active_stories a
    join {{ ref('int_story_source_coverage') }} cv on cv.story_key = a.story_key
    left join {{ ref('dim_sources') }} src on src.source_id = cv.source_id

)

select
    t.story_id,
    t.story_key,
    t.story_title,
    t.source_id,
    t.source_name,
    t.source_count as story_source_count,
    t.article_count,
    t.articles_missing_publication_time,
    t.first_published_at,
    t.last_published_at,
    t.story_first_published_at,
    {{ minutes_between('t.story_first_published_at', 't.first_published_at') }} as minutes_after_story_first_publication,
    t.publication_order,
    cast(case when t.publication_order = 1 and t.first_published_at is not null then 1 else 0 end as bit) as is_first_source
from timeline t
