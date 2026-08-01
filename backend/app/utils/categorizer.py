"""
Keyword-based auto-categorization system with adaptive learning
Extracts keywords from descriptions, matches against learned patterns, improves from user corrections
"""
import re
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from sqlalchemy.orm import Session
from ..models import Category, CategoryKeyword, DEFAULT_KEYWORDS
from ..database import get_db
from .llm_categorizer import categorize_with_llm, llm_available


def extract_keywords(description: str, min_length: int = 3) -> List[str]:
    """
    Extract meaningful keywords from transaction description
    
    Args:
        description: Transaction description (e.g., "NORTHWIND CAFE #12345 RIVERTON ZZ")
        min_length: Minimum keyword length to consider
    
    Returns:
        List of lowercase keywords

    Examples:
        "NORTHWIND COFFEE" -> ["northwind", "coffee"]
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


# === HOW A ROW GOT ITS CATEGORY ===
# Returned alongside the category so the upload preview can say who actually made
# the call. A row the bank labelled was not "AI categorized", and neither was one
# the built-in keyword list matched - labelling both as AI was misleading.
SOURCE_LEARNED = "learned_keywords"   # our own stored mappings (stage 1)
SOURCE_BANK = "bank_category"         # the bank's own CSV label (stage 2)
SOURCE_LLM = "llm"                    # the local model (stage 3)
SOURCE_BUILTIN = "builtin_keywords"   # hardcoded DEFAULT_KEYWORDS (stage 4)
SOURCE_NONE = "none"                  # nothing matched, fell through to "Other"


def _bank_labelled(csv_category_name: str) -> bool:
    """
    Whether the bank actually told us what this row was.

    "Other" doesn't count: that's the bank saying it didn't know either, which is
    precisely the case we want the LLM to look at. Treating it as a real label is
    what used to send every "Other" row straight to our own "Other" bucket.
    """
    cleaned = (csv_category_name or "").strip().lower()
    return cleaned not in ("", "n/a", "other")


def _match_stored_keywords(db: Session, keywords: List[str]) -> Optional[int]:
    """
    Look the description's keywords up in our stored mappings.

    Every row in CategoryKeyword is a real mapping - either learned from a user
    correction or created alongside a category. Matching rows are scored by summed
    weight and the highest-scoring category wins.

    Returns:
        Winning category id, or None if nothing matched.
    """
    if not keywords:
        return None

    matches = db.query(CategoryKeyword).filter(
        CategoryKeyword.keyword.in_(keywords)
    ).all()

    if not matches:
        return None

    scores = {}
    for match in matches:
        scores[match.category_id] = scores.get(match.category_id, 0) + match.weight

    best_category_id = max(scores, key=scores.get)

    # Confidence threshold: require a summed weight of at least 1
    return best_category_id if scores[best_category_id] >= 1 else None


def _match_hardcoded_keywords(db: Session, keywords: List[str]) -> Optional[int]:
    """
    Last resort: the hardcoded DEFAULT_KEYWORDS list in models.py.

    This is a generic built-in guess, not one of our stored mappings, so it is
    never written to the database and never learned from - it just resolves to a
    category by name. It exists so an install with no LLM still categorizes
    something; without it a Bank of America file, which carries no category
    column at all, would import as 100% "Other".

    Returns:
        Category id for the best-matching category name, or None.
    """
    if not keywords:
        return None

    keyword_set = set(keywords)
    scores = {}
    for category_name, default_keywords in DEFAULT_KEYWORDS.items():
        hits = keyword_set.intersection(default_keywords)
        if hits:
            scores[category_name] = len(hits)

    if not scores:
        return None

    best_name = max(scores, key=scores.get)

    # Join the existing category. These names are the seeded DEFAULT_CATEGORIES so
    # they normally exist; we don't create one here because this runs during the
    # upload *preview* too, which must not write to the database.
    category = db.query(Category).filter(Category.name == best_name).first()
    return category.id if category else None


def _other_category_id(db: Session) -> Optional[int]:
    """Look "Other" up by name rather than trusting a seed order that isn't guaranteed."""
    other_category = db.query(Category).filter(Category.name == "Other").first()
    return other_category.id if other_category else None


def auto_categorize_transaction(
    db: Session,
    description: str,
    amount: float,
    csv_category_name: str,
    llm_cache: Optional[Dict[str, Optional[str]]] = None
) -> Tuple[Optional[int], List[str], Optional[str], str]:
    """
    Auto-categorize a transaction based on learned keywords

    Args:
        db: Database session
        description: Transaction description
        amount: Transaction amount (all tracked transactions are expenses / negative)
        csv_category_name: Original category from the bank's CSV, if any
        llm_cache: Optional per-import dict shared across rows of one CSV, so
            repeat merchants cost a single LLM call

    Returns:
        Tuple of (category_id, extracted_keywords, suggested_new_category_name, source)
        where source is one of the SOURCE_* constants above.

    Cascade:
        1. Stored keyword mappings in the database
        2. Bank CSV category - the label the bank put on the row
        3. Local LLM - only for rows the bank did NOT label, and only when wired up
        4. Hardcoded DEFAULT_KEYWORDS - built-in guess, only if nothing above answered
        5. "Other"
    """
    keywords = extract_keywords(description)
    bank_labelled = _bank_labelled(csv_category_name)

    # --- Stage 1: our own stored mappings ---
    stored_match = _match_stored_keywords(db, keywords)
    if stored_match is not None:
        return stored_match, keywords, None, SOURCE_LEARNED

    # --- Stage 2: the bank's own label ---
    if bank_labelled:
        matched_category = utilize_bank_categorization(db, csv_category_name)
        if matched_category != 0:
            return matched_category, keywords, None, SOURCE_BANK

    # --- Stage 3: local LLM ---
    # Skipped for rows the bank labelled: no point spending a model call to
    # second-guess the bank, and it keeps a row from offering two competing
    # "Apply" buttons in the preview.
    if not bank_labelled and llm_available(llm_cache):
        categories = db.query(Category).all()
        answer = categorize_with_llm(
            description, amount, [category.name for category in categories], keywords, llm_cache
        )
        if answer:
            for category in categories:
                if category.name == answer:
                    return category.id, keywords, None, SOURCE_LLM
            # A category that doesn't exist yet. Not created here - it rides to the
            # upload preview for the user to approve, which is what stops the model
            # from growing the category list behind their back.
            return _other_category_id(db), keywords, answer, SOURCE_LLM

    # --- Stage 4: hardcoded fallback, reached only because nothing above answered ---
    hardcoded_match = _match_hardcoded_keywords(db, keywords)
    if hardcoded_match is not None:
        return hardcoded_match, keywords, None, SOURCE_BUILTIN

    # --- Stage 5 ---
    return _other_category_id(db), keywords, None, SOURCE_NONE

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
    
def _keyword_category_map(db: Session, exclude_transaction_id: Optional[int] = None) -> Dict[str, set]:
    """
    Map each keyword we've stored on a transaction to the set of categories it
    has been seen with.

    Built in one pass over the transactions table rather than per keyword, since
    an import learns from every row at once. This is what `Transaction.extracted_keywords`
    is for - it's the corpus.

    Args:
        exclude_transaction_id: Skip this transaction. Used when learning from a
            correction: the row being corrected still carries its OLD category, so
            counting it would make every one of its own keywords look ambiguous.
    """
    from ..models import Transaction

    query = db.query(Transaction.extracted_keywords, Transaction.category_id).filter(
        Transaction.extracted_keywords.isnot(None),
        Transaction.category_id.isnot(None)
    )
    if exclude_transaction_id is not None:
        query = query.filter(Transaction.id != exclude_transaction_id)

    seen: Dict[str, set] = {}
    for stored_keywords, category_id in query.all():
        for keyword in (k.strip() for k in stored_keywords.split(',')):
            if keyword:
                seen.setdefault(keyword, set()).add(category_id)
    return seen


def _is_learnable(keyword: str, category_id: int, keyword_categories: Dict[str, set]) -> bool:
    """
    Whether a token is specific enough to be worth storing as a mapping.

    A merchant token concentrates in one category - that's what makes it a
    merchant. Address and geography tokens scatter, because people buy all kinds
    of things on the same street. So the rule is strict: keep a token only if
    every transaction carrying it shares a single category. A token seen nowhere
    else is trivially kept, since it can only ever match the merchant it came from.

    Deliberately NOT based on how often a token appears. Frequency breaks on small
    files - 3 Globex rows out of 5 is 60% of the file but still one category, and
    is exactly the mapping worth learning.

    Measured on a real 83-row Apple Card statement, whose descriptions embed the
    full postal address: 'usa' appeared in 82 rows across all 6 categories,
    'fairview' in 28 across 4, while 'globex' and 'northwind' each sat in exactly
    one. Without this guard a single user correction taught 'usa' -> Entertainment
    and re-filed 82 of the 83 rows.
    """
    return keyword_categories.get(keyword, set()) <= {category_id}


def learn_from_import(db: Session, rows: List) -> int:
    """
    Turn the local LLM's decisions from a CSV import into stored keyword mappings.

    Without this, re-importing the same file pays for the model all over again and
    the preview reports "AI Mapping" a second time, even though the app has
    already seen those merchants. With it, pass two is a stage-1 hit and makes no
    model calls at all.

    Only LLM rows are learned. The other stages never call the model, so recording
    them saves nothing, and it keeps category_keywords a record of decisions
    something actually reasoned about rather than a copy of every import.

    Expects the rows to be persisted already, so the corpus that decides which
    tokens are ambiguous includes them.

    Args:
        rows: The parsed TransactionCreateFromCSV objects that were just written.

    Returns:
        Number of keyword mappings created or reinforced.
    """
    keyword_categories = _keyword_category_map(db)
    learned = 0

    for row in rows:
        if getattr(row, 'categorization_source', None) != SOURCE_LLM:
            continue
        if not row.category_id or not row.extracted_keywords:
            continue

        for keyword in (k.strip() for k in row.extracted_keywords.split(',')):
            if not keyword or not _is_learnable(keyword, row.category_id, keyword_categories):
                continue

            existing = db.query(CategoryKeyword).filter(
                CategoryKeyword.category_id == row.category_id,
                CategoryKeyword.keyword == keyword
            ).first()

            if existing:
                existing.weight += 1
            else:
                db.add(CategoryKeyword(
                    category_id=row.category_id,
                    keyword=keyword,
                    weight=1
                ))
            learned += 1

    if learned:
        db.commit()

    return learned


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

    # Exclude this transaction: it still carries its OLD category, so counting it
    # would make every one of its own keywords look like it spans two categories.
    keyword_categories = _keyword_category_map(db, exclude_transaction_id=transaction_id)

    # STEP 1: Decrement/remove keywords from OLD category (user changed their mind)
    for keyword in keywords:
        old_keyword = db.query(CategoryKeyword).filter(
            CategoryKeyword.category_id == old_category_id,
            CategoryKeyword.keyword == keyword
        ).first()
        
        if old_keyword:
            if old_keyword.weight > 1:
                # Decrement weight
                old_keyword.weight -= 1
            else:
                # Weight is 1, remove the keyword entirely
                db.delete(old_keyword)
    
    # STEP 2: Increment/add keywords to NEW category (user's correction)
    # Note STEP 1 above is deliberately unfiltered while this is filtered: junk
    # learned before this guard existed should still get cleaned up as the user
    # corrects rows, but nothing new gets added unless it earns it.
    for keyword in keywords:
        if not _is_learnable(keyword, new_category_id, keyword_categories):
            continue

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
                weight=1
            )
            db.add(new_keyword)
    
    db.commit()


