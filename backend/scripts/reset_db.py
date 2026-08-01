"""
Reset the database
Create -> Reset -> Create

WARNING: this DROPS every table in the database it resolves to, wiping all
transactions and learned keywords. DATABASE_URL is relative to the current working
directory, so run this from backend/ to hit backend/finance.db.

Deliberately named reset_db.py and kept out of tests/ - it used to be
tests/test_init_flow.py, where pytest would collect the function below and destroy
the real database on a plain `pytest` run.
"""
import os
import sys

# Allow running this script directly from backend/ - without this, sys.path[0] is
# scripts/ and "import app" fails.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.database as db

def reset_db():
    # Verifies the database initialization is working correctly
    # NOTE: output stays ASCII-only; emoji crash the Windows cp1252 console.
    print("[1] Init (should show 'already exists' if made prior, initializing if not)")
    db.init_database()

    print("\n[2] Reset and re create the database as reset_database calls init")
    reset_result = db.reset_database()
    print(reset_result['status'])

    print("\n[3] Init again (should always show 'already exists' now)")
    db.init_database()

if __name__ == "__main__":
    reset_db()
