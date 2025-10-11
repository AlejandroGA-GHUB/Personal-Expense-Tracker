"""
CRUD operations for personal finance tracker
"""
from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas

def create_transaction_manually(db: Session, transaction: schemas.TransactionCreate) -> models.Transaction:
    """Create a new transaction"""
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

def get_transactions_by_category_id(db: Session, category_id: int) -> list[models.Transaction]:
    """Get all transactions with pagination"""
    return db.query(models.Transaction).filter(models.Transaction.category_id == category_id).all()

# Currently a helper crud operation for update_transaction
def get_transaction(db: Session, transaction_id: int) -> models.Transaction:
    """Get a single transaction by ID"""
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()

def update_transaction(db: Session, transaction_id: int, transaction: schemas.TransactionUpdate) -> models.Transaction:
    """Update an existing transaction"""
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        # Update only the fields that are provided
        if transaction.description is not None:
            db_transaction.description = transaction.description
        if transaction.amount is not None:
            db_transaction.amount = transaction.amount
        if transaction.date is not None:
            db_transaction.date = transaction.date
        if transaction.category_id is not None:
            db_transaction.category_id = transaction.category_id
        
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def get_categories(db: Session) -> list[models.Category]:
    """Get all categories"""
    return db.query(models.Category).all()