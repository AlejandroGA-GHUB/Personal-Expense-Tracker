"""
Category routes for personal finance tracker
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

# Create router instance
router = APIRouter()

@router.get("/", response_model=list[schemas.CategoryOut])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = crud.get_categories(db)
    return categories

@router.post("/", response_model=schemas.CategoryOut)
async def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new category"""
    new_category = crud.create_category(db=db, category=category)
    return new_category