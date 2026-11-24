-- Single-row headline story KPIs for the dashboard. "Story" here means an ACTIVE story (>= 1 article).
-- Stories that exist in dim_story with no articles, and the UNKNOWN sentinel, are reported separately and never counted as stories.
-- Today every story has source_count = 1; multi-source figures will populate as soon as the pipeline clusters one Story ID across publishers.
select
    cast('overall' as varchar(20)) as kpi_scope,
    coalesce(sum(case when s.story_membership_status = 'active' then 1 else 0 end), 0) as total_stories,
    coalesce(sum(case when s.story_membership_status = 'active' and s.source_count > 1 then 1 else 0 end), 0) as multi_source_stories,
    coalesce(sum(case when s.story_membership_status = 'active' and s.source_count = 1 then 1 else 0 end), 0) as single_source_stories,
    {{ pct("sum(case when s.story_membership_status = 'active' and s.source_count > 1 then 1 else 0 end)",
           "sum(case when s.story_membership_status = 'active' then 1 else 0 end)") }} as multi_source_story_pct,
    cast(avg(case when s.story_membership_status = 'active' then cast(s.source_count as decimal(10, 2)) end) as decimal(10, 2)) as avg_publishers_per_story,
    max(case when s.story_membership_status = 'active' then s.source_count end) as max_publishers_per_story,
    coalesce(sum(case when s.story_membership_status = 'active' then s.article_count else 0 end), 0) as total_articles_in_stories,
    cast(avg(case when s.story_membership_status = 'active' then cast(s.article_count as decimal(10, 2)) end) as decimal(10, 2)) as avg_articles_per_story,
    cast(avg(case when s.story_membership_status = 'active' and s.source_count > 1
                  then {{ minutes_between('s.first_published_at', 's.last_published_at') }} end) as decimal(18, 2)) as avg_coverage_gap_minutes_multi_source,
    coalesce(sum(case when s.story_membership_status = 'no_articles' then 1 else 0 end), 0) as stories_without_articles,
    coalesce(sum(case when s.story_membership_status = 'unknown_sentinel' then 1 else 0 end), 0) as unknown_sentinel_stories,
    count(*) as stories_in_dimension,
    cast(sysutcdatetime() as datetime2(0)) as generated_at_utc
from {{ ref('dim_stories') }} s
