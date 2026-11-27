from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.source import SourceResponse
from app.services.source_service import (
    list_sources,
    retrieve_source,
)


router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
)


@router.get(
    "",
    response_model=list[SourceResponse],
    summary="List news sources",
)
def get_sources_endpoint(
    db: Session = Depends(get_db),
):
    return list_sources(db)


@router.get(
    "/{source_id}",
    response_model=SourceResponse,
    summary="Get source details",
)
def get_source_endpoint(
    source_id: str,
    db: Session = Depends(get_db),
):
    return retrieve_source(db, source_id)