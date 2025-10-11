"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TransactionBase(BaseModel):
    """
    Schema for creating a new transaction via API.
    This validates incoming POST request data.
    """
    description: str = Field(..., max_length=255, description="What was purchased/received")
    amount: float = Field(..., ne=0, description="Dollar amount (negative=expense, positive=income)")
    date: datetime = Field(..., description="When the transaction occurred")
    category_id: Optional[int] = Field(None, description="Which category this belongs to (optional)")
    
class TransactionCreate(TransactionBase):
    """Schema for when creating a transaction manually, say one done with cash"""
    pass

class TransactionCreateFromCSV(TransactionBase):
    """
    Schema for when auto creating transactions from a CSV parse
    """
    source_file: str = Field(..., max_length=255, description="CSV File name which was parsed for this transaction")
    original_row: int = Field(..., gt=0, description="Row that this transaction resides in within its source_file")

class TransactionUpdate(BaseModel):
    """
    For updating existing transactions - all fields optional
    """
    description: Optional[str] = Field(None, max_length=255)
    amount: Optional[float] = Field(None, ne=0)
    date: Optional[datetime] = None
    category_id: Optional[int] = None

class TransactionOut(TransactionBase):
    """
    For API responses - includes all database fields
    """
    id: int                                          # Database primary key
    created_at: datetime                             # Auto-generated timestamp
    updated_at: Optional[datetime] = None            # Auto-updated timestamp
    
    # CSV tracking fields (optional as they'd be only present for CSV-imported transactions)
    source_file: Optional[str] = None                # CSV filename (if imported)
    original_row: Optional[int] = None               # CSV row number (if imported)
    
    class Config:
        from_attributes = True  # Allows SQLAlchemy model → JSON conversion

# Category schemas
class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., max_length=100, description="Category name (e.g., 'Food', 'Transportation')")
    description: Optional[str] = Field(None, max_length=255, description="Optional category description")

class CategoryCreate(CategoryBase):
    """Schema for creating new categories"""
    pass

class CategoryOut(CategoryBase):
    """Schema for category API responses"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
