{#- Fails for every combination of columns that appears more than once. No CTE, so it is safe on SQL Server test wrappers. -#}
{% test unique_combination(model, combination_of_columns) %}

select
    {{ combination_of_columns | join(', ') }},
    count(*) as n_records
from {{ model }}
group by {{ combination_of_columns | join(', ') }}
having count(*) > 1

{% endtest %}
