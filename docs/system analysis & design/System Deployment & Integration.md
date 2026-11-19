# Technology Stack & Architecture

## Technology Stack

| Layer | Technology | Purpose | Status |
| ----- | ---------- | ------- | ------ |
| Sources | Youm7 | News source | Implemented |
| Sources | Al-Masry Al-Youm | News source | Implemented |
| Sources | Masrawy | News source | Implemented |
| Scraping & Processing | Python 3.12 | Scraping and processing | Implemented |
| Scraping & Processing | Requests | HTTP requests | Implemented |
| Scraping & Processing | BeautifulSoup4 | HTML parsing | Implemented |
| Storage | Azure Data Lake Storage Gen2 | Data lake storage | In Progress |
| Storage | Bronze | Raw data layer | In Progress |
| Storage | Silver | Cleaned data layer | In Progress |
| Storage | Gold | Analytical data layer | In Progress |
| Database | Azure Database for PostgreSQL Flexible Server | Database hosting | In Progress |
| Database | PostgreSQL | Relational database | In Progress |
| Transformation | dbt | Data transformation | Planned |
| Transformation | SQL | Data modeling and analytics | Planned |
| Orchestration | Apache Airflow | Pipeline orchestration | Planned |
| Backend | FastAPI | REST API | Planned |
| Backend | Python | Backend development | Planned |
| Frontend | Next.js | Web application | Planned |
| Frontend | React | UI development | Planned |
| Frontend | TypeScript | Frontend development | Planned |
| DevOps | Docker | Containerization | Planned |
| DevOps | Git | Version control | Implemented |
| DevOps | GitHub | Source control and collaboration | Implemented |
| DevOps | GitHub Actions | CI/CD automation | Planned |

## End-to-End Architecture

```mermaid
flowchart TD

    A["Egyptian News Websites<br/>Youm7 • Al-Masry Al-Youm • Masrawy"]

    B["Python 3.12<br/>Requests + BeautifulSoup4<br/>Web Scraping"]

    C["Python Processing<br/>Validation • Normalization<br/>Deduplication • Story Clustering"]

    D["Azure Data Lake Storage Gen2<br/>Bronze → Silver → Gold"]

    E["Azure Database for PostgreSQL Flexible Server<br/>PostgreSQL"]

    F["dbt + SQL<br/>Data Warehouse / Data Marts"]

    G["FastAPI<br/>REST API"]

    H["Next.js + React + TypeScript<br/>Web Dashboard"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H

    AF["Apache Airflow<br/>Pipeline Orchestration"]

    AF -.-> B
    AF -.-> C
    AF -.-> D
    AF -.-> E
    AF -.-> F
