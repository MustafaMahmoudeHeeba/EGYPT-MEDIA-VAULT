-- Staging view for dbo.dim_date: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_date') }}

),

renamed as (

    select
        date_key,
        full_date,
        day_number,
        {{ trim_text('day_name') }} as day_name,
        day_of_week,
        week_number,
        month_number,
        {{ trim_text('month_name') }} as month_name,
        quarter_number,
        year_number,
        is_weekend,
        is_unknown
    from source

)

select * from renamed
