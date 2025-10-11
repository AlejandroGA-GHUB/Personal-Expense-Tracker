"""
Database configuration for distributed personal finance tracker.
Each user gets their own local SQLite database file.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import sqlite3

# === DISTRIBUTED DATABASE CONFIGURATION ===
# Each user has their own local SQLite file - no authentication needed

# Database file location (in user's current directory)
DATABASE_URL = "sqlite:///./finance.db"

# Create SQLAlchemy engine for local SQLite
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},  # Allow multiple threads for FastAPI
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Import models to register them with Base (must be after Base is defined)
from . import models

# === SQLITE OPTIMIZATION ===
# Enable foreign key constraints and WAL mode for better performance

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite for optimal performance and data integrity"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")
        # Optimize for performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

# === DATABASE SESSION MANAGEMENT ===

def get_db():
    """
    Dependency injection for FastAPI routes.
    Creates a new database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === DATABASE INITIALIZATION ===

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def init_database():
    """
    Initialize database with tables and default data.
    Call this on application startup.
    """
    # Create tables
    create_tables()
    
    # Add default categories if database is empty
    from .models import Category, DEFAULT_CATEGORIES
    
    db = SessionLocal()
    try:
        # Check if categories already exist
        existing_categories = db.query(Category).count()
        
        if existing_categories == 0:
            print("🌱 Initializing database with default categories...")
            
            # Add default categories
            for category_data in DEFAULT_CATEGORIES:
                category = Category(**category_data)
                db.add(category)
            
            db.commit()
            print(f"✅ Added {len(DEFAULT_CATEGORIES)} default categories")
        else:
            print(f"📊 Database already initialized with {existing_categories} categories")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

# === DATABASE UTILITIES ===

def get_database_info():
    """Get information about the current database"""
    db = SessionLocal()
    try:
        from .models import Transaction, Category
        
        transaction_count = db.query(Transaction).count()
        category_count = db.query(Category).count()
        
        return {
            "database_file": DATABASE_URL.replace("sqlite:///", ""),
            "transactions": transaction_count,
            "categories": category_count,
            "status": "connected"
        }
    except Exception as e:
        return {
            "database_file": DATABASE_URL.replace("sqlite:///", ""),
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()

def reset_database():
    """
    WARNING: This deletes all data and recreates the database.
    Use only for development/testing.
    """
    Base.metadata.drop_all(bind=engine)
    init_database()
    return {"status": "Database reset successfully"}
