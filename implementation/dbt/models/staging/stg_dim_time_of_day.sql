-- Staging view for dbo.dim_time_of_day: trims text and converts empty strings to NULL where noted. No joins, no renames.
with source as (

    select * from {{ source('warehouse', 'dim_time_of_day') }}

),

renamed as (

    select
        time_key,
        full_time,
        hour_number,
        minute_number,
        second_number,
        hour_12,
        {{ trim_text('am_pm') }} as am_pm,
        {{ trim_text('day_period') }} as day_period,
        is_unknown
    from source

)

select * from renamed
