FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /usr/app/dbt

# Install system dependencies and Microsoft ODBC Driver 18
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        git \
        unixodbc-dev \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb \
        https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

COPY dbt/requirements-dbt.txt /tmp/requirements-dbt.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements-dbt.txt

RUN mkdir -p /root/.dbt

WORKDIR /usr/app/dbt

CMD ["dbt", "--version"]
