
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


# Build the Azure SQL connection URL safely.
# URL.create() handles special characters in username/password.
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


# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=settings.sql_pool_recycle,
    pool_size=settings.sql_pool_size,
    max_overflow=settings.sql_max_overflow,
    echo=settings.debug,
)


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for application dependencies.

    The session is always closed after use.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """
    Test connectivity to Azure SQL Database.

    Returns:
        True when the database connection is successful.
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
