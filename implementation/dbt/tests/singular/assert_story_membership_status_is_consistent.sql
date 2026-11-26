-- ERROR. The story classification must agree with the counts.
-- Empty stories and the UNKNOWN sentinel are VALID rows: they are classified, never failed.
select
    story_key,
    story_id,
    story_membership_status,
    article_count
from {{ ref('dim_stories') }}
where (story_membership_status = 'active' and article_count = 0)
   or (story_membership_status = 'no_articles' and article_count > 0)
   or (story_membership_status not in ('active', 'no_articles', 'unknown_sentinel'))
