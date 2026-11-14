# Task 9 – Non-Functional Requirements
**Responsible:** Mohamed Abdelmotaleb  **Phase:** System Architecture & Requirements

## 1. Overview & Scope
This document specifies the non-functional requirements (NFRs) for the **EGYPT-MEDIA-VAULT** platform, defining system attributes across performance, scalability, reliability, security, maintainability, and legal/ethical compliance.

## 2. Quality Attributes & Specifications

### 2.1 Performance & Throughput
* **NFR-P01 (Scraping Latency):** Ingestion pipelines must process single article pages within $\le 2.0$ seconds under standard network conditions.
* **NFR-P02 (Batch Throughput):** The automated pipeline must process and load daily news dumps ($\ge 10,000$ articles) into the staging area within 45 minutes.
* **NFR-P03 (Query Response Time):** Analytical queries on the warehouse fact tables (e.g., article counts, temporal aggregation) must return results in $\le 3.0$ seconds.

### 2.2 Reliability & Fault Tolerance
* **NFR-R01 (Scraper Resilience):** Page structure failures or HTTP 4xx/5xx errors on individual targets must fail gracefully, log detailed diagnostic telemetry, and continue scraping remaining targets without process crash.
* **NFR-R02 (Data Deduplication):** Ingestion rules must maintain $99.9\%$ accuracy in detecting duplicate articles based on canonical URL hashes and temporal publication windows.

### 2.3 Security & Compliance
* **NFR-S01 (Credential Protection):** Database connection strings, API keys, and environment secrets must never be hardcoded or committed to version control.
* **NFR-S02 (Rate Limiting & Ethics):** Web crawlers must respect domain `robots.txt` directives and enforce configurable delays ($\ge 1.0$ sec between requests per host) to prevent DoS-like behavior.

### 2.4 Scalability & Storage
* **NFR-SC01 (Storage Efficiency):** The relational warehouse schema must handle historical data growth for at least 2 years ($\approx 500,000+$ media records) without performance degradation.
