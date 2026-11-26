{#- Fails for every row where the SQL expression is not true (rows where it evaluates to NULL are not reported; use not_null for that). -#}
{% test expression_is_true(model, expression, column_name=none, where_clause=none) %}

select *
from {{ model }}
where not ({{ expression }})
{%- if where_clause is not none %}
  and ({{ where_clause }})
{%- endif %}

{% endtest %}
