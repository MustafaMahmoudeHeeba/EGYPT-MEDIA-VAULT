-- WARN. Publication timestamps later than now + tolerance (var future_timestamp_tolerance_hours).
-- The tolerance also absorbs a UTC vs local-time offset in the stored timestamps.
{{ config(severity='warn') }}
select article_key, article_id, source_id, publication_timestamp
from {{ ref('int_articles_enriched') }}
where publication_timestamp > dateadd(hour, {{ var('future_timestamp_tolerance_hours') }}, sysutcdatetime())
