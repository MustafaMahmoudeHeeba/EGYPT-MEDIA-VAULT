-- Article grain (one row per fact_news_articles row). The single hub for article-level analytics:
-- every dimension is attached once here so marts never repeat these joins.
-- LEFT JOINs are deliberate: if a key ever fails to resolve, the row is kept and a not_null test reports it,
-- instead of the article silently disappearing from every KPI.
-- Publication date/hour/day come from the warehouse calendar and time-of-day dimensions (the pipelines contract);
-- a warn-level test checks they agree with publication_timestamp.
select
    f.article_key,
    a.article_id,
    a.article_title,
    a.original_url,
    a.canonical_url_hash,
    a.link_availability,
    {{ flag_to_bit('a.article_content is not null') }} as has_content,
    {{ flag_to_bit('a.article_description is not null') }} as has_description,
    {{ flag_to_bit('a.article_image_url is not null') }} as has_image,
    f.story_key,
    st.story_id,
    st.representative_title as story_title,
    f.source_key,
    src.source_id,
    src.source_name,
    f.category_key,
    c.category_name,
    f.author_key,
    au.author_name,
    fl.timestamp_validity,
    fl.syndication_indicator,
    f.publication_timestamp,
    {{ flag_to_bit('f.publication_timestamp is not null') }} as has_publication_time,
    f.publication_date_key,
    case when d.is_unknown = 1 then null else d.full_date end as publication_date,
    case when t.is_unknown = 1 then null else t.hour_number end as publication_hour,
    case when d.is_unknown = 1 then null else d.day_name end as publication_day_name,
    case when d.is_unknown = 1 or d.full_date is null then null
         else (datediff(day, cast('19000101' as date), d.full_date) % 7) + 1 end as publication_iso_day_of_week,
    case when d.is_unknown = 1 then null else d.is_weekend end as publication_is_weekend,
    case when t.is_unknown = 1 then null else t.day_period end as publication_day_period,
    f.ingestion_timestamp,
    cast(f.ingestion_timestamp as date) as ingestion_date,
    f.article_count as fact_article_count,
    a.warehouse_updated_at as article_updated_at
from {{ ref('stg_fact_news_articles') }} f
left join {{ ref('stg_dim_article') }} a on a.article_key = f.article_key
left join {{ ref('stg_dim_story') }} st on st.story_key = f.story_key
left join {{ ref('stg_dim_source') }} src on src.source_key = f.source_key
left join {{ ref('stg_dim_category') }} c on c.category_key = f.category_key
left join {{ ref('stg_dim_author') }} au on au.author_key = f.author_key
left join {{ ref('stg_dim_article_flag') }} fl on fl.article_flag_key = f.article_flag_key
left join {{ ref('stg_dim_date') }} d on d.date_key = f.publication_date_key
left join {{ ref('stg_dim_time_of_day') }} t on t.time_key = f.publication_time_of_day_key
