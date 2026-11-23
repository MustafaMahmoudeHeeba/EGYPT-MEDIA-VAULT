
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

from pipeline.egypt_media_vault.config.settings import settings


DATABASE_URL = URL.create(
    drivername="mssql+pyodbc",
    username=settings.azure_sql_username,
    password=settings.azure_sql_password,
    host=settings.azure_sql_server,
    database=settings.azure_sql_database,
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "Encrypt": "yes",
        "TrustServerCertificate": "no",
    },
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


Base = declarative_base()


def get_warehouse_session():
    """Provide a database session and close it after use."""

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def test_warehouse_connection() -> bool:
    """Verify connectivity to the Azure SQL warehouse."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
