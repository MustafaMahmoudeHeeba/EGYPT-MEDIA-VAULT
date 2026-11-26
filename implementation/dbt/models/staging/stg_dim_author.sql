-- Staging view for dbo.dim_author: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_author') }}

),

renamed as (

    select
        author_key,
        {{ trim_text('author_name') }} as author_name
    from source

)

select * from renamed
