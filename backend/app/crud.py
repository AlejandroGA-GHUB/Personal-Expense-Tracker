"""
CRUD operations for personal finance tracker
"""
from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas
from .utils.categorizer import learn_from_category_change

def create_transaction_manually(db: Session, transaction: schemas.TransactionCreate) -> models.Transaction:
    """Create a new transaction, category_id optional"""
    db_transaction = models.Transaction(
        description=transaction.description,
        amount=transaction.amount,
        date=transaction.date,
        category_id=transaction.category_id  # Foreign key to categories table
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(db: Session, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    """Get all transactions with pagination"""
    return db.query(models.Transaction).offset(skip).limit(limit).all()

def get_filtered_transactions(db: Session, category_ids: list[int] = None, transaction_type: str = None) -> list[models.Transaction]:
    """Get all applicable transactions when filtering by multiple categories - returns ALL matching results"""
    query = db.query(models.Transaction)

    # Filter by multiple categories (OR logic - match ANY selected category)
    if category_ids is not None and len(category_ids) > 0:
        query = query.filter(models.Transaction.category_id.in_(category_ids))
    
    # All transactions are expenses (negative amounts only)
    return query.all()  # Return ALL matching transactions

def get_transactions_by_category_id(db: Session, category_id: int) -> list[models.Transaction]:
    """Get all transactions by categories with pagination"""
    return db.query(models.Transaction).filter(models.Transaction.category_id == category_id).all()

# Currently a helper crud operation for update_transaction
def get_transaction(db: Session, transaction_id: int) -> models.Transaction:
    """Get a single transaction by ID"""
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()

def update_transaction(db: Session, transaction_id: int, transaction: schemas.TransactionUpdate) -> models.Transaction:
    """Update an existing transaction"""
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        # Track if category changed for learning
        old_category_id = db_transaction.category_id
        category_changed = False
        
        # Update only the fields that are provided
        if transaction.description is not None:
            db_transaction.description = transaction.description
        if transaction.amount is not None:
            db_transaction.amount = transaction.amount
        if transaction.date is not None:
            db_transaction.date = transaction.date
        if transaction.category_id is not None and transaction.category_id != old_category_id:
            db_transaction.category_id = transaction.category_id
            category_changed = True
        
        db.commit()
        db.refresh(db_transaction)
        
        # If category was changed, learn from this correction
        if category_changed:
            learn_from_category_change(db, transaction_id, old_category_id, transaction.category_id)
        
    return db_transaction

def get_categories(db: Session) -> list[models.Category]:
    """Get all categories"""
    return db.query(models.Category).all()

def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    """Create a category, description optional"""
    db_category = models.Category(
        name=category.name,
        description=category.description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def create_transactions_from_csv(db: Session, transactions: list[schemas.TransactionCreateFromCSV]) -> list[models.Transaction]:
    """Create multiple transactions from CSV import"""
    db_transactions = []
    
    for transaction in transactions:
        db_transaction = models.Transaction(
            description=transaction.description,
            amount=transaction.amount,
            date=transaction.date,
            category_id=transaction.category_id,
            source_file=transaction.source_file,
            original_row=transaction.original_row,
            extracted_keywords=transaction.extracted_keywords,
            csv_category_name=transaction.csv_category_name
        )
        db_transactions.append(db_transaction)
    
    # Add all transactions to the session
    db.add_all(db_transactions)
    db.commit()
    
    # Refresh all transactions to get their IDs
    for db_transaction in db_transactions:
        db.refresh(db_transaction)
    
    return db_transactions