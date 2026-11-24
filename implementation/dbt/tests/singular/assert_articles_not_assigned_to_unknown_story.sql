-- WARN. Articles whose story is the UNKNOWN sentinel (they would be excluded from every story KPI).
{{ config(severity='warn') }}
select article_key, article_id, story_id
from {{ ref('int_articles_enriched') }}
where upper(story_id) = upper('{{ var("unknown_story_id") }}')
