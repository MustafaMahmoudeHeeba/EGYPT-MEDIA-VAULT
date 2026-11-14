# Task 10 – Problem Statement & Objectives

Responsible: Ibrahim Mowafy
Phase: System Analysis & Design

## 1. Problem Statement

Egyptian news websites publish a large number of articles every day, and the same story is often covered by several websites at different times and in different ways. This news is spread across many separate websites, so it is hard to collect it in one place, keep its history, or compare how different sources cover the same story. Without a central and organized data source, analysts cannot easily measure which sources cover which stories, how many sources cover the same story, or how far apart their publication times are.

EGYPT-MEDIA-VAULT solves this problem by collecting news articles automatically, storing them in a central Data Warehouse, and giving analysts KPIs and reports about news coverage.

## 2. Objectives

Each objective is linked to a measure from the Functional Requirements (Task 8).

| # | Objective | How it is measured |
|---|-----------|--------------------|
| 1 | Collect news articles automatically from multiple Egyptian news websites. | Total Articles Ingested (KPI-01); collection-run history |
| 2 | Clean, validate and standardize the collected data before using it. | Data Completeness (%); Duplicate Article Rate (%) |
| 3 | Store the data in one central Data Warehouse, with history over time and original source information. | Historical comparisons across reporting periods; Attribution Completeness (%) |
| 4 | Group articles that cover the same story across different sources. | Cross-Source Story Coverage (KPI-02) |
| 5 | Compare when different sources published the same story. | Publication Time Delta (KPI-03), measured from the earliest valid publication time in the story group |
| 6 | Analyze how often each source publishes. | Source Publishing Frequency (KPI-04), by day and week |
| 7 | Analyze the distribution of articles across categories (optional, depends on scope decision). | Category Distribution Share (KPI-05) |
| 8 | Run collection and processing periodically and monitor the pipeline. | Pipeline Success Rate (%); Scraping Failure Rate (%) |
| 9 | Let users filter and explore results by period and source. | Filtered results update correctly; clear message when no records match |

Numeric targets (for example, the number of sources or the collection frequency) are not decided yet. They are listed in the open questions below.

## 3. Scope

**In scope:**
- Web scraping from selected Egyptian news websites
- Data validation, cleaning and standardization
- Duplicate detection
- Grouping related articles into story groups across sources
- A centralized Data Warehouse with historical data
- Analytics and KPIs about news coverage
- Scheduled, automated pipeline runs
- Pipeline monitoring and failure investigation
- Filtering results by reporting period and source

**To be confirmed (scope decision pending):**
- Source management (enable or disable a news source)
- Category distribution analysis

**Out of scope (current version):**
- A news-reading interface for general readers
- Implementation technologies (they will be decided later)

## 4. Assumptions

- The selected news websites are publicly accessible.
- Each article has enough information (title, source, link, publication date) to be stored and compared.
- A suitable method can be found to match the same or similar stories.
- This document follows the Functional Requirements draft (Task 8, version 0.2 pending review). If the baseline changes, this document will be updated.

## 5. Constraints

- The project must be finished by the strict cutoff date of 12/2/2026.
- Implementation starts on 11/6/2026, so the design work must be finished by 11/5/2026.
- No programming language, database or tool has been decided yet.
- Data collection must respect the access conditions of each website.
- Story matching needs a method that is still to be chosen, and pipeline monitoring needs execution logs.

## 6. Open Design Questions

1. How will the system decide that two articles cover the same story? (OQ-01)
2. How should syndicated articles and repeated content be counted? (OQ-02)
3. What is the denominator for source share, and what happens when the total is zero? (OQ-03)
4. What defines a successful, partially successful, failed or missed pipeline run? (OQ-04)
5. Are source management and category distribution part of the first version? (OQ-05)
6. Which time unit should be used for publication time differences, and how are identical timestamps handled? (OQ-06)
7. How long should historical data be kept? (OQ-07)
8. Which news websites will be collected first, and how many?
9. How often should the data be collected?
10. What should happen when a website changes its structure or is not available?
11. Will general readers get a direct interface in a later version?