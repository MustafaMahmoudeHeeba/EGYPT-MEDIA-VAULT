-- Staging view for dbo.fact_pipeline_run: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'fact_pipeline_run') }}

),

renamed as (

    select
        {{ trim_text('run_id') }} as run_id,
        run_date_key,
        run_status_key,
        run_count,
        scheduled_timestamp,
        start_timestamp,
        end_timestamp,
        {{ clean_text('missed_reason') }} as missed_reason
    from source

)

select * from renamed
