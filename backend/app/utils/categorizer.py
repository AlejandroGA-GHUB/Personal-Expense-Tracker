"""
Keyword-based auto-categorization system with adaptive learning
Extracts keywords from descriptions, matches against learned patterns, improves from user corrections
"""
import re
from datetime import datetime
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from ..models import Category, CategoryKeyword
from ..database import get_db


def extract_keywords(description: str, min_length: int = 3) -> List[str]:
    """
    Extract meaningful keywords from transaction description
    
    Args:
        description: Transaction description (e.g., "STARBUCKS #12345 SEATTLE WA")
        min_length: Minimum keyword length to consider
    
    Returns:
        List of lowercase keywords
    
    Examples:
        "STARBUCKS COFFEE" -> ["starbucks", "coffee"]
        "UBER TRIP 123" -> ["uber", "trip"]
        "Shell Gas Station #4567" -> ["shell", "gas", "station"]
    """
    # Remove special characters, numbers, convert to lowercase
    cleaned = re.sub(r'[^a-zA-Z\s]', ' ', description.lower())
    
    # Split into words
    words = cleaned.split()
    
    # Filter out common stopwords, generic transaction terms, and patterns
    stopwords = {
        # Common words
        'the', 'and', 'for', 'with', 'from', 'inc', 'llc', 'corp', 'ltd', 
        'co', 'company', 'store', 'number', 'location',
        # Generic transaction terms
        'purchase', 'payment', 'transaction', 'charge', 'debit', 'credit',
        'online', 'order', 'sale', 'bill', 'invoice',
        # Generic patterns (masked numbers, dates, etc.)
        'xxxxx', 'xxxx', 'xxx', 'conf', 'ref', 'auth'
    }
    
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stopwords
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords


def auto_categorize_transaction(
    db: Session,
    description: str,
    amount: float,
    csv_category_name: str
) -> Tuple[int, List[str]]:
    """
    Auto-categorize a transaction based on learned keywords
    
    Args:
        db: Database session
        description: Transaction description
        amount: Transaction amount (positive = income, negative = expense)
    
    Returns:
        Tuple of (category_id, extracted_keywords)
    
    Algorithm:
        1. Extract keywords from description
        2. Special rule: If amount > 0, check for Income category
        3. Query matching CategoryKeywords from database
        4. Calculate score per category (sum of matching keyword weights)
        5. Return category with highest score (or "Other" if no good match)
    """
    # Extract keywords from description
    keywords = extract_keywords(description)
    
    if csv_category_name != "":
        matched_category = utilize_bank_categorization(db, csv_category_name)
        if matched_category != 0:
            return matched_category, keywords
        
    if not keywords:
        # No keywords found, default to "Other"
        other_category = db.query(Category).filter(Category.name == "Other").first()
        return (other_category.id if other_category else 6), []
    
    # Query all matching keywords from database
    matching_keywords = db.query(CategoryKeyword).filter(
        CategoryKeyword.keyword.in_(keywords)
    ).all()
    
    if not matching_keywords:
        # No learned patterns match, default to "Other"
        other_category = db.query(Category).filter(Category.name == "Other").first()
        return (other_category.id if other_category else 7), keywords
    
    # Get Income category ID to filter it out for negative amounts
    income_category = db.query(Category).filter(Category.name == "Income").first()
    income_category_id = income_category.id if income_category else None
    
    # Calculate score for each category (sum of keyword weights)
    category_scores = {}
    category_match_counts = {}
    
    for kw in matching_keywords:
        # Skip Income category if amount is negative (it's an expense, not income!)
        if amount < 0 and kw.category_id == income_category_id:
            continue
            
        if kw.category_id not in category_scores:
            category_scores[kw.category_id] = 0
            category_match_counts[kw.category_id] = 0
        
        category_scores[kw.category_id] += kw.weight
        category_match_counts[kw.category_id] += 1
    
    # Check if we have any valid categories after filtering
    if not category_scores:
        # No valid matches (e.g., PayPal expense but only Income keywords matched)
        other_category = db.query(Category).filter(Category.name == "Other").first()
        return (other_category.id if other_category else 7), keywords
    
    # Find category with highest score
    best_category_id = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category_id]
    match_count = category_match_counts[best_category_id]
    
    # Confidence threshold: require at least one keyword match with weight ≥ 1
    # This allows default keywords to work immediately while still benefiting from learning
    if best_score >= 1:
        return best_category_id, keywords
    
    # No confident match, default to "Other"
    other_category = db.query(Category).filter(Category.name == "Other").first()
    return (other_category.id if other_category else 7), keywords

def utilize_bank_categorization(db: Session, csv_category: str) -> int:
    """
    Try to match bank's CSV category to our system categories
    
    Args:
        db: Database session
        csv_category: Category name from CSV (e.g., "Grocery", "Restaurants", "Medical")
    
    Returns:
        Category ID if match found, 0 if no match
    """
    if not csv_category or csv_category.strip() == "":
        return 0
    
    csv_category_lower = csv_category.lower().strip()
    
    # Common bank category mappings to our system categories
    category_mappings = {
        # Food & Dining variations
        "restaurants": "Food & Dining",
        "restaurant": "Food & Dining",
        "grocery": "Food & Dining",
        "groceries": "Food & Dining",
        "food": "Food & Dining",
        "dining": "Food & Dining",
        "coffee": "Food & Dining",
        "bar": "Food & Dining",
        "alcohol": "Food & Dining",
        
        # Transportation variations
        "gas": "Transportation",
        "fuel": "Transportation",
        "parking": "Transportation",
        "transit": "Transportation",
        "uber": "Transportation",
        "lyft": "Transportation",
        "taxi": "Transportation",
        
        # Shopping variations
        "shopping": "Shopping",
        "retail": "Shopping",
        "clothing": "Shopping",
        "electronics": "Shopping",
        
        # Entertainment variations
        "entertainment": "Entertainment",
        "movies": "Entertainment",
        "gaming": "Entertainment",
        "streaming": "Entertainment",
        "music": "Entertainment",
        
        # Bills & Utilities variations
        "utilities": "Bills & Utilities",
        "utility": "Bills & Utilities",
        "insurance": "Bills & Utilities",
        "medical": "Bills & Utilities",
        "healthcare": "Bills & Utilities",
        "health": "Bills & Utilities",
        "phone": "Bills & Utilities",
        "internet": "Bills & Utilities",
        
        # Income variations
        "income": "Income",
        "salary": "Income",
        "payroll": "Income",
        "deposit": "Income",
        
        # Other
        "other": "Other",
        "misc": "Other",
        "miscellaneous": "Other"
    }

    # Try direct matching with our categories
    categories = db.query(Category).all()
    
    for category in categories:
        category_name_lower = category.name.lower()
        
        # Exact match (case-insensitive)
        if category_name_lower == csv_category_lower:
            return category.id
        
        # Check if CSV category contains our category name (partial match)
        if category_name_lower in csv_category_lower:
            return category.id

    # If no direct match found, check if CSV category matches a known mapping
    if csv_category_lower in category_mappings:
        target_category_name = category_mappings[csv_category_lower]
        category = db.query(Category).filter(Category.name == target_category_name).first()
        if category:
            return category.id
        
    # No match found
    return 0
    
def learn_from_category_change(
    db: Session,
    transaction_id: int,
    old_category_id: int,
    new_category_id: int
):
    """
    Learn from user manually changing a transaction's category
    
    When user edits a CSV-imported transaction's category:
    1. Get stored keywords from transaction
    2. For OLD category: decrement weight (or remove if weight becomes 0)
    3. For NEW category: add keywords (if not exist) or increment weight (+1)
    
    This is how the system learns and improves accuracy over time while
    also correcting mistakes when users change their mind
    
    Args:
        db: Database session
        transaction_id: ID of transaction being updated
        old_category_id: Previous category ID (to decrement/remove)
        new_category_id: New category ID (user's choice, to increment/add)
    """
    from ..models import Transaction
    
    # Get the transaction with its stored keywords
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction or not transaction.extracted_keywords:
        # No keywords to learn from (probably manually created transaction)
        return
    
    # Parse stored keywords
    keywords = [kw.strip() for kw in transaction.extracted_keywords.split(',') if kw.strip()]
    
    if not keywords:
        return
    
    # STEP 1: Decrement/remove keywords from OLD category (user changed their mind)
    for keyword in keywords:
        old_keyword = db.query(CategoryKeyword).filter(
            CategoryKeyword.category_id == old_category_id,
            CategoryKeyword.keyword == keyword,
            CategoryKeyword.is_default == False  # Only modify user-learned keywords, not defaults
        ).first()
        
        if old_keyword:
            if old_keyword.weight > 1:
                # Decrement weight
                old_keyword.weight -= 1
            else:
                # Weight is 1, remove the keyword entirely
                db.delete(old_keyword)
    
    # STEP 2: Increment/add keywords to NEW category (user's correction)
    for keyword in keywords:
        # Check if keyword already exists for this category
        existing = db.query(CategoryKeyword).filter(
            CategoryKeyword.category_id == new_category_id,
            CategoryKeyword.keyword == keyword
        ).first()
        
        if existing:
            # User confirmed this keyword→category association, increase weight
            existing.weight += 1
        else:
            # Create new learned keyword association
            new_keyword = CategoryKeyword(
                category_id=new_category_id,
                keyword=keyword,
                weight=1,
                is_default=False  # User-learned, not system default
            )
            db.add(new_keyword)
    
    db.commit()


def seed_default_keywords(db: Session):
    """
    Seed default keywords into CategoryKeyword table
    Called during database initialization
    
    Takes DEFAULT_KEYWORDS from models.py and creates CategoryKeyword entries
    """
    from ..models import DEFAULT_KEYWORDS
    
    # Get all categories
    categories = {cat.name: cat.id for cat in db.query(Category).all()}
    
    # Seed keywords for each category
    for category_name, keywords in DEFAULT_KEYWORDS.items():
        if category_name not in categories:
            print(f"Warning: Category '{category_name}' not found, skipping keywords")
            continue
        
        category_id = categories[category_name]
        
        for keyword in keywords:
            # Check if keyword already exists for this category
            existing = db.query(CategoryKeyword).filter(
                CategoryKeyword.category_id == category_id,
                CategoryKeyword.keyword == keyword
            ).first()
            
            if not existing:
                # Create new default keyword
                new_keyword = CategoryKeyword(
                    category_id=category_id,
                    keyword=keyword,
                    weight=1,  # Default keywords start with weight of 1
                    is_default=True
                )
                db.add(new_keyword)
    
    db.commit()
    print(f"✓ Seeded default keywords for auto-categorization")
