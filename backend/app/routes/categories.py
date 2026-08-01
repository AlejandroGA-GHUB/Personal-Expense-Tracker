"""
Category routes for personal finance tracker
"""
from fastapi import APIRouter, Depends, HTTPException
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
    """Create a new category. Category names are unique."""
    # Reject duplicates up front with a clear 409 instead of letting the
    # UNIQUE constraint raise an IntegrityError that surfaces as a 500.
    if crud.get_category_by_name(db=db, name=category.name):
        raise HTTPException(
            status_code=409,
            detail=f"A category named '{category.name}' already exists"
        )
    new_category = crud.create_category(db=db, category=category)
    return new_category

@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a category. Any transactions filed under it are moved to "Other".

    Path parameters:
    - category_id: ID of the category to delete

    Example: DELETE /api/categories/7
    """
    category = crud.get_category(db=db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail=f"No category with id {category_id}")

    # "Other" is where everything else lands when deleted, and the last resort of
    # the categorization cascade. Removing it would leave both without a target.
    if category.name == "Other":
        raise HTTPException(
            status_code=400,
            detail="The 'Other' category can't be deleted - it's the fallback every other category empties into"
        )

    category_name = category.name
    moved = crud.delete_category(db=db, category=category)

    return {
        "success": True,
        "deleted_category": category_name,
        "transactions_reassigned": moved,
        "message": f"Deleted '{category_name}' and moved {moved} transaction(s) to Other"
    }
