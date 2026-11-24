-- ERROR. A story/publisher can never end before it starts.
select story_id, cast(null as nvarchar(100)) as source_id, first_published_at, last_published_at
from {{ ref('mart_story_coverage') }}
where first_published_at > last_published_at
union all
select story_id, source_id, first_published_at, last_published_at
from {{ ref('mart_story_source_timeline') }}
where first_published_at > last_published_at
