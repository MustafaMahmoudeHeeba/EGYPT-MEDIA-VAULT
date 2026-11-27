from fastapi import FastAPI, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import test_connection

from app.routers.articles import router as articles_router
from app.routers.stories import router as stories_router
from app.routers.sources import router as sources_router
from app.routers.categories import router as categories_router
from app.routers.analytics import router as analytics_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "REST API for EGYPT-MEDIA-VAULT. "
        "Provides access to Egyptian news articles, "
        "stories, sources, categories, and analytics."
    ),
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
)


# API Routers
app.include_router(stories_router, prefix=settings.api_v1_prefix)
app.include_router(articles_router, prefix=settings.api_v1_prefix)
app.include_router(sources_router, prefix=settings.api_v1_prefix)
app.include_router(categories_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to EGYPT-MEDIA-VAULT API",
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
    }


@app.get("/ready", tags=["Health"])
def readiness_check():
    try:
        test_connection()
        return {
            "status": "ready",
            "database": "connected",
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        )
