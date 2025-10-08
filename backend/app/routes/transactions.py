"""
Transaction routes for personal finance tracker
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

# Create router instance
router = APIRouter()

@router.post("/", response_model=schemas.TransactionOut)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction manually
    
    Example request body:
    {
        "description": "Coffee at Starbucks",
        "amount": -25.50,
        "date": "2025-10-03T10:30:00",
        "category_id": 1
    }
    
    Note: 
    - Negative amount = expense
    - Positive amount = income
    - category_id references the categories table
    """
    return crud.create_transaction_manually(db=db, transaction=transaction)

@router.get("/", response_model=list[schemas.TransactionOut])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all transactions with pagination
    
    Query parameters:
    - skip: Number of transactions to skip (default: 0)
    - limit: Maximum number of transactions to return (default: 100)
    
    Example: GET /api/transactions/?skip=0&limit=50
    """
    transactions = crud.get_transactions(db, skip=skip, limit=limit)
    return transactions

@router.get("/category/{category_id}", response_model=list[schemas.TransactionOut])
async def get_transactions_by_category_id(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all transactions for a specific category
    
    Path parameters:
    - category_id: ID of the category to filter by
    
    Example: GET /api/transactions/category/1
    """
    transactions = crud.get_transactions_by_category_id(db=db, category_id=category_id)
    return transactions


@router.patch("/{transaction_id}", response_model=schemas.TransactionOut)
async def update_transaction(
    transaction_id: int,                    
    transaction: schemas.TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates an individual transaction chosen by the user

    Path parameters:
    - transaction_id: ID of the transaction to update (from URL)

    Request body (all fields optional for PATCH), amount omitted in this example:
    {
        "description": "Updated coffee purchase",
        "date": "2025-10-03T10:30:00", 
        "category_id": 2
    }

    Note:
    - Only include fields you want to change
    - Omitted fields will remain unchanged
    - All fields are optional (partial update)

    Example: PATCH /api/transactions/50
    """
    return crud.update_transaction(db=db, transaction_id=transaction_id, transaction=transaction)