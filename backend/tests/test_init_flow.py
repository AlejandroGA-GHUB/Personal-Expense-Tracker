#!/usr/bin/env python3
import app.database as db

# Testing file to verify the database initialization working correctly
print("1️⃣ Init (should show 'already exists' if made prior, initializing if not)")
db.init_database()

print("\n2️⃣ Reset and re create the database as reset_database calls init")
reset_result = db.reset_database()
print(reset_result['status'])

print("\n3️⃣ Init again (should always show 'already exists' now)")
db.init_database()