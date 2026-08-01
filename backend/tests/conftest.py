"""
Shared pytest fixtures

Every test runs against a throwaway SQLite file, never the real finance.db. The
DATABASE_URL environment variable is set before app.database is imported, so the
engine is bound to the temp file from the moment it is created - overriding the
get_db dependency alone would not be enough, since anything reaching startup
would still touch the real database.
"""
import os
import sys
import tempfile
from datetime import datetime

# Both of these must happen before "import app" anywhere below
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DB_PATH = os.path.join(tempfile.mkdtemp(prefix="pft_tests_"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, SessionLocal
from app.main import app
from app.models import Category, Transaction, CategoryKeyword, DEFAULT_CATEGORIES


def pytest_configure():
    """Fail loudly rather than quietly writing to the developer's real database"""
    from app.database import DATABASE_URL
    assert "finance.db" not in DATABASE_URL, (
        f"Tests are pointed at the real database ({DATABASE_URL}). Aborting."
    )


@pytest.fixture
def db() -> Session:
    """
    A clean database with the default categories seeded

    Tables are dropped and recreated per test so nothing leaks between them, which
    matters more here than usual - the categorizer learns from whatever rows exist,
    so a stray transaction from an earlier test changes later results.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    for category_data in DEFAULT_CATEGORIES:
        session.add(Category(**category_data))
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db) -> TestClient:
    """
    A TestClient whose requests share the test's database session

    Overriding get_db keeps the route and the test looking at the same data, so a
    test can assert against rows the request just wrote without reopening a session.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def categories(db) -> dict:
    """Mapping of category name -> id, for tests that need to reference them"""
    return {category.name: category.id for category in db.query(Category).all()}


@pytest.fixture
def make_transaction(db, categories):
    """
    Factory for building transactions without repeating the boilerplate

    Amounts are negated so callers can pass a readable positive number; the app
    stores expenses as negative.
    """
    def _make(description: str, amount: float, category: str = None,
              date: str = "2025-01-15", keywords: str = None) -> Transaction:
        transaction = Transaction(
            description=description,
            amount=-abs(amount),
            date=datetime.fromisoformat(date),
            category_id=categories[category] if category else None,
            extracted_keywords=keywords
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    return _make


@pytest.fixture
def csv_row(db, categories):
    """
    Factory for parsed-CSV rows, and the persisted transaction each one represents

    learn_from_import reads its corpus from persisted rows, so a row that only exists
    as a schema object would never be learnable - both halves have to exist.
    """
    from app.schemas import TransactionCreateFromCSV

    counter = {"row": 0}

    def _make(description: str, amount: float, category: str, keywords: str,
              source: str, persist: bool = True) -> TransactionCreateFromCSV:
        counter["row"] += 1
        row = TransactionCreateFromCSV(
            description=description,
            amount=-abs(amount),
            date=datetime(2025, 1, 1),
            category_id=categories[category],
            source_file="statement.csv",
            original_row=counter["row"],
            extracted_keywords=keywords,
            categorization_source=source
        )
        if persist:
            db.add(Transaction(
                description=row.description, amount=row.amount, date=row.date,
                category_id=row.category_id, extracted_keywords=row.extracted_keywords
            ))
            db.commit()
        return row

    return _make


@pytest.fixture
def keyword_for(db, categories):
    """Factory for seeding a learned keyword mapping at a chosen weight"""
    def _make(keyword: str, category: str, weight: int = 1) -> CategoryKeyword:
        mapping = CategoryKeyword(
            keyword=keyword,
            category_id=categories[category],
            weight=weight
        )
        db.add(mapping)
        db.commit()
        return mapping

    return _make
