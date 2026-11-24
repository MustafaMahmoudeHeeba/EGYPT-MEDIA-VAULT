-- ERROR. For every active story the timeline must contain exactly source_count rows (one per distinct publisher).
select
    c.story_id,
    c.source_count,
    count(t.source_id) as timeline_rows
from {{ ref('mart_story_coverage') }} c
left join {{ ref('mart_story_source_timeline') }} t on t.story_key = c.story_key
group by c.story_id, c.source_count
having c.source_count <> count(t.source_id)
