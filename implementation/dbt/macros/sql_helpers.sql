{# Small T-SQL helpers. Each one is used by several models, which is why they are macros. #}

{# Trim leading/trailing whitespace. #}
{% macro trim_text(column_name) -%}
    ltrim(rtrim({{ column_name }}))
{%- endmacro %}

{# Trim and turn empty strings into NULL. #}
{% macro clean_text(column_name) -%}
    nullif(ltrim(rtrim({{ column_name }})), '')
{%- endmacro %}

{# SQL Server has no boolean type: expose conditions as BIT. #}
{% macro flag_to_bit(condition) -%}
    cast(case when {{ condition }} then 1 else 0 end as bit)
{%- endmacro %}

{#
    Elapsed minutes (2 decimals) between two datetimes. Uses second-level DATEDIFF_BIG, because
    DATEDIFF(minute, ...) counts minute boundaries crossed (10:59:59 -> 11:00:00 would be 1 minute).
    Returns NULL when either side is NULL.
#}
{% macro minutes_between(start_column, end_column) -%}
    cast(datediff_big(second, {{ start_column }}, {{ end_column }}) / 60.0 as decimal(18, 2))
{%- endmacro %}

{# Percentage with 2 decimals; NULL when the denominator is 0 or NULL. #}
{% macro pct(numerator, denominator) -%}
    cast(100.0 * ({{ numerator }}) / nullif({{ denominator }}, 0) as decimal(7, 2))
{%- endmacro %}

{# Lower-cased value of a project variable, for case-insensitive label comparison. #}
{% macro var_label(var_name) -%}
    '{{ var(var_name) | lower | replace("'", "''") }}'
{%- endmacro %}
