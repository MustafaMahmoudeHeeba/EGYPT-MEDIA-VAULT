-- Staging view for dbo.dim_collection_outcome: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_collection_outcome') }}

),

renamed as (

    select
        collection_outcome_key,
        {{ trim_text('collection_outcome') }} as collection_outcome,
        {{ trim_text('failed_step') }} as failed_step
    from source

)

select * from renamed
