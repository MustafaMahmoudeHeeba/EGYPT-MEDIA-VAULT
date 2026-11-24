-- Staging view for dbo.fact_news_articles: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'fact_news_articles') }}

),

renamed as (

    select
        article_key,
        source_key,
        story_key,
        category_key,
        author_key,
        article_flag_key,
        publication_date_key,
        publication_time_of_day_key,
        ingestion_date_key,
        article_count,
        publication_timestamp,
        ingestion_timestamp
    from source

)

select * from renamed
