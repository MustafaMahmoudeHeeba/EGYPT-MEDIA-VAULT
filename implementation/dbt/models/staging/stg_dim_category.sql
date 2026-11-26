-- Staging view for dbo.dim_category: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_category') }}

),

renamed as (

    select
        category_key,
        {{ trim_text('category_name') }} as category_name
    from source

)

select * from renamed
