"""
Transaction routes for personal finance tracker
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas
from ..utils.csv_parser import validate_csv_format, get_csv_preview, parse_bank_of_america_csv

# Create router instance
router = APIRouter()

@router.post("/", response_model=schemas.TransactionOut)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction manually
    
    Example request body:
    {
        "description": "Coffee at Starbucks",
        "amount": -25.50,
        "date": "2025-10-03T10:30:00",
        "category_id": 1
    }
    
    Note: 
    - Negative amount = expense
    - Positive amount = income
    - category_id references the categories table
    """
    return crud.create_transaction_manually(db=db, transaction=transaction)

@router.get("/", response_model=list[schemas.TransactionOut])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all transactions with pagination
    
    Query parameters:
    - skip: Number of transactions to skip (default: 0)
    - limit: Maximum number of transactions to return (default: 100)
    
    Example: GET /api/transactions/?skip=0&limit=50
    """
    transactions = crud.get_transactions(db, skip=skip, limit=limit)
    return transactions

@router.get("/category/{category_id}", response_model=list[schemas.TransactionOut])
async def get_transactions_by_category_id(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all transactions for a specific category
    
    Path parameters:
    - category_id: ID of the category to filter by
    
    Example: GET /api/transactions/category/1
    """
    transactions = crud.get_transactions_by_category_id(db=db, category_id=category_id)
    return transactions

@router.get("/expense_or_income/{expense_or_income}", response_model=list[schemas.TransactionOut])
async def get_transaction_by_expense_or_income(
    expense_or_income: str,
    db: Session = Depends(get_db)
):
    sorted_transactions = crud.get_transactions_by_expense_or_income(db=db, expense_or_income=expense_or_income)
    return sorted_transactions

@router.patch("/{transaction_id}", response_model=schemas.TransactionOut)
async def update_transaction(
    transaction_id: int,                    
    transaction: schemas.TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates an individual transaction chosen by the user

    Path parameters:
    - transaction_id: ID of the transaction to update (from URL)

    Request body (all fields optional for PATCH), amount omitted in this example:
    {
        "description": "Updated coffee purchase",
        "date": "2025-10-03T10:30:00", 
        "category_id": 2
    }

    Note:
    - Only include fields you want to change
    - Omitted fields will remain unchanged
    - All fields are optional (partial update)

    Example: PATCH /api/transactions/50
    """
    return crud.update_transaction(db=db, transaction_id=transaction_id, transaction=transaction)

@router.post("/upload-csv", response_model=dict)
async def upload_csv_transactions(
    file: UploadFile = File(...),
    default_category_id: int = 7,  # Default to 'Other' category
    db: Session = Depends(get_db)
):
    """
    Upload and process a Bank of America CSV file to create transactions
    
    Parameters:
    - file: CSV file upload
    - default_category_id: Category to assign all transactions (default: 7 = 'Other')
    
    Returns:
    - Summary of processing results including number of transactions created
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read the CSV content
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        # Validate CSV format
        validation = validate_csv_format(csv_text)
        if not validation["is_valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid CSV format. Expected Bank of America format. Found {validation['total_rows']} rows but no valid data header."
            )
        
        # Parse transactions
        transactions = parse_bank_of_america_csv(csv_text, file.filename, default_category_id)
        
        if not transactions:
            return {
                "success": True,
                "message": "CSV processed successfully but no transactions found (empty file or only balance rows)",
                "filename": file.filename,
                "transactions_created": 0,
                "total_rows_processed": validation["total_rows"],
                "data_rows_found": validation["data_rows"],
                "default_category_id": default_category_id
            }
        
        # Create transactions in database
        created_transactions = crud.create_transactions_from_csv(db=db, transactions=transactions)
        
        return {
            "success": True,
            "message": f"Successfully imported {len(created_transactions)} transactions",
            "filename": file.filename,
            "transactions_created": len(created_transactions),
            "total_rows_processed": validation["total_rows"],
            "data_rows_found": validation["data_rows"],
            "default_category_id": default_category_id
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8 encoded CSV")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@router.post("/preview-csv", response_model=dict)
async def preview_csv_transactions(
    file: UploadFile = File(...),
    default_category_id: int = 7
):
    """
    Preview the first few transactions that would be created from a CSV file
    without actually creating them in the database
    
    Parameters:
    - file: CSV file upload
    - default_category_id: Category that would be assigned to transactions
    
    Returns:
    - Preview of transactions and validation results
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read the CSV content
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        # Validate and get preview
        validation = validate_csv_format(csv_text)
        preview = get_csv_preview(csv_text, file.filename, max_transactions=5)
        
        return {
            "success": True,
            "filename": file.filename,
            "validation": validation,
            "preview_transactions": preview,
            "total_transactions_found": validation["data_rows"],
            "default_category_id": default_category_id
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8 encoded CSV")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")