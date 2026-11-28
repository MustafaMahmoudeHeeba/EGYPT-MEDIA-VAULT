from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.source_repository import (
    get_source_by_id,
    get_sources,
)


def list_sources(db: Session):
    return get_sources(db)


def retrieve_source(db: Session, source_id: str):
    source = get_source_by_id(db, source_id)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found.",
        )

    return source