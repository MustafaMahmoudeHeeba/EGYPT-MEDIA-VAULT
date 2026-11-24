# EGYPT-MEDIA-VAULT: dbt analytics layer

dbt project for the existing Azure SQL Server warehouse (`egypt_media_vault`, schema `dbo`). The Python pipeline keeps
doing scraping, validation, dedup, clustering, Story ID assignment and warehouse loading. dbt only **reads** the warehouse
and builds the transformation, testing and analytics layer for the FastAPI backend and the Next.js dashboard.

## 1. Architecture

| Layer | Folder | Schema | Materialization | Models |
|---|---|---|---|---|
| Sources | `models/sources` | `dbo` (read-only) | n/a | 13 warehouse tables |
| Staging | `models/staging` | `dbt_staging` | view | 13 `stg_*` (1:1, trim/clean only) |
| Intermediate | `models/intermediate` | `dbt_intermediate` | view | 4 `int_*` |
| Core marts | `models/marts/core` | `core` | table | `dim_sources`, `dim_stories`, `fct_articles` |
| Analytics marts | `models/marts/analytics` | `analytics` | table | 12 `mart_*` |

Total 32 models, 18 singular tests, 2 generic tests, ~180 generic test declarations, 2 diagnostic analyses.

Excluded on purpose: `raw_articles`, `raw_article_issues` (pipeline-owned staging) and `sysdiagrams`. `dim_source.configuration` and
`access_conditions` are not staged (free-form configuration, not needed for analytics, and potentially sensitive).

### Model inventory

**Staging** (`stg_<table>`): `dim_article`, `dim_article_flag`, `dim_author`, `dim_category`, `dim_collection_outcome`, `dim_date`,
`dim_run_status`, `dim_source`, `dim_story`, `dim_time_of_day`, `fact_news_articles`, `fact_pipeline_run`, `fact_source_collection`.

**Intermediate**
- `int_articles_enriched` : article grain hub, all dimensions attached once.
- `int_story_source_coverage` : story x `source_id`; the building block of the main KPI.
- `int_pipeline_runs_enriched` : run grain with status and date.
- `int_source_collection_enriched` : run x source with outcome, status, source and date.

**Core marts**: `dim_sources` (one row per publisher), `dim_stories` (every dim_story row + counts + membership status), `fct_articles` (article feed, no full text).

**Analytics marts**

| Model | Grain | Serves |
|---|---|---|
| `mart_story_coverage` | active story | MAIN KPI: publishers, `source_count`, `article_count`, first/last publication, gap, first source, rank |
| `mart_story_source_timeline` | active story x publisher | publisher-by-publisher times and lag behind the first publisher |
| `mart_story_kpis` | 1 row | total / single / multi-source stories, average publishers per story |
| `mart_source_summary` | publisher | totals, share of coverage, most active, shared vs exclusive stories |
| `mart_source_daily` | date x publisher | publication trends, daily share, rank, cumulative |
| `mart_category_summary` | category x publisher | category distribution, categories by source |
| `mart_category_daily` | date x category x publisher | category trends |
| `mart_time_activity` | date x hour x publisher | per day, per hour, weekday and hour patterns, trends |
| `mart_pipeline_runs` | run | status, duration, collected / rejected / duplicate totals |
| `mart_pipeline_status_summary` | run status | run counts per status (Success / Partial / Failed ...) |
| `mart_source_run_collection` | run x publisher | collected, rejected, duplicates, outcome per source per run |
| `mart_source_reliability` | publisher | success rate, retries, failures by step |

## 2. Business rules (the important ones)

- **Story relationship, not titles.** Everything is driven by `fact_news_articles.story_key` -> `dim_story`.
- **`article_count` vs `source_count`.** `article_count` = article rows in the story (`COUNT(*)`; the fact column
  `fact_news_articles.article_count` is a row-level measure expected to be 1 and is never summed).
  `source_count` = number of **distinct `dim_source.source_id`**. `int_story_source_coverage` has one row per story x `source_id`,
  so several articles from one website raise `article_count` only.
- **`source_id`, not `source_key`.** `dim_source` is Type 2 (versioned); counting `source_key` could count one website twice after a configuration change.
- **First source** = publisher of the earliest `publication_timestamp`; ties break on `source_id` (alphabetical), so results are deterministic.
  Articles without a timestamp count in `article_count`/`source_count`, are excluded from timing, and are reported in `articles_missing_publication_time`. No timestamp is ever invented.
- **Coverage gap** = minutes (2 decimals, computed from seconds) between the earliest and latest publication of the story.
- **No fabricated multi-source stories.** Today every story has `source_count = 1`. Multi-source output appears automatically once the pipeline assigns one Story ID to articles of several publishers.

### Integrity findings and how dbt treats them

- `fact_article_without_story = 0`: every fact row resolves to a story. Enforced by your foreign keys and re-checked by tests.
- **Stories with 0 articles and `UNKNOWN`**: kept in `dim_stories`, classified by `story_membership_status`:
  `active` (>= 1 article), `no_articles`, `unknown_sentinel`. Only `active` stories count in story KPIs. They are reported (`stories_without_articles`, `unknown_sentinel_stories` in `mart_story_kpis`) and **no test fails on them**.
- **`dim_article_without_fact = 1`**: surfaced by the warn-level test `assert_dim_article_without_fact`; not deleted or hidden.
- To see which rows these are, compile and run the diagnostics in SSMS: `dbt compile` then open
  `target/compiled/egypt_media_vault/analyses/diagnose_stories_without_articles.sql` and `diagnose_dim_article_without_fact.sql`.
  The comments in those files explain how to interpret `warehouse_created_at`. Whether those rows are stale, orphaned or intentionally retained
  depends on your pipeline behavior (not visible from the warehouse alone); dbt reports them but does not decide.

## 3. Materialization strategy

- Staging and intermediate are **views** (always current); marts are **tables rebuilt on every run**.
- **No incremental models.** `fact_news_articles` has no updated timestamp, and a re-clustered article changes `story_key` on the fact row
  without necessarily touching `dim_article.warehouse_updated_at`; an incremental filter on one timestamp would silently miss such changes.
  Full rebuilds recompute from current warehouse state and cannot lose updates. At this volume they are cheap. Revisit only at millions of rows.
- **No snapshots.** `dim_source` already versions itself; nothing in the data justifies SCD logic in dbt.

## 4. Setup

### Requirements
- Python 3.12, **Microsoft ODBC Driver 18 for SQL Server** installed on the machine running dbt.
- `pip install -r requirements-dbt.txt` (pins `dbt-core` and `dbt-sqlserver` to the same minor version, `~=1.9.0`).
  These pins were **not** verified against PyPI when this project was produced. Run `pip index versions dbt-sqlserver` and keep core/adapter minors identical.
- No dbt packages are used (`packages.yml` is empty): the generic tests and macros live in this project.

### Environment variables (PowerShell)
```powershell
$env:DBT_SQLSERVER_HOST     = "<server>.database.windows.net"
$env:DBT_SQLSERVER_DATABASE = "egypt_media_vault"     # default
$env:DBT_SQLSERVER_SCHEMA   = "dbt"                   # fallback schema only
$env:DBT_SQLSERVER_AUTH     = "sql"                   # sql | ActiveDirectoryPassword | ServicePrincipal | CLI | auto
$env:DBT_SQLSERVER_USER     = "<login>"
$env:DBT_SQLSERVER_PASSWORD = "<password>"            # set in your shell / secret store, never in files
```
For `ServicePrincipal`, uncomment `tenant_id`, `client_id`, `client_secret` in your copy of `profiles.yml` and feed them from env vars.

### Profile
```powershell
Copy-Item .\dbt\profiles.yml.example "$HOME\.dbt\profiles.yml"    # or set $env:DBT_PROFILES_DIR
```
`profiles.yml.example` contains no credentials; it enables `encrypt: true`, `trust_cert: false` (required for Azure SQL).

### Database permissions
Read access on `dbo`, plus the right to create objects in the four dbt schemas. Pre-creating the schemas avoids granting `CREATE SCHEMA`:
```sql
CREATE SCHEMA dbt_staging;       -- run each as its own batch
CREATE SCHEMA dbt_intermediate;
CREATE SCHEMA core;
CREATE SCHEMA analytics;
GRANT SELECT ON SCHEMA::dbo TO [dbt_user];
GRANT CREATE TABLE, CREATE VIEW TO [dbt_user];
GRANT CONTROL ON SCHEMA::dbt_staging TO [dbt_user];
GRANT CONTROL ON SCHEMA::dbt_intermediate TO [dbt_user];
GRANT CONTROL ON SCHEMA::core TO [dbt_user];
GRANT CONTROL ON SCHEMA::analytics TO [dbt_user];
```
(`[dbt_user]` is a placeholder database user. Adjust to your security policy.) Note: `analytics` and `core` are also the schemas the API should read; grant it `SELECT` there.

## 5. Commands (run from the `dbt` folder)
```powershell
cd dbt
dbt debug                      # connectivity check
dbt deps                       # no-op (no packages), safe for CI
dbt parse                      # offline structure check; still needs the env vars (dummy values are enough)
dbt build                      # models + tests in dependency order
dbt run   --select staging intermediate marts
dbt test  --select marts
dbt source freshness           # warns if no article/run was loaded for 48 h
dbt docs generate; dbt docs serve
```
Useful selections: `dbt build --select +mart_story_coverage` (the main KPI and everything it needs), `dbt test --select test_type:singular`.

## 6. Testing strategy

Generic tests: `not_null`, `unique`, `relationships`, `accepted_values` and the project tests `unique_combination` and `expression_is_true`.
Singular tests (`tests/singular`) start with `-- ERROR` (fails the build) or `-- WARN` (reports, never blocks):

| Test | Severity | Meaning |
|---|---|---|
| `assert_story_source_count_matches_distinct_sources` | error | `source_count` equals an independent `COUNT(DISTINCT source_id)` |
| `assert_story_article_count_matches_fact_rows` | error | story `article_count` equals fact rows (0 for empty stories) |
| `assert_story_membership_status_is_consistent` | error | classification agrees with counts; empty / UNKNOWN stories are valid |
| `assert_story_time_order` | error | first <= last, per story and per publisher |
| `assert_timeline_has_one_row_per_publisher` | error | timeline rows == `source_count` |
| `assert_story_kpis_reconcile` | error | headline KPIs reconcile with story mart |
| `assert_source_summary_reconciles_with_fact` | error | source totals == fact rows |
| `assert_fct_articles_matches_fact_rows` | error | no articles lost or duplicated |
| `assert_collection_counts_are_not_negative` | error | operational counters >= 0 |
| `assert_run_end_not_before_start` | error | run end >= start |
| `assert_publication_timestamps_not_in_future` | warn | beyond `now + future_timestamp_tolerance_hours` |
| `assert_publication_dimension_keys_match_timestamp` | warn | date/hour dimension keys agree with `publication_timestamp` |
| `assert_dim_article_without_fact` | warn | reports the known `dim_article_without_fact` row(s) |
| `assert_articles_not_assigned_to_unknown_story` | warn | articles in the UNKNOWN sentinel story |
| `assert_no_duplicate_canonical_url_hash` | warn | possible missed duplicate articles |
| `assert_each_run_covers_every_current_source` | warn | one row per source per run, all current enabled sources covered |
| `assert_fact_row_measures_are_one` | warn | `article_count` / `run_count` are row-level 1s |
| `assert_success_labels_match_warehouse_values` | warn | the configured success labels match real values |

Expected behavior today: all error tests pass; warn tests report the one `dim_article` without fact (and, if applicable, future-dated timestamps).
`source_id` accepted values (`youm7`, `almasryalyoum`, `masrawy`) is warn-only so a new publisher does not break the build.

## 7. Assumptions (decide and document, change in `dbt_project.yml` if wrong)

1. **Timezone.** Publication dates/hours are analyzed in the timezone the pipeline stored (via `dim_date` / `dim_time_of_day`); dbt does not shift timestamps.
   If they are UTC and the dashboard should show Cairo time, convert in the API or ask for a follow-up model using `AT TIME ZONE`.
2. **Success labels.** A collection/run is successful when `collection_outcome` / `run_status` equals `Success` (case-insensitive), vars `success_outcome_label` and `success_run_status_label`.
   The warn test `assert_success_labels_match_warehouse_values` fires if these labels match nothing.
3. **Status vocabularies not hard-coded.** The legal values of `run_status`, `collection_outcome`, `timestamp_validity`, `syndication_indicator` and `link_availability` were not supplied, so no `accepted_values` test is invented for them.
   To add one: `SELECT DISTINCT run_status FROM dbo.dim_run_status` and add an `accepted_values` test in `models/staging/schema.yml`.
4. **Weekday.** `publication_iso_day_of_week` is computed (1 = Monday ... 7 = Sunday). `publication_is_weekend` and day names come from `dim_date` as stored.
5. **`UNKNOWN` story** identified by `story_id = 'UNKNOWN'` (var `unknown_story_id`, case-insensitive).
6. `rejected_to_collected_pct` / `duplicate_to_collected_pct` are plain ratios; the project does not assume whether `articles_collected_count` already includes rejected/duplicate records.

## 8. KPIs that cannot be calculated reliably today

- **Rejection reasons**: live in `raw_article_issues` (pipeline staging), not modelled.
- **Article update history / time-to-update**: the warehouse has no source-side updated timestamp; `warehouse_updated_at` only reflects warehouse changes (exposed as `article_updated_at`).
- **Validation status** beyond `timestamp_validity` and `syndication_indicator`: no such column in the warehouse.
- **Publisher lag and coverage gap** are meaningful only once multi-source stories exist (all current stories have one publisher).
- **Pipeline duration** needs non-null `start_timestamp` and `end_timestamp`; otherwise NULL. **Reliability rates** are indicative only with a handful of runs.

## 9. SQL Server notes

T-SQL only: `TOP` (not `LIMIT`), no `ORDER BY` in views, `STRING_AGG ... WITHIN GROUP`, `DATEDIFF_BIG`, conditions exposed as `BIT`, explicit casts.
Staging uses `NVARCHAR`-safe trimming (Arabic text untouched). Test queries avoid CTEs for compatibility with the adapter's test wrapper.

## 10. CI

`.github/workflows/dbt-ci.yml` is outside this folder and was not changed. It should install `requirements-dbt.txt`, install ODBC Driver 18,
provide the `DBT_SQLSERVER_*` secrets, and run `dbt deps` then `dbt build` (or `dbt parse` for an offline check).
