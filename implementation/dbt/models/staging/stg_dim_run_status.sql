-- Staging view for dbo.dim_run_status: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_run_status') }}

),

renamed as (

    select
        run_status_key,
        {{ trim_text('run_status') }} as run_status,
        {{ trim_text('status_definition') }} as status_definition
    from source

)

select * from renamed
