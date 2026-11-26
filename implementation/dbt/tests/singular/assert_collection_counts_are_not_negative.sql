-- ERROR. Operational counters can never be negative.
select run_id, source_key, attempt_count, articles_collected_count, articles_rejected_count, duplicate_record_count
from {{ ref('stg_fact_source_collection') }}
where attempt_count < 0
   or articles_collected_count < 0
   or articles_rejected_count < 0
   or duplicate_record_count < 0
