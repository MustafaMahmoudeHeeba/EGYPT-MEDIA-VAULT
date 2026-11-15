# OOP Design – Class Diagram & Sequence Diagram 1
**Responsible:** Mohamed Abdelmotaleb  **Phase:** System Analysis & Design

## 1. Overview
This document presents the Object-Oriented Programming (OOP) structural and behavioral design for **EGYPT-MEDIA-VAULT**, covering **Deliverable 4 (Class Diagram)** and **Deliverable 5 (Sequence Diagram 1: News Collection & Processing)**. The design aligns directly with the system's Kimball Fact Constellation Data Warehouse (`raw_articles`, `raw_article_issues`, 3 fact tables, and 10 dimensions) and the 10-step incremental ETL pipeline (`L1`–`L10`).

---

## 2. Deliverable 4 – Class Diagram

### 2.1 Class Specifications

| Class Name | Key Attributes | Key Methods | Role & Relationships |
| :--- | :--- | :--- | :--- |
| **`PipelineScheduler`** | `schedule_cron: String`, `is_running: Boolean` | `trigger_pipeline_run()`, `record_missed_run()` | Triggers `0..*` **`PipelineController`** execution runs |
| **`PipelineController`** | `run_id: Int`, `scheduled_timestamp: DateTime`, `start_timestamp: DateTime`, `end_timestamp: DateTime`, `run_status: String` | `execute_run()`, `reconcile_counts()`, `finalize_run()` | Orchestrates **`NewsSource`**, **`WebScraper`**, **`ArticleValidator`**, **`StoryMatcher`**, and **`WarehouseLoader`** |
| **`NewsSource`** | `source_id: Int`, `source_name: String`, `enabled_status: String`, `configuration: Dict`, `access_conditions: String` | `is_enabled()`, `get_crawl_delay()`, `update_config()` | Represents configured Egyptian news portals (`1` source produces `0..*` **`RawArticle`** & **`Article`** records) |
| **`WebScraper`** | `max_retries: Int = 3`, `min_delay_sec: Float = 1.0` | `check_robots_txt()`, `fetch_with_backoff()` | Enforces ethical crawling (`robots.txt`, >= 1.0s delay, up to 3 retries) and outputs **`RawArticle`** objects |
| **`RawArticle`** | `staging_record_id: BigInt`, `run_id: Int`, `source_id: Int`, `raw_title: String`, `raw_original_url: String`, `canonical_url_hash: Hash`, `title_hash: Hash`, `content_fingerprint: Hash`, `ingestion_timestamp: DateTime`, `processing_status: String` | `compute_hashes()`, `mark_status()` | Immutable landed staging payload; owns `0..*` **`ValidationIssue`** records via composition |
| **`ValidationIssue`** | `issue_seq: Int`, `issue_type: String`, `field_name: String`, `issue_description: String`, `is_rejecting: Boolean` | `format_log()` | Records missing required fields or invalid timestamp warnings (`raw_article_issues`) |
| **`ArticleValidator`** | `target_timezone: String = "UTC+2"` | `validate_required_fields()`, `normalize_to_utc2()`, `classify_record()`, `build_clean_article()` | Validates the 4 required fields, normalizes dates to Cairo local time (`UTC+2`), and classifies records (`New`, `Duplicate`, `Updated`, `Rejected`) |
| **`Article`** | `article_id: BigInt`, `article_title: String`, `original_url: String`, `canonical_url_hash: Hash`, `publication_timestamp: DateTime`, `ingestion_timestamp: DateTime`, `timestamp_validity: String`, `syndication_indicator: String`, `link_availability: String` | `is_valid_timestamp()`, `to_fact_record()` | Atomic analytical unit (`dim_article` / `fact_news_articles`); linked to `1` **`NewsSource`**, `1` **`Category`**, `0..1` **`Author`**, and `1` **`StoryCluster`** |
| **`StoryMatcher`** | `similarity_threshold: Float = 0.75` | `vectorize_tfidf()`, `compute_cosine_similarity()`, `match_or_create_story()` | Groups articles into unified stories using TF-IDF + Cosine Similarity on titles (~0.75 threshold) |
| **`StoryCluster`** | `story_cluster_id: Int`, `representative_headline: String`, `first_publication_timestamp: DateTime`, `distinct_source_count: Int` | `add_article()`, `recompute_metrics()` | Parent story entity (`dim_story`) aggregating `1..*` **`Article`** instances |
| **`Category` & `Author`** | `category_id: Int`, `category_name: String` / `author_id: Int`, `author_name: String` | `resolve_or_default()` | Conformed/provisional lookup dimensions defaulting to `"Uncategorized"` and `"Unknown author"` |
| **`WarehouseLoader`** | `db_connection: Connection` | `save_raw_staging()`, `upsert_dimensions()`, `insert_article_fact()`, `log_source_attempt()`, `log_pipeline_run()` | Persists staging records, facts, dimensions, and execution telemetry to the Data Warehouse |

### 2.2 Class Diagram

![Class Diagram](./diagrams/class-diagram.png)

```mermaid
classDiagram
    class PipelineScheduler {
        +String schedule_cron
        +Boolean is_running
        +trigger_pipeline_run() PipelineController
        +record_missed_run() void
    }

    class PipelineController {
        +Int run_id
        +DateTime scheduled_timestamp
        +DateTime start_timestamp
        +DateTime end_timestamp
        +String run_status
        +execute_run() void
        +reconcile_counts() Boolean
    }

    class NewsSource {
        +Int source_id
        +String source_name
        +String enabled_status
        +Dict configuration
        +String access_conditions
        +is_enabled() Boolean
        +get_crawl_delay() Float
    }

    class WebScraper {
        +Int max_retries
        +Float min_delay_sec
        +check_robots_txt(url) Boolean
        +fetch_with_backoff(source) List~RawArticle~
    }

    class RawArticle {
        +BigInt staging_record_id
        +Int run_id
        +Int source_id
        +String raw_title
        +String raw_original_url
        +String raw_publication_text
        +String raw_category_label
        +Bytes canonical_url_hash
        +Bytes content_fingerprint
        +DateTime ingestion_timestamp
        +String processing_status
        +compute_hashes() void
    }

    class ValidationIssue {
        +Int issue_seq
        +String issue_type
        +String field_name
        +String issue_description
        +Boolean is_rejecting
    }

    class ArticleValidator {
        +String target_timezone
        +validate_required_fields(raw) Boolean
        +normalize_to_utc2(raw_date) DateTime
        +classify_record(raw) String
        +build_clean_article(raw) Article
    }

    class Article {
        +BigInt article_id
        +String article_title
        +String original_url
        +Bytes canonical_url_hash
        +DateTime publication_timestamp
        +DateTime ingestion_timestamp
        +String timestamp_validity
        +String syndication_indicator
        +String link_availability
    }

    class StoryMatcher {
        +Float similarity_threshold
        +match_or_create_story(article, active_stories) StoryCluster
    }

    class StoryCluster {
        +Int story_cluster_id
        +String representative_headline
        +DateTime first_publication_timestamp
        +Int distinct_source_count
        +recompute_metrics() void
    }

    class Category {
        +Int category_id
        +String category_name
        +resolve_or_default(raw_label) String
    }

    class Author {
        +Int author_id
        +String author_name
        +resolve_or_default(raw_author) String
    }

    class WarehouseLoader {
        +save_raw_staging(raw_list) void
        +upsert_dimensions(article) void
        +insert_article_fact(article, story) void
        +log_source_attempt(run_id, source_id, stats) void
        +log_pipeline_run(controller) void
    }

    PipelineScheduler "1" --> "0..*" PipelineController : triggers
    PipelineController "1" --> "1..*" NewsSource : queries active
    PipelineController "1" --> "1" WebScraper : invokes
    PipelineController "1" --> "1" ArticleValidator : invokes
    PipelineController "1" --> "1" StoryMatcher : invokes
    PipelineController "1" --> "1" WarehouseLoader : persists via
    WebScraper ..> NewsSource : scrapes
    WebScraper "1" --> "0..*" RawArticle : extracts
    RawArticle "1" *-- "0..*" ValidationIssue : logs issues
    ArticleValidator ..> RawArticle : validates
    ArticleValidator ..> Article : creates
    StoryMatcher ..> Article : evaluates
    StoryMatcher ..> StoryCluster : assigns / creates
    StoryCluster "1" o-- "1..*" Article : groups
    NewsSource "1" --> "0..*" Article : publishes
    Category "1" --> "0..*" Article : categorizes
    Author "1" --> "0..*" Article : writes
    WarehouseLoader ..> Article : loads to DW
    WarehouseLoader ..> StoryCluster : updates in DW
```

---

## 3. Deliverable 5 – Sequence Diagram 1: News Collection & Processing

### 3.1 Interaction Flow Summary
1. **Trigger & Active Source Discovery:** `PipelineScheduler` triggers `PipelineController`, which loads active `NewsSource` configurations (`enabled_status = 'Enabled'`).
2. **Per-Source Isolated Scraping:** `WebScraper` checks `robots.txt`, waits >= 1.0s between host requests, and applies up to 3 exponential retries on failure so single-source errors remain isolated.
3. **Immutable Staging Landing (`L1`):** Extracted payloads are written to `raw_articles` with the system `UTC+2` `ingestion_timestamp`.
4. **Validation, Deduplication & Classification (`L2`–`L3`):** `ArticleValidator` enforces the 4 required fields (`title`, `source`, `link`, `publication date`), converts timestamps to `UTC+2`, hashes URLs/content, records issues in `raw_article_issues`, and classifies rows as `Rejected`, `Duplicate`, `Updated`, or `New`.
5. **Story Clustering (`L4` & `L6`):** `StoryMatcher` computes TF-IDF + Cosine Similarity (~0.75) on titles for `New` articles to assign an existing `StoryCluster` or create a new one.
6. **Warehouse Load & Execution Logging (`L5`, `L7`–`L10`):** `WarehouseLoader` resolves surrogate keys, inserts `dim_article` and `fact_news_articles`, refreshes `dim_story` derived metrics, logs per-source and run-level outcomes (`fact_source_collection`, `fact_pipeline_run`), and runs `DQ-10` reconciliation.

### 3.2 Sequence Diagram 1

![Sequence Diagram 1 - News Collection & Processing](./diagrams/sequence-diagram-1-collection-processing.png)

```mermaid
sequenceDiagram
    autonumber
    actor Scheduler as PipelineScheduler
    participant Ctrl as PipelineController
    participant Src as NewsSource
    participant Scraper as WebScraper
    participant Staging as StagingArea (raw_articles)
    participant Val as ArticleValidator
    participant Matcher as StoryMatcher
    participant DW as DataWarehouse

    Scheduler->>Ctrl: trigger_pipeline_run()
    Ctrl->>Src: get_active_sources()
    Src-->>Ctrl: active_sources_list

    loop For each active NewsSource (Per-Source Isolation)
        Ctrl->>Scraper: scrape_source(source)
        Scraper->>Scraper: check_robots_txt() & wait(>= 1.0s)
        alt HTTP / Network Error
            Scraper->>Scraper: retry_exponential_backoff(max=3)
        end
        Scraper-->>Ctrl: raw_payloads (or source_error)

        opt Payloads Collected
            Ctrl->>Staging: save_raw_articles(raw_payloads, ingestion_ts)
            Staging-->>Ctrl: staging_records

            loop For each RawArticle
                Ctrl->>Val: validate_and_classify(raw_record)
                Val->>Val: check_4_required_fields() & normalize_utc2()
                Val->>Val: compute_canonical_url_hash() & fingerprint()
                Val->>DW: check_existing_hash(canonical_url_hash)
                DW-->>Val: hash_lookup_result

                alt Missing Required Fields
                    Val->>Staging: log_issue(raw_article_issues, is_rejecting=True)
                    Val-->>Ctrl: status = Rejected
                else Hash Exists (Unchanged or Updated)
                    Val->>Staging: update_status(Duplicate / Updated)
                    Val-->>Ctrl: status = Duplicate / Updated
                else New Valid Article
                    Val-->>Ctrl: clean_article (status = New)
                    Ctrl->>Matcher: match_or_create_story(clean_article)
                    Matcher->>DW: fetch_active_stories()
                    DW-->>Matcher: active_story_clusters
                    Matcher->>Matcher: compute_tfidf_cosine_similarity(threshold=0.75)
                    Matcher-->>Ctrl: matched_or_new_story

                    Ctrl->>DW: resolve_dimension_keys(article)
                    Ctrl->>DW: insert_dim_article_and_fact(article, story)
                    Ctrl->>DW: recompute_story_metrics(story)
                    Ctrl->>Staging: update_status(Loaded, article_id)
                end
            end
        end

        Ctrl->>DW: insert_fact_source_collection(run_id, source_id, counts, status)
    end

    Ctrl->>Ctrl: reconcile_counts (DQ-10)
    Ctrl->>DW: insert_fact_pipeline_run(run_id, run_status, timestamps)
```