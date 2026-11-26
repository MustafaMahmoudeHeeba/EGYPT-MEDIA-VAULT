-- MAIN KPI. Grain: one row per ACTIVE story (stories with >= 1 article; the UNKNOWN sentinel and empty stories are excluded).
-- Cross-publisher coverage, driven by the Story ID relationship (never title matching):
--   article_count        number of articles in the story
--   source_count         number of DISTINCT publishers (not inflated by several articles from one site)
--   publisher_ids/names  publishers ordered by when each first published (earliest first)
--   first/last_published_at   earliest / latest publication timestamp across all articles of the story
--   coverage_gap_minutes      minutes between first_published_at and last_published_at (NULL if no timestamps)
--   first_source_*       publisher of the earliest article (tie -> alphabetically first source_id); NULL if no timestamps
-- Per-publisher times are in mart_story_source_timeline.
with stories as (

    select
        s.story_key,
        s.story_id,
        s.story_title,
        s.article_count,
        s.source_count,
        s.articles_missing_publication_time,
        s.first_published_at,
        s.last_published_at
    from {{ ref('dim_stories') }} s
    where s.story_membership_status = 'active'

),

ordered_sources as (

    select
        cv.story_key,
        cv.source_id,
        cv.first_published_at,
        row_number() over (
            partition by cv.story_key
            order by case when cv.first_published_at is null then 1 else 0 end, cv.first_published_at, cv.source_id
        ) as publish_order
    from {{ ref('int_story_source_coverage') }} cv

),

publishers as (

    select
        o.story_key,
        string_agg(cast(o.source_id as nvarchar(100)), ', ') within group (order by o.publish_order) as publisher_ids,
        string_agg(cast(src.source_name as nvarchar(255)), ', ') within group (order by o.publish_order) as publisher_names
    from ordered_sources o
    left join {{ ref('dim_sources') }} src on src.source_id = o.source_id
    group by o.story_key

),

first_source as (

    select
        o.story_key,
        o.source_id as first_source_id,
        src.source_name as first_source_name
    from ordered_sources o
    left join {{ ref('dim_sources') }} src on src.source_id = o.source_id
    where o.publish_order = 1
      and o.first_published_at is not null

)

select
    s.story_id,
    s.story_key,
    s.story_title,
    s.article_count,
    s.source_count,
    {{ flag_to_bit('s.source_count > 1') }} as is_multi_source,
    p.publisher_ids,
    p.publisher_names,
    s.first_published_at,
    s.last_published_at,
    {{ minutes_between('s.first_published_at', 's.last_published_at') }} as coverage_gap_minutes,
    fs.first_source_id,
    fs.first_source_name,
    s.articles_missing_publication_time,
    dense_rank() over (order by s.source_count desc, s.article_count desc) as coverage_rank
from stories s
left join publishers p on p.story_key = s.story_key
left join first_source fs on fs.story_key = s.story_key
