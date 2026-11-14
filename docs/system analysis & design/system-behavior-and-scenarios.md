# Subtask 12.2 – System Behavior & Operational Scenarios
**Responsible:** Mohamed Abdelmotaleb  **Phase:** System Analysis & Design

## 1. Overview & Purpose
This document details the operational scenarios and system behavioral flows for the **EGYPT-MEDIA-VAULT** media ingestion and data warehousing pipeline. It operationalizes the functional requirements, non-functional requirements, and stakeholder use cases.

## 2. Primary Operational Scenarios

### 2.1 Automated Batch Ingestion & Staging Run
* **Trigger:** Scheduled Cron execution or automated trigger at midnight (00:00 UTC).
* **System State:** Pipeline idle, database connections active, staging tables truncated.
* **Main Operational Flow:**
  1. **Crawler Initialization:** Scraper modules fetch active target domain endpoints configured in system metadata.
  2. **Page Fetch & Extraction:** HTTP requests extract raw article text, publication metadata, author details, and canonical URLs while respecting `robots.txt` rate delays ($\ge 1.0\text{s}$ per host).
  3. **Staging Load:** Raw HTML payloads and parsed JSON entries are pushed to the staging database landing area.
  4. **Validation:** Ingestion validator checks payload completeness and logs success telemetry.

### 2.2 Deduplication & Data Warehouse Transformation
* **Trigger:** Successful completion of the raw staging ingestion run.
* **Main Operational Flow:**
  1. **Canonical Hash Generation:** Hash functions generate unique identifiers based on normalized canonical URLs and article titles.
  2. **Deduplication Check:** Deduplication pipeline cross-references incoming article hashes against the historical fact table (`fact_news_articles`).
  3. **Metadata Normalization:** Text payloads undergo encoding cleanups, timestamp standardizations (UTC+2 / Cairo Local Time), and category classification.
  4. **Dimension & Fact Upsert:** Transformed records are inserted into `fact_news_articles` and referenced dimension tables (`dim_source`, `dim_author`, `dim_date`).

### 2.3 Exception Handling & Target Site Structure Change
* **Trigger:** Target news outlet updates page DOM structure or returns persistent HTTP 4xx/5xx status codes.
* **System Behavior:**
  1. **Retry Policy:** Scraper executes exponential backoff retries (up to 3 retries).
  2. **Graceful Degradation:** If extraction fails, the target site scraper halts for that specific domain while continuing execution across remaining active targets.
  3. **Alerting & Logging:** Error details, target URL, and stack trace are written to system diagnostic logs and recorded in the monitoring dashboard.

### 2.4 Analytical Query & Dashboard Execution
* **Trigger:** Stakeholder or automated BI dashboard executes analytical query (e.g., comparing coverage across news portals).
* **System Behavior:**
  1. **Query Parsing:** Data warehouse executes optimized star-schema aggregation on indexed dimension surrogate keys.
  2. **Response Delivery:** Result sets are returned to the visualization layer within target response time ($\le 3.0\text{s}$).

## 3. System State Matrix

| System State | Trigger Event | Allowed Operations | Next Transition State |
| :--- | :--- | :--- | :--- |
| **Idle** | Cron Schedule | Initiates scraper workers | Ingesting |
| **Ingestion** | Payload Downloaded | Writes raw staging data | Processing / Transforming |
| **Transforming** | ETL Execution | Deduplicates and loads DW | Idle / Exception Logged |
| **Error Handling** | Parsing / HTTP Failure | Logs exception, triggers alert | Ingesting (Next Target) |
