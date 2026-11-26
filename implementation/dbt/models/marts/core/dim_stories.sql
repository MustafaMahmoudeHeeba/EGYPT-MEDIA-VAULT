-- One row per dim_story row (nothing is dropped), enriched with article/source counts and a membership status:
--   active           : the story has at least one article row            -> used by every story KPI
--   no_articles      : the story exists in dim_story but no article row points at it (stale/orphaned/pre-registered)
--   unknown_sentinel : the pipelines UNKNOWN placeholder story         -> never a real story
-- article_count  = number of article rows in the story
-- source_count   = number of DISTINCT publishers (source_id), computed from int_story_source_coverage
with coverage as (

    select
        cv.story_key,
        sum(cv.article_count) as article_count,
        count(*) as source_count,
        sum(cv.articles_missing_publication_time) as articles_missing_publication_time,
        min(cv.first_published_at) as first_published_at,
        max(cv.last_published_at) as last_published_at
    from {{ ref('int_story_source_coverage') }} cv
    group by cv.story_key

)

select
    st.story_key,
    st.story_id,
    st.representative_title as story_title,
    coalesce(cov.article_count, 0) as article_count,
    coalesce(cov.source_count, 0) as source_count,
    coalesce(cov.articles_missing_publication_time, 0) as articles_missing_publication_time,
    cov.first_published_at,
    cov.last_published_at,
    cast(
        case
            when upper(st.story_id) = upper('{{ var("unknown_story_id") }}') then 'unknown_sentinel'
            when coalesce(cov.article_count, 0) = 0 then 'no_articles'
            else 'active'
        end as varchar(20)
    ) as story_membership_status,
    st.warehouse_created_at,
    st.warehouse_updated_at
from {{ ref('stg_dim_story') }} st
left join coverage cov on cov.story_key = st.story_key
