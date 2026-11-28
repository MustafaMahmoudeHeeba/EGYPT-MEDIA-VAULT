from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import (
    list_categories,
    retrieve_category,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List news categories",
)
def get_categories_endpoint(
    db: Session = Depends(get_db),
):
    return list_categories(db)


@router.get(
    "/{category_key}",
    response_model=CategoryResponse,
    summary="Get category details",
)
def get_category_endpoint(
    category_key: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    return retrieve_category(db, category_key)