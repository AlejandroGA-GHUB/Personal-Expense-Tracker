"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction via API.
    This validates incoming POST request data.
    """
    description: str = Field(..., max_length=255, description="What was purchased/received")
    amount: float = Field(..., description="Dollar amount (negative=expense, positive=income)")
    date: datetime = Field(..., description="When the transaction occurred")
    category_id: Optional[int] = Field(None, description="Which category this belongs to (optional)")
    
    @validator('amount')
    def amount_cannot_be_zero(cls, v):
        """Custom validation: amount must not be zero"""
        if v == 0:
            raise ValueError('Transaction amount cannot be zero')
        return v
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        """Custom validation: clean up description"""
        v = v.strip()
        if not v:
            raise ValueError('Description cannot be empty')
        return v

# Example usage in FastAPI route:
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import get_db

@app.post("/transactions/")
async def create_transaction(
    transaction_data: TransactionCreate,  # <-- Pydantic validates this automatically
    db: Session = Depends(get_db)
):
    # transaction_data is now a validated TransactionCreate object
    # You can access: transaction_data.description, transaction_data.amount, etc.
    pass
"""
