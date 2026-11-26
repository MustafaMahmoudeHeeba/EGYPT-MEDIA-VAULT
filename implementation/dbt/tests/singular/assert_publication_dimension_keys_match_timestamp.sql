-- WARN. publication_date_key / time-of-day key must agree with publication_timestamp:
-- known timestamp -> same calendar date and hour; missing timestamp -> unknown date/time members.
{{ config(severity='warn') }}
select article_key, article_id, publication_timestamp, publication_date, publication_hour
from {{ ref('int_articles_enriched') }}
where (publication_timestamp is null and (publication_date is not null or publication_hour is not null))
   or (publication_timestamp is not null and (
           publication_date is null
        or publication_date <> cast(publication_timestamp as date)
        or publication_hour is null
        or publication_hour <> datepart(hour, publication_timestamp)))
