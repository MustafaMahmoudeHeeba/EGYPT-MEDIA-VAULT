{#-
    Use the custom schema exactly as configured (dbt_staging, dbt_intermediate, core, analytics)
    instead of dbt's default "<target_schema>_<custom_schema>" concatenation.
    Models without a custom schema land in target.schema.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema | trim }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
