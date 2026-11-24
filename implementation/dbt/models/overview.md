{% docs __overview__ %}

# EGYPT-MEDIA-VAULT analytics layer

dbt models on top of the existing Azure SQL Server data warehouse (`dbo` star schema). The Python pipeline owns scraping,
validation, deduplication, story clustering, Story ID assignment and warehouse loading. dbt only reads the warehouse and builds:

| Layer | Schema | Materialization | Purpose |
|---|---|---|---|
| staging (`stg_*`) | `dbt_staging` | view | 1:1 clean views of warehouse tables |
| intermediate (`int_*`) | `dbt_intermediate` | view | joins and reusable logic |
| core marts | `core` | table | conformed entities (`fct_articles`, `dim_stories`, `dim_sources`) |
| analytics marts (`mart_*`) | `analytics` | table | dashboard / API facing KPIs |

**Main KPI:** `mart_story_coverage` and `mart_story_source_timeline` (cross-publisher story coverage by Story ID).

Key definitions: `article_count` = articles in a story; `source_count` = DISTINCT publishing websites (`source_id`).
They are never interchangeable.

{% enddocs %}
