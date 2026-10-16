# Task 8 – Functional Requirements

**Project:** EGYPT-MEDIA-VAULT
**Phase:** Requirements Gathering
**Prepared by:** Mustafa Mahmoud

---

## 1. Purpose

This document defines the functional requirements of the EGYPT-MEDIA-VAULT project based on the approved project scope, Task 5 – KPI Catalog, Task 6 – Stakeholder Analysis, and Task 7 – User Stories & Use Cases.

The requirements describe what the system must do to collect, validate, standardize, store, integrate, and analyze news articles from multiple Egyptian news sources. They also cover automated execution, data quality, analytics, and pipeline monitoring.

The document establishes a traceable requirements baseline for subsequent system design, implementation, and testing.

## 2. Requirements Identification and Numbering

Each functional requirement has a unique identifier using the following prefixes.

| Prefix | Category          | Description                                         |
| ------ | ----------------- | --------------------------------------------------- |
| FR-DC  | Data Collection   | Collecting articles from news sources               |
| FR-DQ  | Data Quality      | Validating, standardizing, and detecting duplicates |
| FR-ST  | Story Integration | Grouping related articles across sources            |
| FR-STO | Data Storage      | Preserving historical article and processing data   |
| FR-AN  | Analytics         | Calculating KPIs and comparing news sources         |
| FR-MON | Monitoring        | Tracking pipeline execution and failures            |
| FR-SRC | Source Management | Managing active news sources                        |
| FR-FLT | Filtering         | Filtering and exploring analytical results          |

### 2.1 Priority Definitions

| Priority | Meaning                                                           |
| -------- | ----------------------------------------------------------------- |
| Must     | Essential for the core project scope and acceptance               |
| Should   | Important, but may be deferred if scope or constraints require it |
| Could    | Optional enhancement that can be implemented if time permits      |

Priorities are proposed and should be confirmed during requirements review.

## 3. Functional Requirements

### 3.1 Data Collection

| ID       | Functional Requirement                                                                                                           | Priority | Source       |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------ |
| FR-DC-01 | The system shall collect available news articles from configured and active Egyptian news sources.                               | Must     | US-01        |
| FR-DC-02 | The system shall capture the article title, source name, publication date and time, and original article URL whenever available. | Must     | US-01, US-07 |
| FR-DC-03 | The system shall continue collecting articles from other available sources when an individual source fails.                      | Must     | US-01        |
| FR-DC-04 | The system shall support scheduled execution of the article collection process.                                                  | Must     | US-02        |
| FR-DC-05 | The system shall record the start time, end time, and execution outcome of each collection run.                                  | Must     | US-02, US-15 |
| FR-DC-06 | The system shall make missed or unsuccessful scheduled executions identifiable in the execution history.                         | Must     | US-02, US-15 |
| FR-DC-07 | The system shall respect applicable source access conditions and collection restrictions.                                        | Should   | US-04        |

### 3.2 Data Validation and Quality

| ID       | Functional Requirement                                                                                                     | Priority | Source       |
| -------- | -------------------------------------------------------------------------------------------------------------------------- | -------- | ------------ |
| FR-DQ-01 | The system shall validate collected articles against the required data fields before including them in analytical results. | Must     | US-05        |
| FR-DQ-02 | The system shall standardize article metadata, including source names and publication timestamps, into consistent formats. | Must     | US-05        |
| FR-DQ-03 | The system shall flag articles with missing or invalid required fields and record the reason for the validation failure.   | Must     | US-05        |
| FR-DQ-04 | The system shall exclude articles that fail mandatory validation rules from affected analytical calculations.              | Must     | US-05        |
| FR-DQ-05 | The system shall detect duplicate article records and prevent duplicate records from inflating article counts.             | Must     | US-01, US-06 |
| FR-DQ-06 | The system shall make duplicate detection results available for analysis by source and reporting period.                   | Should   | US-06        |
| FR-DQ-07 | The system shall preserve the original source attribution and article URL for collected articles whenever available.       | Must     | US-07        |
| FR-DQ-08 | The system shall calculate and report data completeness for each collection run.                                           | Must     | US-05        |

*Note:* The final rules for distinguishing duplicate articles from syndicated copies must be documented before implementation. Syndicated copies may be relevant to cross-source coverage analysis and must not automatically be treated as ordinary duplicates.

### 3.3 Story Grouping and Cross-Source Integration

| ID       | Functional Requirement                                                                                                                                                | Priority | Source       |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------ |
| FR-ST-01 | The system shall group articles identified as covering the same news story across different sources.                                                                  | Must     | US-11        |
| FR-ST-02 | The system shall provide an approved and documented rule for determining whether articles belong to the same story group.                                             | Must     | US-11        |
| FR-ST-03 | The system shall associate each story group with its member articles and the corresponding source information.                                                        | Must     | US-11, US-12 |
| FR-ST-04 | The system shall display story groups even when a story is covered by only one source.                                                                                | Must     | US-11        |
| FR-ST-05 | The system shall display the number of distinct sources covering each story group.                                                                                    | Must     | US-11        |
| FR-ST-06 | The system shall allow users to inspect the articles within a story group, including each article's source, title, publication time, and original URL when available. | Must     | US-12        |

*Dependency:* The story-matching approach and acceptance criteria must be agreed upon before FR-ST-01 can be considered fully testable.

### 3.4 Historical Data Storage

| ID        | Functional Requirement                                                                                                | Priority | Source                     |
| --------- | --------------------------------------------------------------------------------------------------------------------- | -------- | -------------------------- |
| FR-STO-01 | The system shall preserve collected article records and their relevant metadata for historical analysis.              | Must     | US-01, US-17               |
| FR-STO-02 | The system shall maintain the relationship between articles, their original sources, and their assigned story groups. | Must     | US-07, US-11               |
| FR-STO-03 | The system shall preserve collection-run history and associated execution results for monitoring and investigation.   | Must     | US-02, US-15, US-16        |
| FR-STO-04 | The system shall retain sufficient historical information to support comparisons across reporting periods.            | Must     | US-08, US-09, US-10, US-17 |

The storage technology, retention duration, and physical data model are design decisions and are not prescribed by these functional requirements.

### 3.5 Analytics and KPI Calculation

| ID       | Functional Requirement                                                                                                                                                 | Priority | Source        |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------- |
| FR-AN-01 | The system shall calculate the total number of valid collected articles for each selected source and reporting period.                                                 | Must     | US-08; KPI-01 |
| FR-AN-02 | The system shall compare article volumes across selected news sources.                                                                                                 | Must     | US-09; KPI-01 |
| FR-AN-03 | The system shall calculate each source's share of the total article volume for the selected reporting period and filters.                                              | Must     | US-09         |
| FR-AN-04 | The system shall calculate cross-source story coverage using the number of distinct sources associated with each story group.                                          | Must     | US-11; KPI-02 |
| FR-AN-05 | The system shall calculate publication time differences between articles covering the same story, measured from the earliest valid publication timestamp in the group. | Must     | US-13; KPI-03 |
| FR-AN-06 | The system shall calculate the publishing frequency of each source by day and week.                                                                                    | Must     | US-10; KPI-04 |
| FR-AN-07 | The system should provide an analysis of publishing activity by hour when sufficient valid timestamp data is available.                                                | Should   | US-10         |
| FR-AN-08 | The system should calculate the distribution of articles across categories for each source and selected reporting period.                                              | Should   | US-14; KPI-05 |
| FR-AN-09 | The system shall display zero article counts when a source has no valid articles for the selected period, rather than displaying a misleading blank value.             | Must     | US-08         |
| FR-AN-10 | The system shall exclude invalid publication timestamps from publication timing calculations and make the affected records identifiable.                               | Must     | US-13         |

### 3.6 Pipeline Monitoring and Failure Investigation

| ID        | Functional Requirement                                                                                                                    | Priority | Source       |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------ |
| FR-MON-01 | The system shall maintain a history of pipeline executions, including execution times and final statuses.                                 | Must     | US-02, US-15 |
| FR-MON-02 | The system shall record the number of articles processed by each source during a collection run when that information is available.       | Must     | US-15        |
| FR-MON-03 | The system shall distinguish successful, partially successful, failed, and missed executions where applicable.                            | Must     | US-02, US-15 |
| FR-MON-04 | The system shall allow users to inspect collection failures by source, processing step, and available error details.                      | Must     | US-16        |
| FR-MON-05 | The system shall calculate pipeline success and source failure rates over a selected reporting period using documented calculation rules. | Must     | US-15, US-16 |
| FR-MON-06 | The system shall provide sufficient execution information to help users investigate unsuccessful collection runs.                         | Must     | US-16        |

*Note:* The exact definitions of a successful run, a partially successful run, and a failed run must be agreed upon before the monitoring KPIs are finalized.

### 3.7 News Source Management

| ID        | Functional Requirement                                                                                                          | Priority                               | Source       |
| --------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ------------ |
| FR-SRC-01 | The system should allow an authorized user to enable or disable a configured news source.                                       | Should                                 | US-03        |
| FR-SRC-02 | The system shall exclude disabled sources from scheduled collection runs.                                                       | Must, if source management is included | US-03        |
| FR-SRC-03 | The system should maintain the configuration information required to identify and collect articles from each configured source. | Should                                 | US-03, US-04 |

The scope of source management and the identity of the authorized user must be confirmed during requirements review.

### 3.8 Filtering and Analytical Exploration

| ID        | Functional Requirement                                                                                                 | Priority | Source       |
| --------- | ---------------------------------------------------------------------------------------------------------------------- | -------- | ------------ |
| FR-FLT-01 | The system shall allow users to filter analytical results by reporting period and news source.                         | Must     | US-17        |
| FR-FLT-02 | The system should allow users to filter analytical results by article category when category information is available. | Should   | US-14, US-17 |
| FR-FLT-03 | The system shall update the relevant analytical results according to the selected filters.                             | Must     | US-17        |
| FR-FLT-04 | The system shall display a clear empty-result state when no records match the selected filters.                        | Must     | US-17        |
| FR-FLT-05 | The system shall support historical comparisons across available reporting periods.                                    | Must     | US-17        |

## 4. KPI Traceability

The following table links the KPIs defined in Task 5 to their corresponding functional requirements.

| KPI ID | KPI Name                    | Related Functional Requirements | Priority      |
| ------ | --------------------------- | ------------------------------- | ------------- |
| KPI-01 | Total Articles Ingested     | FR-AN-01, FR-AN-02, FR-AN-09    | Must          |
| KPI-02 | Cross-Source Story Coverage | FR-ST-01, FR-ST-05, FR-AN-04    | Must          |
| KPI-03 | Publication Time Delta      | FR-AN-05, FR-AN-10              | Must          |
| KPI-04 | Source Publishing Frequency | FR-AN-06, FR-AN-07              | Must / Should |
| KPI-05 | Category Distribution Share | FR-AN-08, FR-FLT-02             | Should        |

### 4.1 Additional Operational Measures

The following measures are supported by the requirements but should be confirmed and documented in the KPI Catalog if they are to be treated as formal KPIs.

| Measure                  | Related Functional Requirements |
| ------------------------ | ------------------------------- |
| Data Completeness        | FR-DQ-01, FR-DQ-03, FR-DQ-08    |
| Duplicate Article Rate   | FR-DQ-05, FR-DQ-06              |
| Source Share             | FR-AN-03                        |
| Pipeline Success Rate    | FR-MON-03, FR-MON-05            |
| Scraping Failure Rate    | FR-MON-04, FR-MON-05            |
| Attribution Completeness | FR-DQ-07                        |

## 5. Requirements Traceability Matrix (RTM)

The Requirements Traceability Matrix links the user stories and KPIs to the functional requirements, providing a basis for verifying that the project's needs are covered.

| User Story / KPI                     | Related Functional Requirements                       | Coverage                    |
| ------------------------------------ | ----------------------------------------------------- | --------------------------- |
| US-01 – Collect Articles             | FR-DC-01, FR-DC-02, FR-DC-03, FR-DQ-05, FR-STO-01     | Covered                     |
| US-02 – Schedule Collection          | FR-DC-04, FR-DC-05, FR-DC-06, FR-MON-01, FR-MON-03    | Covered                     |
| US-03 – Manage Sources               | FR-SRC-01, FR-SRC-02, FR-SRC-03                       | Scope confirmation required |
| US-04 – Respect Source Conditions    | FR-DC-07, FR-SRC-03                                   | Covered at a high level     |
| US-05 – Validate and Standardize     | FR-DQ-01, FR-DQ-02, FR-DQ-03, FR-DQ-04, FR-DQ-08      | Covered                     |
| US-06 – Detect Duplicates            | FR-DQ-05, FR-DQ-06                                    | Business rules pending      |
| US-07 – Preserve Attribution         | FR-DQ-07, FR-STO-02                                   | Covered                     |
| US-08 – Count Articles               | FR-AN-01, FR-AN-09                                    | Covered                     |
| US-09 – Compare Sources              | FR-AN-02, FR-AN-03, FR-FLT-01                         | Covered                     |
| US-10 – Analyze Publishing Frequency | FR-AN-06, FR-AN-07                                    | Covered                     |
| US-11 – Group Related Stories        | FR-ST-01, FR-ST-02, FR-ST-03, FR-ST-04, FR-ST-05      | Matching rule pending       |
| US-12 – Inspect Story Articles       | FR-ST-03, FR-ST-06                                    | Covered                     |
| US-13 – Compare Publication Timing   | FR-AN-05, FR-AN-10                                    | Covered                     |
| US-14 – Analyze Categories           | FR-AN-08, FR-FLT-02                                   | Optional scope              |
| US-15 – Monitor Pipeline             | FR-DC-05, FR-MON-01, FR-MON-02, FR-MON-03, FR-MON-05  | Status definitions pending  |
| US-16 – Investigate Failures         | FR-MON-04, FR-MON-05, FR-MON-06                       | Covered                     |
| US-17 – Filter and Explore           | FR-FLT-01, FR-FLT-02, FR-FLT-03, FR-FLT-04, FR-FLT-05 | Covered                     |
| KPI-01 – Total Articles Ingested     | FR-AN-01, FR-AN-02, FR-AN-09                          | Covered                     |
| KPI-02 – Cross-Source Story Coverage | FR-ST-01, FR-ST-05, FR-AN-04                          | Matching rule pending       |
| KPI-03 – Publication Time Delta      | FR-AN-05, FR-AN-10                                    | Covered                     |
| KPI-04 – Source Publishing Frequency | FR-AN-06, FR-AN-07                                    | Covered                     |
| KPI-05 – Category Distribution Share | FR-AN-08, FR-FLT-02                                   | Optional scope              |

## 6. Open Questions and Decisions Required

The following questions must be resolved or explicitly accepted as limitations before the requirements baseline is approved.

| ID    | Open Question                                                                            | Impacted Requirements                     | Required Decision                                                    |
| ----- | ---------------------------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------- |
| OQ-01 | How will the system determine whether two articles cover the same story?                 | FR-ST-01, FR-ST-02, FR-ST-05, FR-AN-04    | Define and approve the story-matching rules and acceptance criteria. |
| OQ-02 | How should syndicated articles and repeated content be handled?                          | FR-DQ-05, FR-DQ-06, FR-AN-01, FR-AN-04    | Define duplicate detection and syndicated-content counting rules.    |
| OQ-03 | What is the denominator for source share, and how should a zero-total period be handled? | FR-AN-03                                  | Define the calculation and zero-total behavior.                      |
| OQ-04 | What defines a successful, partially successful, failed, or missed pipeline run?         | FR-MON-01, FR-MON-03, FR-MON-05           | Approve execution status definitions and success-rate calculation.   |
| OQ-05 | Are source management and category distribution included in the initial project scope?   | FR-SRC-01, FR-SRC-02, FR-SRC-03, FR-AN-08 | Confirm the scope and priorities.                                    |
| OQ-06 | What time unit and comparison rules should be used for publication time differences?     | FR-AN-05                                  | Confirm the reporting unit and handling of identical timestamps.     |
| OQ-07 | What historical retention period is required?                                            | FR-STO-01, FR-STO-03, FR-STO-04           | Confirm retention expectations and any constraints.                  |

## 7. Requirements Change Log

All changes to the requirements baseline must be documented to preserve traceability and prevent unreviewed scope changes.

| Version | Date       | Change Description                                                            | Status           |
| ------- | ---------- | ----------------------------------------------------------------------------- | ---------------- |
| 0.1     | 14/10/2026 | Initial functional requirements draft derived from Tasks 5, 6, and 7.         | Draft            |
| 0.2     | Pending    | Update requirements based on review feedback and decisions on open questions. | Pending Review   |
| 1.0     | Pending    | Approve the reviewed requirements as the project baseline.                    | Pending Approval |

### 7.1 Change Management Rules

1. Every proposed change shall identify the affected requirement IDs.
2. The change shall include a reason and its expected impact on scope, dependencies, and acceptance criteria.
3. The project team shall review the change before incorporating it into the baseline.
4. Approved changes shall update the functional requirements, RTM, and relevant project documents.
5. The change log shall preserve previous versions and record the approval status.

## 8. Quality and Acceptance Checks

The functional requirements shall be considered ready for baseline approval when the following checks are satisfied.

- [ ] Every functional requirement has a unique ID.
- [ ] Each requirement describes one clear and testable system behavior.
- [ ] Each requirement has a priority and a traceable source.
- [ ] All five core KPIs from Task 5 map to at least one functional requirement.
- [ ] All 17 user stories from Task 7 map to one or more functional requirements, or have a documented scope decision.
- [ ] Data collection, validation, standardization, historical storage, cross-source integration, analytics, scheduling, and monitoring are covered.
- [ ] No unconfirmed implementation technology is imposed by the functional requirements.
- [ ] Duplicate or conflicting requirements have been reviewed.
- [ ] Open questions and assumptions are documented.
- [ ] The RTM is consistent with the latest user stories and KPI catalog.
- [ ] The project reviewer has confirmed the baseline.

## 9. Definition of Done

Task 8 is complete when:

1. The functional requirements document has been reviewed.
2. All requirements have unique identifiers, priorities, and traceable sources.
3. Every in-scope user story and core KPI maps to at least one functional requirement.
4. Open questions have been resolved or formally recorded as pending decisions.
5. The Requirements Traceability Matrix has been checked for coverage and consistency.
6. The requirements change log has been established.
7. The reviewer has approved the baseline version.

**Final Status:** Proposed Functional Requirements Baseline – Pending Review and Approval.
