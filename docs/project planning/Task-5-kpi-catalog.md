# Task 5 – KPI Catalog & Definition Plan

**Responsible:** Bolla Kameel **Phase:** Project Planning

# 1. Executive Summary & Objective

This document outlines the KPI Catalog and Analytical Measures for the **EGYPT-MEDIA-VAULT** project prior to implementation[cite: 3]. It identifies, defines, and structures the core performance metrics and analytical requirements necessary to track news coverage, article distribution, and media insights across Egyptian news portals[cite: 2, 3].

# 2. KPI Catalog & Evaluation

| KPI ID | KPI Name | Category | Description & Purpose | Calculation Level | Priority / Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **KPI01** | Total Articles Ingested | Data Volume | Measures total volume of news articles successfully scraped and loaded into the Data Warehouse [cite: 3]. | Per source, per time period [cite: 2] | Core |
| **KPI02** | Cross-Source Story Coverage | Story Comparison | Tracks the number of unique news websites publishing articles covering the same or similar news story [cite: 2, 3]. | Per story cluster | Core |
| **KPI03** | Publication Time Delta | Timing & Velocity | Calculates the time gap in publication timestamps between the initial breaking source and subsequent reporting outlets [cite: 2, 3]. | Per article pair / per story | Core |
| **KPI04** | Source Publishing Frequency | Source Statistics | Evaluates output volume, publishing velocity, and active hours per news website [cite: 2]. | Per source, per day/week | Core |
| **KPI05** | Category Distribution Share | Content Analytics | Analyzes the proportion of news coverage distributed across various categories (e.g., Politics, Economy, Sports). | Per category, per source | Optional |

# 3. KPI-to-Data-Input Matrix

| KPI ID | Required Data Inputs | Source Tables / Fields | Technical Calculation Logic |
| :--- | :--- | :--- | :--- |
| **KPI01** | Article ID, Source ID, Ingestion Timestamp | `raw_articles`, `sources` | `COUNT(article_id)` grouped by `source_id` over specified intervals. |
| **KPI02** | Story Cluster ID, Article ID, Source ID | `story_clusters`, `article_mappings` | Distinct count of `source_id` associated with each `story_cluster_id`. |
| **KPI03** | Publication Timestamp, Source ID, Story ID | `articles` | `publication_timestamp - MIN(publication_timestamp)` for articles in the same cluster. |
| **KPI04** | Article ID, Publication Timestamp, Source ID | `articles` | Time-series aggregation of article counts per source. |
| **KPI05** | Category ID, Article ID, Source ID | `articles`, `categories` | `(Articles per Category / Total Articles) * 100` per source. |

# 4. Open KPI Definition Questions & Logging

* **Q01:** What exact text-similarity threshold or entity-matching algorithm defines a "similar story" across competing news portals [cite: 2]? (Assigned to Ibrahim Mowafy) [cite: 2]
* **Q02:** How should syndicated news feeds or identical wire service releases be filtered or weighted in publication velocity metrics? (Assigned to Bolla Kameel) [cite: 2]
* **Q03:** Can source-level comparison statistics be easily phrased as clear user acceptance criteria for upcoming user stories [cite: 2]? (Assigned to Mohamed Khaled) [cite: 2]
