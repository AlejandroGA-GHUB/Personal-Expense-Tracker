"""
Chart routes for personal finance tracker
"""
from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from typing import Dict

# Create router instance
router = APIRouter()

# Endpoint to get category spending for a specific month/year (for charts)
@router.get("/category_spending_monthly", response_model=list[tuple])
async def get_category_spending_for_month(
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get spending per category for a specific month/year

    Returns:
    - A list of (category name, total spent) tuples ordered from highest to lowest
    - Categories with nothing spent in that month are left out, since the inner join only
      returns categories holding transactions

    Examples:
    - GET /api/charts/category_spending_monthly?month=3&year=2025
    """

    category_spending = db.query(
        models.Category.name,
        func.sum(func.abs(models.Transaction.amount)).label('total_spending')
    ).join(
        models.Transaction,
        models.Category.id == models.Transaction.category_id
    ).filter(
        extract('month', models.Transaction.date) == month,
        extract('year', models.Transaction.date) == year
    ).group_by(
        models.Category.id,
        models.Category.name
    ).order_by(
        func.sum(func.abs(models.Transaction.amount)).desc()
    ).all()
    
    return category_spending

# Endpoint to get category spending for entire year (for charts)
@router.get("/category_spending_yearly", response_model=list[tuple])
async def get_category_spending_for_year(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get spending per category for an entire year

    Returns:
    - A list of (category name, total spent) tuples ordered from highest to lowest
    - Categories with nothing spent that year are left out, since the inner join only returns
      categories holding transactions

    Examples:
    - GET /api/charts/category_spending_yearly?year=2025
    """

    category_spending = db.query(
        models.Category.name,
        func.sum(func.abs(models.Transaction.amount)).label('total_spending')
    ).join(
        models.Transaction,
        models.Category.id == models.Transaction.category_id
    ).filter(
        extract('year', models.Transaction.date) == year
    ).group_by(
        models.Category.id,
        models.Category.name
    ).order_by(
        func.sum(func.abs(models.Transaction.amount)).desc()
    ).all()
    
    return category_spending

# Endpoint to get total spending per year (for year-over-year comparison)
@router.get("/spending_by_year", response_model=list[tuple])
async def get_spending_by_year(
    db: Session = Depends(get_db)
):
    """
    Get total spending for each year that holds transactions

    Returns:
    - A list of (year, total spent) tuples in ascending year order
    - Years with no transactions are absent rather than zero, so the frontend plots only the
      years that actually exist

    Examples:
    - GET /api/charts/spending_by_year
    """

    yearly_spending = db.query(
        extract('year', models.Transaction.date).label('year'),
        func.sum(func.abs(models.Transaction.amount)).label('total_spending')
    ).group_by(
        extract('year', models.Transaction.date)
    ).order_by(
        extract('year', models.Transaction.date)
    ).all()
    
    return yearly_spending


# Endpoint to get monthly spending per category for a given year
@router.get("/categories_by_month", response_model=Dict[str, list])
async def get_category_spending_by_month(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get every category's month by month spending for a given year

    Returns:
    - A mapping of category name -> list of 12 monthly totals (Jan..Dec)
    - Every category is present even with no spending, padded with 0.0, so the frontend can
      chart them without filling gaps itself

    Examples:
    - GET /api/charts/categories_by_month?year=2025
    """

    categories = db.query(models.Category).all()
    result: Dict[str, list[float]] = {cat.name: [0.0] * 12 for cat in categories}

    rows = db.query(
        models.Category.name,
        extract('month', models.Transaction.date).label('month'),
        func.sum(func.abs(models.Transaction.amount)).label('total')
    ).join(
        models.Transaction,
        models.Category.id == models.Transaction.category_id
    ).filter(
        extract('year', models.Transaction.date) == year
    ).group_by(
        models.Category.id,
        models.Category.name,
        extract('month', models.Transaction.date)
    ).all()

    for name, month, total in rows:
        try:
            m = int(month) - 1
            if 0 <= m < 12:
                result[name][m] = float(total)
        except Exception:
            continue

    return result


# Endpoint for category year-to-year comparison
@router.get("/category_year_comparison", response_model=Dict[str, list])
async def get_category_year_comparison(
    category: str,
    years: str,  # Comma-separated years like "2024,2025"
    db: Session = Depends(get_db)
):
    """
    Get one category's month by month spending across multiple years

    Returns:
    - A mapping of year -> list of 12 monthly totals (Jan..Dec), e.g. {"2024": [12.34, ...]}
    - An empty mapping when the category name doesn't exist

    Examples:
    - GET /api/charts/category_year_comparison?category=Shopping&years=2024,2025
    """
    year_list = [int(y.strip()) for y in years.split(',')]
    result: Dict[str, list[float]] = {}
    
    # Find the category
    cat = db.query(models.Category).filter(models.Category.name == category).first()
    if not cat:
        return {}
    
    for year in year_list:
        monthly_values = [0.0] * 12
        
        rows = db.query(
            extract('month', models.Transaction.date).label('month'),
            func.sum(func.abs(models.Transaction.amount)).label('total')
        ).filter(
            models.Transaction.category_id == cat.id,
            extract('year', models.Transaction.date) == year
        ).group_by(
            extract('month', models.Transaction.date)
        ).all()
        
        for month, total in rows:
            try:
                m = int(month) - 1
                if 0 <= m < 12:
                    monthly_values[m] = float(total)
            except Exception:
                continue
        
        result[str(year)] = monthly_values
    
    return result
