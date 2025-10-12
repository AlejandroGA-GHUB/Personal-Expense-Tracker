"""
CSV Parser for Bank of America transaction files
Handles parsing CSV files and converting them to transaction objects
"""
import csv
import io
from datetime import datetime
from typing import List, Dict, Any
from ..schemas import TransactionCreateFromCSV

def parse_bank_of_america_csv(csv_content: str, filename: str, default_category_id: int = 7) -> List[TransactionCreateFromCSV]:
    """
    Parse Bank of America CSV format and return list of TransactionCreateFromCSV objects
    
    Args:
        csv_content: Raw CSV content as string
        filename: Name of the CSV file for tracking
        default_category_id: Category ID to assign to all transactions (defaults to 'Other')
        
    Returns:
        List of TransactionCreateFromCSV objects ready for database insertion
    """
    transactions = []
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    # Skip the summary section at the beginning
    # Look for the line that contains "Date,Description,Amount,Running Bal."
    header_found = False
    first_data_row_skipped = False
    row_number = 0
    
    for row in csv_reader:
        row_number += 1
        
        # Skip empty rows
        if not row or all(cell.strip() == '' for cell in row):
            continue
            
        # Look for the header row
        if not header_found:
            # Check if this row contains the data header
            if len(row) >= 4 and 'Date' in row[0] and 'Description' in row[1] and 'Amount' in row[2]:
                header_found = True
                continue  # Skip the header row itself
            else:
                continue  # Skip summary/metadata rows
        
        # Skip the first data row (beginning balance filler row)
        if header_found and not first_data_row_skipped:
            first_data_row_skipped = True
            continue
        
        # Process actual transaction data rows
        if header_found and len(row) >= 4:
            try:
                # Extract data from CSV columns
                date_str = row[0].strip()
                description = row[1].strip()
                amount_str = row[2].strip()
                # running_balance = row[3].strip()  # Not needed for transaction creation
                
                # Skip empty or invalid rows
                if not date_str or not description or not amount_str:
                    continue
                
                # Skip rows where amount is empty (like beginning balance row)
                if amount_str == '':
                    continue
                
                # Parse date (MM/DD/YYYY format)
                transaction_date = datetime.strptime(date_str, '%m/%d/%Y')
                
                # Parse amount (remove any extra spaces, handle negative signs, remove quotes and commas)
                # Bank of America shows debits as negative, credits as positive
                cleaned_amount = amount_str.replace(',', '').replace('$', '').replace('"', '')
                amount = float(cleaned_amount)
                
                # Create TransactionCreateFromCSV object
                transaction = TransactionCreateFromCSV(
                    description=description,
                    amount=amount,
                    date=transaction_date,
                    category_id=default_category_id,
                    source_file=filename,
                    original_row=row_number
                )
                
                transactions.append(transaction)
                
            except (ValueError, IndexError) as e:
                # Skip invalid rows but continue processing
                print(f"Skipping invalid row {row_number}: {row}. Error: {e}")
                continue
    
    return transactions

def validate_csv_format(csv_content: str) -> Dict[str, Any]:
    """
    Validate that the CSV appears to be a Bank of America format
    
    Args:
        csv_content: Raw CSV content as string
        
    Returns:
        Dict with validation results and metadata
    """
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    total_rows = 0
    header_found = False
    data_rows = 0
    first_data_row_skipped = False
    
    for row in csv_reader:
        total_rows += 1
        
        # Look for the header row
        if not header_found and len(row) >= 4:
            if 'Date' in row[0] and 'Description' in row[1] and 'Amount' in row[2]:
                header_found = True
                continue
        
        # Skip the first data row (beginning balance)
        if header_found and not first_data_row_skipped:
            first_data_row_skipped = True
            continue
        
        # Count actual transaction data rows
        if header_found and len(row) >= 4:
            date_str = row[0].strip()
            description = row[1].strip()
            amount_str = row[2].strip()
            
            if date_str and description and amount_str and amount_str != '':
                data_rows += 1
    
    return {
        "is_valid": header_found and data_rows >= 0,  # Allow 0 transactions for empty files
        "total_rows": total_rows,
        "data_rows": data_rows,
        "header_found": header_found,
        "format": "bank_of_america" if header_found else "unknown"
    }

def get_csv_preview(csv_content: str, filename: str, max_transactions: int = 5) -> List[Dict[str, Any]]:
    """
    Get a preview of the first few transactions that would be created
    
    Args:
        csv_content: Raw CSV content as string
        filename: Name of the CSV file
        max_transactions: Maximum number of transactions to preview
        
    Returns:
        List of transaction dictionaries for preview
    """
    transactions = parse_bank_of_america_csv(csv_content, filename)
    
    preview = []
    for i, transaction in enumerate(transactions[:max_transactions]):
        preview.append({
            "date": transaction.date.strftime("%Y-%m-%d"),
            "description": transaction.description,
            "amount": transaction.amount,
            "category_id": transaction.category_id,
            "source_file": transaction.source_file,
            "original_row": transaction.original_row,
            "preview_index": i + 1
        })
    
    return preview
