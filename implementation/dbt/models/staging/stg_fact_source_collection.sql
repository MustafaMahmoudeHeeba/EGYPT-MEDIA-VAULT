-- Staging view for dbo.fact_source_collection: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'fact_source_collection') }}

),

renamed as (

    select
        {{ trim_text('run_id') }} as run_id,
        source_key,
        run_date_key,
        collection_outcome_key,
        attempt_count,
        articles_collected_count,
        articles_rejected_count,
        duplicate_record_count,
        {{ clean_text('error_description') }} as error_description
    from source

)

select * from renamed
