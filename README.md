# EGYPT-MEDIA-VAULT

An end-to-end Egyptian news data engineering platform designed to collect, store, process, transform, and analyze news articles from Egyptian news websites.

The platform combines automated data ingestion, cloud storage, data warehousing, orchestration, and a web-based dashboard.

## Architecture

The project uses the following technologies:

| Component | Technology | Responsibility |
|---|---|---|
| Data Ingestion | Python | Scraping and collecting news articles |
| Orchestration | Apache Airflow | Scheduling and managing pipelines |
| Data Lake | Azure Data Lake Storage Gen2 | Bronze and Silver data storage |
| Data Warehouse | Azure SQL Database | Central analytical database |
| Data Transformation | dbt | SQL transformations and data modeling |
| Backend | FastAPI | API endpoints and data access |
| Frontend | Next.js | Interactive dashboard |
| Containerization | Docker Compose | Running Airflow services |

### Architecture Flow

```text
Egyptian News Websites
        |
        v
  Python Ingestion
        |
        v
    Apache Airflow
        |
        v
 Azure Data Lake Storage
     Bronze / Silver
        |
        v
  Azure SQL Database
        |
        v
        dbt
        |
        v
   Analytical Models
        |
        v
      FastAPI
        |
        v
    Next.js Dashboard
```

## Prerequisites

Before running the project, make sure you have installed:

- Python 3.12
- Node.js and npm
- Docker Desktop
- Git
- Visual Studio Code (recommended)

You also need access to the existing Azure resources used by the project.

## 1. Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd EGYPT-MEDIA-VAULT
```

## 2. Configure Environment Variables

The project uses Azure resources that are already provisioned. Developers do not need to create a new SQL Server or Storage Account.

However, each developer must obtain the required configuration and access permissions from the project administrator.

### Azure SQL Database

Required configuration:

| Variable | Description |
|---|---|
| AZURE_SQL_SERVER | Azure SQL Server hostname |
| AZURE_SQL_DATABASE | Database name |
| AZURE_SQL_USERNAME | Database username |
| AZURE_SQL_PASSWORD | Database password |

Example:

```env
AZURE_SQL_SERVER=<YOUR_SERVER>.database.windows.net
AZURE_SQL_DATABASE=<YOUR_DATABASE>
AZURE_SQL_USERNAME=<YOUR_USERNAME>
AZURE_SQL_PASSWORD=<YOUR_PASSWORD>
```

### Azure Data Lake Storage Gen2

The project also requires access to the existing Azure Storage Account.

Obtain the following information from the project administrator, according to the authentication method configured in the project:

- Storage Account name.
- Storage container or filesystem names.
- Required authentication credentials or Microsoft Entra ID permissions.

Use the exact environment variable names defined by the project's configuration templates.

### Environment Files

Configure the environment files required by the project:

- Root `.env`
- `airflow/.env`
- Other component-specific environment files, if required.

Create local copies from the provided `.env.example` or `.env.template` files when available.

**Important:**

- Never commit `.env` files.
- Never expose Azure passwords, account keys, or connection strings.
- Do not replace existing configuration values without understanding their purpose.

## 3. Configure Azure Access

Azure resources are hosted remotely and must be accessible before running the application.

### Azure SQL Firewall

The project administrator must authorize the developer's public IP address in the Azure SQL Server firewall.

Required configuration:

- SQL Server: Existing Azure SQL Server.
- TCP Port: `1433`.
- Firewall rule: Developer's public IP address.

If a connection attempt originates from Docker, the outgoing public IP reported by Azure SQL may differ from the developer's local network address.

Make sure the actual outgoing IP is authorized.

Do not use unrestricted firewall rules.

### Azure Storage Permissions

The developer must have the required access permissions to the existing Storage Account and its containers.

For Microsoft Entra ID authentication, the administrator should assign an appropriate Azure RBAC data role, such as:

- Storage Blob Data Reader (read-only access).
- Storage Blob Data Contributor (read/write access).

The exact permissions depend on the operations performed by the pipeline.

## 4. Set Up Python Environment

The project uses a shared Python virtual environment in its root directory.

Create it if it does not already exist:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies using the dependency manifest provided in the repository.

For example, if a root `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

Keep the virtual environment activated when running Python components locally.

## 5. Start Apache Airflow

Make sure Docker Desktop is running.

Open a terminal:

```bash
cd airflow
```

Start the Airflow services:

```bash
docker compose up -d
```

Check container status:

```bash
docker compose ps
```

The required services should be running, including:

- PostgreSQL (Airflow metadata database).
- Airflow Scheduler.
- Airflow Webserver.

**Note:** The PostgreSQL container is used for Airflow metadata. It is not the project's central Data Warehouse.

Open the Airflow interface:

```text
http://localhost:8080
```

Locate the DAG:

```text
egypt_media_vault_pipeline
```

Enable it if necessary.

You can trigger the DAG manually or allow the configured schedule to run it.

## 6. Start the FastAPI Backend

Open a new terminal:

```bash
cd backend
```

Make sure the root Python virtual environment is activated.

Start the API server:

```bash
uvicorn app.main:app --reload
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## 7. Start the Next.js Frontend

Open another terminal:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the dashboard:

```text
http://localhost:3000
```

Make sure the frontend API configuration points to the locally running FastAPI backend.

## dbt Transformations

dbt transformations are executed automatically as part of the main data pipeline orchestrated by **Apache Airflow**.

You do not need to run dbt manually. Once the Airflow pipeline is triggered, Airflow handles the dbt transformation tasks as part of the workflow.

## 8. Local Service URLs

| Service | URL |
|---|---|
| Airflow | [http://localhost:8080](http://localhost:8080) |
| FastAPI | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| Swagger UI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| Next.js Dashboard | [http://localhost:3000](http://localhost:3000) |

Azure SQL Database and Azure Data Lake Storage Gen2 are cloud-hosted services and do not run locally.

## 9. Recommended Startup Order

For normal local development:

1. Start Docker Desktop.
2. Start Airflow using Docker Compose.
3. Verify Azure SQL and Storage connectivity.
4. Start the FastAPI backend.
5. Start the Next.js frontend.
6. Open the dashboard and verify API communication.
7. Trigger the Airflow DAG when data ingestion or processing is required.

## Troubleshooting

| Problem | Possible Solution |
|---|---|
| Docker containers are not starting | Check Docker Desktop and container logs |
| Azure SQL login timeout | Verify network access, firewall rules, credentials, and connection settings |
| Azure SQL error 40615 | Authorize the actual outgoing public IP in the SQL Server firewall |
| Storage access denied | Verify Storage Account authentication and RBAC permissions |
| `ModuleNotFoundError` | Activate the correct virtual environment and install dependencies |
| Frontend cannot reach the API | Verify that FastAPI is running and check the frontend API URL |
| dbt connection error | Verify the dbt configuration used by the Airflow pipeline and Azure SQL connectivity |

## Project Structure

The repository is organized into separate components:

```text
EGYPT-MEDIA-VAULT/
│
├── airflow/
├── backend/
├── dbt/
├── frontend/
├── infrastructure/
├── pipeline/
│
├── docs/
├── tests/
│
├── .gitignore
└── README.md
```

See the individual component directories and project documentation for implementation details.
