-- ERROR. Headline KPIs must reconcile with the story-level mart.
select
    k.total_stories,
    k.single_source_stories,
    k.multi_source_stories,
    c.story_rows
from {{ ref('mart_story_kpis') }} k
cross join (select count(*) as story_rows from {{ ref('mart_story_coverage') }}) c
where k.total_stories <> c.story_rows
   or k.single_source_stories + k.multi_source_stories <> k.total_stories
