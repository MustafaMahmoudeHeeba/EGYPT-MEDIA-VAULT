-- Grain: run x publisher. Articles collected, rejected and duplicate per source per run, with outcome.
-- rejected_to_collected_pct / duplicate_to_collected_pct are plain ratios to articles_collected_count (NULL when it is 0 or NULL);
-- no assumption is made about whether the collected count already includes rejected or duplicate records.
select
    c.run_id,
    c.run_date,
    c.run_status,
    c.source_id,
    c.source_name,
    c.collection_outcome,
    c.failed_step,
    c.is_successful_collection,
    c.attempt_count,
    c.is_retried,
    c.articles_collected_count,
    c.articles_rejected_count,
    c.duplicate_record_count,
    {{ pct('c.articles_rejected_count', 'c.articles_collected_count') }} as rejected_to_collected_pct,
    {{ pct('c.duplicate_record_count', 'c.articles_collected_count') }} as duplicate_to_collected_pct,
    c.error_description,
    c.start_timestamp,
    c.end_timestamp
from {{ ref('int_source_collection_enriched') }} c
