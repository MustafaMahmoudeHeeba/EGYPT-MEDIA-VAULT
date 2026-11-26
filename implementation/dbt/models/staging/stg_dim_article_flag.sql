-- Staging view for dbo.dim_article_flag: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_article_flag') }}

),

renamed as (

    select
        article_flag_key,
        {{ trim_text('timestamp_validity') }} as timestamp_validity,
        {{ trim_text('syndication_indicator') }} as syndication_indicator
    from source

)

select * from renamed
