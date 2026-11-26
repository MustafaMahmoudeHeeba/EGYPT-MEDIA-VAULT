-- Grain: publication_date x publication_hour x publisher (articles with a known publication date and time only).
-- One compact model serves every time view: articles per day / per hour, activity by weekday and by hour of day, trends over time
-- (the API simply SUMs article_count grouped by the column it needs).
-- publication_iso_day_of_week: 1 = Monday ... 7 = Sunday (computed, independent of dim_dates own numbering).
-- Dates/hours are expressed in the timezone the pipeline stored the timestamps in (see README, "Assumptions").
select
    e.publication_date,
    e.publication_hour,
    e.source_id,
    max(e.publication_day_name) as publication_day_name,
    max(e.publication_iso_day_of_week) as publication_iso_day_of_week,
    max(e.publication_day_period) as publication_day_period,
    max(cast(e.publication_is_weekend as int)) as publication_is_weekend,
    count(*) as article_count
from {{ ref('int_articles_enriched') }} e
where e.publication_date is not null
  and e.publication_hour is not null
group by e.publication_date, e.publication_hour, e.source_id
