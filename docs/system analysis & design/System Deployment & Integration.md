# Technology Stack & Architecture

## Technology Stack

| Layer | Technology | Purpose |
| ----- | ---------- | ------- |
| Sources | Youm7 | News source |
| Sources | Al-Masry Al-Youm | News source |
| Sources | Masrawy | News source |
| Scraping & Processing | Python 3.12 | Scraping and processing |
| Scraping & Processing | Requests | HTTP requests |
| Scraping & Processing | BeautifulSoup4 | HTML parsing |
| Storage | Azure Data Lake Storage Gen2 | Data lake storage |
| Storage | Bronze | Raw data layer |
| Storage | Silver | Cleaned data layer |
| Storage | Gold | Analytical data layer |
| Database | Azure Database for PostgreSQL Flexible Server | Database hosting |
| Database | PostgreSQL | Relational database |
| Transformation | dbt | Data transformation |
| Transformation | SQL | Data modeling and analytics |
| Orchestration | Apache Airflow | Pipeline orchestration |
| Backend | FastAPI | REST API |
| Backend | Python | Backend development |
| Frontend | Next.js | Web application |
| Frontend | React | UI development |
| Frontend | TypeScript | Frontend development |
| DevOps | Docker | Containerization |
| DevOps | Git | Version control |
| DevOps | GitHub | Source control and collaboration |
| DevOps | GitHub Actions | CI/CD automation |

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
