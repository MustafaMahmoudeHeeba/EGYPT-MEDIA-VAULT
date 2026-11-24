-- WARN. The same canonical URL hash on several dim_article rows suggests a duplicate article that deduplication missed.
{{ config(severity='warn') }}
select canonical_url_hash, count(*) as article_rows
from {{ ref('stg_dim_article') }}
where canonical_url_hash is not null
group by canonical_url_hash
having count(*) > 1
