# Task 4 – Risk Assessment & Mitigation Plan
**Responsible:** Mohamed Abdelmotaleb  **Phase:** Project Planning

## 1. Executive Summary & Objective
This document outlines the risk management plan for the **EGYPT-MEDIA-VAULT** project prior to implementation. It identifies, assesses, and provides mitigation strategies for potential risks across scope, schedule, data collection, data quality, legal/ethical compliance, and team coordination.

## 2. Risk Register & Evaluation
| Risk ID | Category | Risk Description | Likelihood | Impact | Risk Rating | Primary Owner | Mitigation Strategy | Contingency Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R01** | Data Sources | Changes in Egyptian news site structures (e.g., Youm7, Masrawy) breaking scraping rules. | High | High | **High** | Mohamed Abdelmotaleb | Implement modular/flexible parser designs and automated fallback extraction logic. | Manual structure re-mapping and fallback to generic selector rules. |
| **R02** | Schedule | Overlapping early planning and requirements tasks (Tasks 4–7) causing deadline compression. | High | Medium | **High** | Mohamed Abdelmotaleb | Establish early draft handoffs and clear subtask ownership boundaries. | Utilize buffer days (e.g., 10/15) for alignment and correction before baseline lock. |
| **R03** | Legal & Ethical | Terms of service updates or anti-bot measures restricting data collection. | Medium | High | **High** | Ahmed Eladawy | Adhere to polite scraping practices, respect rate limits, and maintain source transparency. | Pause collection on affected domains; analyze alternative open public feeds or APIs. |
| **R04** | Data Quality | Inconsistent Arabic text formats, duplicates, or missing publication metadata across news portals. | High | Medium | **High** | Mohamed Abdelmotaleb | Define strict data standardization rules and validation checks during ingestion. | Flag anomalous data for automatic quarantine prior to warehouse loading. |
| **R05** | Requirements | Scope creep or unverified assumptions regarding similarity calculation/clustering across stories. | Medium | Medium | **Medium** | Mustafa Mahmoud | Maintain a locked baseline with formal change management for any new scope additions. | Defer optional or non-core KPI metrics to post-implementation phases. |

## 3. High-Impact Risks Affecting Architecture & Requirements
- **R01 & R03 (Scraping & Legal Limits):** Directly impact **Non-functional Requirements (Task 9)** for system resilience and logging rate-limit responses.
- **R04 (Data Quality):** Informs **Database Design & Data Modeling (Task 11)** regarding data standardization, cleaning rules, and staging areas.
