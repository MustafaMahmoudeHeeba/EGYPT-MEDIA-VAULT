
FROM apache/airflow:2.10.5

USER root

RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        gcc \
        g++ \
        unixodbc-dev \
        msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    requests \
    beautifulsoup4 \
    sqlalchemy \
    pyodbc \
    pydantic \
    pydantic-settings \
    azure-storage-file-datalake \
    sentence-transformers \
    scikit-learn

RUN pip install --no-cache-dir \
    "numpy==1.26.4" \
    "scipy==1.15.3"

# Install Docker Provider compatible with Airflow 2.10.5
RUN pip install --no-cache-dir \
    apache-airflow-providers-docker \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"
