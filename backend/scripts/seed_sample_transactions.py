"""
Seed the database with sample transactions

Writes 50 identical placeholder expenses into whatever database DATABASE_URL
resolves to, for filling out an empty dashboard by hand. Run from backend/.

Was tests/test_create_manual_transaction.py - moved here because it writes to the
real database, which is a seeding job rather than a test.
"""
import os
import sys
from datetime import datetime

# Allow running this script directly from backend/ - without this, sys.path[0] is
# scripts/ and "import app" fails.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.database as db
import app.crud as crud
import app.schemas as schemas
from app.database import SessionLocal


def seed_sample_transactions(count: int = 50):
    """Create placeholder expenses so the dashboard has something to show"""
    # Initialize database only if needed
    db_info = db.get_database_info()
    if db_info.get('categories', 0) == 0:
        db.init_database()

    # Create database session
    session = SessionLocal()

    try:
        # Create a transaction. The amount must be negative - this app tracks
        # expenses only, and TransactionCreate rejects anything >= 0.
        for i in range(count):
            transaction_data = schemas.TransactionCreate(
                description="Coffee",
                amount=-4.50,
                date=datetime.now(),
                category_id=1
            )

            # Create the transaction using CRUD
            created_transaction = crud.create_transaction_manually(
                db=session,
                transaction=transaction_data
            )

            print(f"[ok] Created transaction ID: {created_transaction.id}")

    finally:
        session.close()

if __name__ == "__main__":
    seed_sample_transactions()
