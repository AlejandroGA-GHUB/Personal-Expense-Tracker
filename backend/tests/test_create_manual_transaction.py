"""
Test manual transaction creation
"""
from datetime import datetime
from decimal import Decimal

import app.database as db
import app.crud as crud
import app.schemas as schemas
from app.database import SessionLocal


def test_create_manual_transaction():
    """Test creating a manual transaction"""
    # Initialize database only if needed
    db_info = db.get_database_info()
    if db_info.get('categories', 0) == 0:
        db.init_database()
    
    # Create database session
    session = SessionLocal()
    
    try:
        # Create a transaction
        for i in range(50):
            transaction_data = schemas.TransactionCreate(
                description="Paycheck",
                amount=4.50,
                date=datetime.now(),
                category_id=1
            )
        
            # Create the transaction using CRUD
            created_transaction = crud.create_transaction_manually(
                db=session, 
                transaction=transaction_data
            )
        
            print(f"✅ Created transaction ID: {created_transaction.id}")
        
    finally:
        session.close()

if __name__ == "__main__":
    test_create_manual_transaction()

