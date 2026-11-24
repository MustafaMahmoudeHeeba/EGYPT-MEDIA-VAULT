-- ERROR. A run cannot end before it starts.
select run_id, start_timestamp, end_timestamp
from {{ ref('stg_fact_pipeline_run') }}
where end_timestamp < start_timestamp
