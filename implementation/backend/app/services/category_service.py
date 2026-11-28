from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.category_repository import (
    get_categories,
    get_category_by_id,
)


def list_categories(db: Session):
    return get_categories(db)


def retrieve_category(db: Session, category_key: int):
    category = get_category_by_id(db, category_key)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category_key}' not found.",
        )

    return category