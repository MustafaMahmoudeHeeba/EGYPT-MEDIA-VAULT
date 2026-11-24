-- Diagnostic (compiled by dbt, never materialized): dim_story rows that are NOT active stories.
-- Run the compiled SQL (target/compiled/.../analyses/) in SSMS or Azure Data Studio.
-- How to read it:
--   unknown_sentinel : the UNKNOWN placeholder story, expected and intentional.
--   no_articles      : no article row points at the story. Compare warehouse_created_at with your pipeline run times:
--                      rows created BEFORE the latest run and left empty are consistent with stories whose articles were
--                      later re-assigned to a different Story ID; rows created at the latest run are stories registered before
--                      their article facts were loaded.
select
    s.story_membership_status,
    s.story_key,
    s.story_id,
    s.story_title,
    s.warehouse_created_at,
    s.warehouse_updated_at
from {{ ref('dim_stories') }} s
where s.story_membership_status <> 'active'
order by s.story_membership_status, s.warehouse_created_at
