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
    description: str = Field(..., max_length=255, description="What was purchased")
    amount: float = Field(..., description="Dollar amount (negative for expenses)")
    date: datetime = Field(..., description="When the transaction occurred")
    category_id: Optional[int] = Field(None, description="Which category this belongs to (optional)")
    
class TransactionCreate(TransactionBase):
    """Schema for when creating a transaction manually, say one done with cash"""
    # The app tracks expenses only, so a positive amount is rejected rather than
    # silently stored as income. Constrained here rather than on TransactionBase
    # so TransactionOut can still serialize any legacy rows.
    amount: float = Field(..., lt=0, description="Dollar amount, negative (expenses only)")

class TransactionCreateFromCSV(TransactionBase):
    """
    Schema for when auto creating transactions from a CSV parse
    """
    source_file: str = Field(..., max_length=255, description="CSV File name which was parsed for this transaction")
    original_row: int = Field(..., gt=0, description="Row that this transaction resides in within its source_file")
    extracted_keywords: Optional[str] = Field(None, max_length=500, description="Comma-separated keywords for learning")
    csv_category_name: Optional[str] = Field(None, max_length=500, description="Original CSV category name")
    # Preview-only hint: a category the LLM proposed that doesn't exist yet.
    # Never persisted - it exists so the user can approve it during upload.
    llm_suggested_category: Optional[str] = Field(None, max_length=100, description="New category proposed by the local LLM")
    # Preview-only: which stage of the cascade picked the category, so the UI can
    # credit the right one instead of calling every guess "AI". See categorizer.SOURCE_*.
    categorization_source: Optional[str] = Field(None, max_length=50, description="Which cascade stage chose the category")

class TransactionUpdate(BaseModel):
    """
    For updating existing transactions - all fields optional
    """
    description: Optional[str] = Field(None, max_length=255)
    amount: Optional[float] = Field(None, lt=0, description="Dollar amount, negative (expenses only)")
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
