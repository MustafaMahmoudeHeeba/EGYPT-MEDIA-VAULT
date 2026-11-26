-- Grain: story x source_id. THE building block of the cross-publisher KPI.
-- Grouping by source_id (the natural publisher id, NOT the versioned source_key) guarantees that
--   * several articles from the same website collapse into one row (they raise article_count, never source_count), and
--   * a Type 2 change of dim_source never makes one website look like two publishers.
-- Therefore: source_count of a story = number of rows here for that story_key.
select
    story_key,
    story_id,
    source_id,
    count(*) as article_count,
    count(publication_timestamp) as articles_with_publication_time,
    count(*) - count(publication_timestamp) as articles_missing_publication_time,
    min(publication_timestamp) as first_published_at,
    max(publication_timestamp) as last_published_at
from {{ ref('int_articles_enriched') }}
group by story_key, story_id, source_id
