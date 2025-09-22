from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# === USER MODEL ===
# This represents users who log into the system

class User(Base):
   
    __tablename__ = "users"  # SQLite table name
    
    # Primary key - unique ID for each user
    id = Column(Integer, primary_key=True, index=True)
    
    # Login credentials
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Never store plain passwords!
    
    # Optional user details
    is_active = Column(Boolean, default=True)  # Can disable users without deleting
    
    # Auto-managed timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship: One user can have many transactions
    # This creates a connection between User and Transaction tables
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


# === CATEGORY MODEL ===
# This represents spending categories (Food, Transport, etc.)

class Category(Base):
   
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category info
    name = Column(String(50), unique=True, index=True, nullable=False)  # "Food & Dining"
    description = Column(Text, nullable=True)  # "Restaurants, groceries, food delivery"
    color = Column(String(7), default="#007bff")  # Hex color for UI charts: "#FF6B6B"
    icon = Column(String(50), nullable=True)  # Emoji or icon name: "🍽️"
    is_default = Column(Boolean, default=False)  # True for system-created categories
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship: One category can be used by many transactions
    transactions = relationship("Transaction", back_populates="category")


# === TRANSACTION MODEL ===
# This is the core model - actual financial transactions

class Transaction(Base):
   
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core transaction data (usually from CSV upload)
    description = Column(String(255), nullable=False)  # "Starbucks Coffee"
    amount = Column(Float, nullable=False)  # -4.50 (negative=expense, positive=income)
    date = Column(DateTime, nullable=False, index=True)  # When it happened
    
    # Links to other tables (foreign keys)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # Can be uncategorized
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Must belong to someone
    
    # CSV upload tracking (for audit trail)
    source_file = Column(String(255), nullable=True)  # "chase_statement_jan2024.csv"
    original_row = Column(Integer, nullable=True)  # Row 15 in the original CSV
    
    # Auto-managed timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - SQLAlchemy will automatically handle JOINs
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    
    # === HELPER PROPERTIES ===
    # These are computed properties, not stored in database
    
    @property
    def is_income(self):
        """Returns True if this is income (positive amount)"""
        return self.amount > 0
    
    @property
    def is_expense(self):
        """Returns True if this is an expense (negative amount)"""
        return self.amount < 0
    
    @property
    def absolute_amount(self):
        """Returns positive version of amount (useful for charts)"""
        return abs(self.amount)


# === DEFAULT CATEGORIES DATA ===
# These will be automatically created when we initialize the database

DEFAULT_CATEGORIES = [
    {
        "name": "Food & Dining", 
        "description": "Restaurants, groceries, food delivery", 
        "color": "#FF6B6B",  # Red
        "icon": "🍽️", 
        "is_default": True
    },
    {
        "name": "Transportation", 
        "description": "Gas, public transport, car maintenance", 
        "color": "#4ECDC4",  # Teal
        "icon": "🚗", 
        "is_default": True
    },
    {
        "name": "Shopping", 
        "description": "Clothing, electronics, general shopping", 
        "color": "#45B7D1",  # Blue
        "icon": "🛍️", 
        "is_default": True
    },
    {
        "name": "Entertainment", 
        "description": "Movies, games, subscriptions", 
        "color": "#96CEB4",  # Green
        "icon": "🎬", 
        "is_default": True
    },
    {
        "name": "Bills & Utilities", 
        "description": "Rent, electricity, internet, phone", 
        "color": "#FFEAA7",  # Yellow
        "icon": "📋", 
        "is_default": True
    },
    {
        "name": "Income", 
        "description": "Salary, freelance, investments", 
        "color": "#98FB98",  # Light Green
        "icon": "💰", 
        "is_default": True
    },
    {
        "name": "Other", 
        "description": "Miscellaneous expenses", 
        "color": "#D3D3D3",  # Gray
        "icon": "📦", 
        "is_default": True
    },
]