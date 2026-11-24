-- Staging view for dbo.dim_story: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_story') }}

),

renamed as (

    select
        story_key,
        {{ trim_text('story_id') }} as story_id,
        {{ trim_text('representative_title') }} as representative_title,
        warehouse_created_at,
        warehouse_updated_at
    from source

)

select * from renamed
