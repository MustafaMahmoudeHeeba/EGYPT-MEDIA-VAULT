-- ERROR. mart_story_coverage.source_count must equal COUNT(DISTINCT source_id) computed independently from the article rows.
-- Guards the central rule: several articles from one website must never inflate source_count.
select
    c.story_key,
    c.source_count,
    x.distinct_sources
from {{ ref('mart_story_coverage') }} c
join (
    select story_key, count(distinct source_id) as distinct_sources
    from {{ ref('int_articles_enriched') }}
    group by story_key
) x on x.story_key = c.story_key
where c.source_count <> x.distinct_sources
