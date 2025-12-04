"""
CSV Parser for bank transaction files with configurable bank formats
Uses Strategy Pattern to support multiple banks without code modification
"""
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..schemas import TransactionCreateFromCSV, CategoryCreate
from .categorizer import auto_categorize_transaction
from .. import crud


@dataclass
class BankFormatConfig:
    """Configuration for a specific bank's CSV format"""
    name: str
    # Header detection
    header_columns: List[str]  # Expected column names in header
    # Column indices (0-based)
    date_col: int
    description_col: int
    amount_col: int
    # Parsing config
    date_format: str  # strftime format string
    skip_first_data_row: bool = False  # Skip first row after header
    invert_amount_sign: bool = False  # If True, multiply amount by -1 (for banks with inverted signs)
    # Debit/Credit indicator (for banks with all positive amounts)
    type_col: Optional[int] = None  # Column index for transaction type (Debit/Credit)
    debit_indicators: List[str] = None  # Values that indicate debit (e.g., ["Debit", "Withdrawal"])
    credit_indicators: List[str] = None  # Values that indicate credit (e.g., ["Credit", "Deposit"])
    # Optional: custom validators
    row_validator: Optional[Callable[[List[str]], bool]] = None
    csv_has_categories: bool = False # Don't check for the csv having categories
    category_col: Optional[int] = None


# Bank format configurations
BANK_FORMATS = {
    "bank_of_america": BankFormatConfig(
        name="Bank of America",
        header_columns=["Date", "Description", "Amount", "Running Bal."],
        date_col=0,
        description_col=1,
        amount_col=2,
        date_format="%m/%d/%Y",
        skip_first_data_row=True,  # Skip beginning balance row
        invert_amount_sign=False,  # Normal: expenses negative, income positive
        type_col=None,             # Not needed since the amount data is displayed normally
        debit_indicators=None,
        credit_indicators=None,
        csv_has_categories=False,
        category_col=None
    ),
    "apple_card": BankFormatConfig(
        name="Apple Card",
        header_columns=["Transaction Date", "Clearing Date", "Description", "Merchant", "Category",
                        "Type", "Amount (USD)", "Purchased By"],
        date_col=0,
        description_col=2,
        amount_col=6,
        date_format="%m/%d/%Y",
        skip_first_data_row=False,
        invert_amount_sign=True,  # Apple Card uses inverted signs (purchases positive, payments negative)
        type_col=None,            # Not needed since we use invert_amount_sign
        debit_indicators=None,
        credit_indicators=None,
        csv_has_categories=True,
        category_col=4
    ),
    # Example for future bank with all positive amounts and Debit/Credit column:
    # "example_bank": BankFormatConfig(
    #     name="Example Bank",
    #     header_columns=["Date", "Description", "Amount", "Type"],
    #     date_col=0,
    #     description_col=1,
    #     amount_col=2,
    #     date_format="%m/%d/%Y",
    #     skip_first_data_row=False,
    #     type_col=3,
    #     debit_indicators=["Debit", "Withdrawal", "Payment"],
    #     credit_indicators=["Credit", "Deposit", "Refund"],
    #     invert_amount_sign=False,
    #     csv_has_categories=False,
    #     category_col=None
    # ),
    # Add more banks/card providers here:
    
}

def detect_bank_format(csv_content: str) -> Optional[str]:
    """
    Auto-detect which bank format the CSV file matches by scanning for known header patterns
    
    Scans up to the first 20 rows of the CSV file looking for a header row that matches
    one of the configured bank formats in BANK_FORMATS.
    
    Args:
        csv_content: Raw CSV content as string
        
    Returns:
        Bank format key (e.g., "bank_of_america") or None if not recognized
    """
    csv_reader = csv.reader(io.StringIO(csv_content))
    max_rows_to_scan = 20
    
    # Scan the first several rows looking for a matching header
    for row_index in range(max_rows_to_scan):
        try:
            current_row = next(csv_reader)
            
            # Skip empty rows
            if _is_empty_row(current_row):
                continue
            
            # Try to match this row against each known bank format
            detected_format = _match_row_to_bank_format(current_row)
            if detected_format:
                return detected_format
                        
        except StopIteration:
            # Reached end of file before finding a match
            break
    
    # No matching bank format found
    return None


def _is_empty_row(row: List[str]) -> bool:
    """Check if a CSV row is empty or contains only whitespace"""
    return not row or all(cell.strip() == '' for cell in row)


def _match_row_to_bank_format(row: List[str]) -> Optional[str]:
    """
    Try to match a CSV row against all configured bank formats
    
    Args:
        row: List of cell values from a CSV row
        
    Returns:
        Bank format key if match found, None otherwise
    """
    for bank_key, bank_config in BANK_FORMATS.items():
        if _row_matches_bank_header(row, bank_config):
            return bank_key
    
    return None


def _row_matches_bank_header(row: List[str], bank_config: BankFormatConfig) -> bool:
    """
    Check if a CSV row matches the expected header for a bank format
    
    Args:
        row: List of cell values from a CSV row
        bank_config: Bank format configuration to check against
        
    Returns:
        True if row matches the bank's expected header columns
    """
    # Row must have at least as many columns as expected
    if len(row) < len(bank_config.header_columns):
        return False
    
    # Check if each expected header column appears in the correct position
    # Uses case-insensitive substring matching for flexibility
    for column_index, expected_header in enumerate(bank_config.header_columns):
        actual_cell = row[column_index].lower()
        expected_text = expected_header.lower()
        
        if expected_text not in actual_cell:
            return False
    
    return True


def parse_csv_with_format(
    csv_content: str, 
    filename: str, 
    bank_format_key: str,
    db: Session = None
) -> List[TransactionCreateFromCSV]:
    """
    Parse CSV using specified bank format configuration with auto-categorization
    
    Args:
        csv_content: Raw CSV content as string
        filename: Name of the CSV file for tracking
        bank_format_key: Key for bank format in BANK_FORMATS dict
        db: Database session for auto-categorization (optional, defaults to "Other" if not provided)
        
    Returns:
        List of TransactionCreateFromCSV objects with auto-categorized transactions
    """
    if bank_format_key not in BANK_FORMATS:
        raise ValueError(f"Unknown bank format: {bank_format_key}")
    
    config = BANK_FORMATS[bank_format_key]
    transactions = []
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    header_found = False
    first_data_row_skipped = False
    row_number = 0
    
    for row in csv_reader:
        row_number += 1
        
        # Skip empty rows
        if not row or all(cell.strip() == '' for cell in row):
            continue
        
        # Look for header row
        if not header_found:
            if len(row) >= len(config.header_columns):
                matches = all(
                    expected.lower() in row[i].lower()
                    for i, expected in enumerate(config.header_columns)
                )
                if matches:
                    header_found = True
                    continue
            continue
        
        # Skip first data row if configured
        if config.skip_first_data_row and not first_data_row_skipped:
            first_data_row_skipped = True
            continue
        
        # Process transaction data rows
        if len(row) > max(config.date_col, config.description_col, config.amount_col):
            try:
                # Apply custom validator if exists
                if config.row_validator and not config.row_validator(row):
                    continue
                
                # Extract data using configured column indices
                date_str = row[config.date_col].strip()
                description = row[config.description_col].strip()
                amount_str = row[config.amount_col].strip()
                
                # Skip invalid rows
                if not date_str or not description or not amount_str or amount_str == '':
                    continue
                
                # Parse date
                transaction_date = datetime.strptime(date_str, config.date_format)
                
                # Parse amount
                cleaned_amount = amount_str.replace(',', '').replace('$', '').replace('"', '').strip()
                amount = float(cleaned_amount)
                
                # Handle banks with all positive amounts and debit/credit indicator
                if config.type_col is not None:
                    transaction_type = row[config.type_col].strip().lower()
                    
                    # Check if it's a debit (expense) - make negative
                    if config.debit_indicators and any(indicator.lower() in transaction_type for indicator in config.debit_indicators):
                        amount = -abs(amount)  # Ensure negative
                    # Check if it's a credit (income) - make positive
                    elif config.credit_indicators and any(indicator.lower() in transaction_type for indicator in config.credit_indicators):
                        amount = abs(amount)  # Ensure positive
                    # Default: if no match, assume debit (expense)
                    else:
                        amount = -abs(amount)
                
                # Invert amount sign if bank uses inverted convention (applied after debit/credit logic)
                if config.invert_amount_sign:
                    amount = -amount
                
                # Skip positive amounts (income) - we only track expenses
                if amount >= 0:
                    continue
                
                # Extract category from CSV if available
                csv_category_name = ""
                if config.csv_has_categories and config.category_col is not None:
                    csv_category_name = row[config.category_col].strip()
                
                # Auto-categorize transaction
                if db:
                    category_id, keywords = auto_categorize_transaction(db, description, amount, csv_category_name)
                    keywords_str = ','.join(keywords) if keywords else None
                else:
                    # No database session, default to "Other" (ID 7)
                    category_id = 7
                    keywords_str = None
                
                # Create transaction
                transaction = TransactionCreateFromCSV(
                    description=description,
                    amount=amount,
                    date=transaction_date,
                    category_id=category_id,
                    extracted_keywords=keywords_str,
                    source_file=filename,
                    original_row=row_number,
                    csv_category_name=csv_category_name if csv_category_name != "" else "N/A"
                )
                
                transactions.append(transaction)
                
            except (ValueError, IndexError) as e:
                print(f"Skipping invalid row {row_number}: {row}. Error: {e}")
                continue
    
    return transactions


def parse_csv_auto_detect(
    csv_content: str, 
    filename: str, 
    db: Session = None
) -> List[TransactionCreateFromCSV]:
    """
    Auto-detect bank format and parse CSV with auto-categorization
    
    Args:
        csv_content: Raw CSV content as string
        filename: Name of the CSV file for tracking
        db: Database session for auto-categorization (optional)
        
    Returns:
        List of TransactionCreateFromCSV objects with auto-categorized transactions
        
    Raises:
        ValueError: If bank format cannot be detected
    """
    bank_format = detect_bank_format(csv_content)
    
    if not bank_format:
        raise ValueError(
            "Could not detect bank format. Currently supported: " + 
            ", ".join(config.name for config in BANK_FORMATS.values())
        )
    
    return parse_csv_with_format(csv_content, filename, bank_format, db)


def validate_csv_format(csv_content: str) -> Dict[str, Any]:
    """
    Validate CSV and detect format
    
    Args:
        csv_content: Raw CSV content as string
        
    Returns:
        Dict with validation results and metadata
    """
    bank_format = detect_bank_format(csv_content)
    
    if not bank_format:
        return {
            "is_valid": False,
            "total_rows": 0,
            "data_rows": 0,
            "header_found": False,
            "format": "unknown"
        }
    
    config = BANK_FORMATS[bank_format]
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    total_rows = 0
    header_found = False
    data_rows = 0
    first_data_row_skipped = False
    
    for row in csv_reader:
        total_rows += 1
        
        # Look for header
        if not header_found and len(row) >= len(config.header_columns):
            matches = all(
                expected.lower() in row[i].lower()
                for i, expected in enumerate(config.header_columns)
            )
            if matches:
                header_found = True
                continue
        
        # Skip first data row if configured
        if config.skip_first_data_row and not first_data_row_skipped and header_found:
            first_data_row_skipped = True
            continue
        
        # Count data rows
        if header_found and len(row) > max(config.date_col, config.description_col, config.amount_col):
            date_str = row[config.date_col].strip()
            description = row[config.description_col].strip()
            amount_str = row[config.amount_col].strip()
            
            if date_str and description and amount_str and amount_str != '':
                data_rows += 1
    
    return {
        "is_valid": header_found and data_rows >= 0,
        "total_rows": total_rows,
        "data_rows": data_rows,
        "header_found": header_found,
        "format": bank_format,
        "format_name": config.name
    }


def create_csv_categories(
    category_names: list[str],
    db: Session
) -> Dict[str, int]:
    """
    Create categories from CSV names and return name->ID mapping
    
    Args:
        category_names: Set of category names from CSV
        db: Database session
        
    Returns:
        Dict mapping category name to category ID
    """
    mapping = {}
    for category_name in category_names:
        category_schema = CategoryCreate(name=category_name, description="")
        category = crud.create_category(db=db, category=category_schema)
        mapping[category_name] = category.id
    return mapping


def get_csv_preview(
    csv_content: str, 
    filename: str, 
    db: Session = None,
    max_transactions: int = None
) -> List[Dict[str, Any]]:
    """
    Get a preview of transactions using auto-detection and auto-categorization
    
    Args:
        csv_content: Raw CSV content as string
        filename: Name of the CSV file
        db: Database session for auto-categorization (optional)
        max_transactions: Maximum number of transactions to preview (None = all)
        
    Returns:
        List of transaction dictionaries for preview
    """
    transactions = parse_csv_auto_detect(csv_content, filename, db)
    
    # Show all transactions if max_transactions is None
    transactions_to_show = transactions if max_transactions is None else transactions[:max_transactions]
    
    preview = []
    for i, transaction in enumerate(transactions_to_show):
        preview.append({
            "date": transaction.date.strftime("%Y-%m-%d"),
            "description": transaction.description,
            "amount": transaction.amount,
            "category_id": transaction.category_id,
            "source_file": transaction.source_file,
            "original_row": transaction.original_row,
            "preview_index": i + 1,
            "csv_category_name": transaction.csv_category_name
        })
    
    return preview
