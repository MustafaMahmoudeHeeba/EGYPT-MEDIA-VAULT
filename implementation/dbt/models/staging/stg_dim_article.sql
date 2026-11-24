-- Staging view for dbo.dim_article: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_article') }}

),

renamed as (

    select
        article_key,
        {{ trim_text('article_id') }} as article_id,
        {{ clean_text('article_title') }} as article_title,
        {{ clean_text('original_url') }} as original_url,
        {{ clean_text('canonical_url_hash') }} as canonical_url_hash,
        {{ clean_text('article_description') }} as article_description,
        {{ clean_text('article_content') }} as article_content,
        {{ clean_text('article_image_url') }} as article_image_url,
        {{ trim_text('link_availability') }} as link_availability,
        warehouse_created_at,
        warehouse_updated_at
    from source

)

select * from renamed
