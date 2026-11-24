-- Staging view for dbo.dim_source: trims text and converts empty strings to NULL where noted. No joins, no renames.
-- Columns deliberately not staged: configuration, access_conditions (free-form configuration; not needed for analytics).

with source as (

    select * from {{ source('warehouse', 'dim_source') }}

),

renamed as (

    select
        source_key,
        {{ trim_text('source_id') }} as source_id,
        {{ trim_text('source_name') }} as source_name,
        enabled_status,
        version_effective_from,
        version_effective_to,
        is_current
    from source

)

select * from renamed
