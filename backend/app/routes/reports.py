"""
Report routes for personal finance tracker
"""
from fastapi import APIRouter, Depends

from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..utils.reports_util import (
    highest_spending_category,
    spending_period_filter,
    total_spending_for_period
)

# Create router instance
router = APIRouter()

# Combined endpoint to get the average daily spending across all transactions stored, and the total amount spent period
# Combined to optimize query usage as I didn't want to call a seperate endpoint to query all transactions again
@router.get("/daily_and_total_expenses", response_model=tuple())
async def get_daily_spending_average_and_total_expenses(
    db: Session = Depends(get_db)
):
    """
    Get average daily spending + total amount spent

    Returns:
    - A tuple of (average daily spending, total amount spent), or (0.0, 0.0) with no transactions
    - The average divides by the number of days that hold spending, not the calendar range,
      so untouched days never drag it down

    Examples:
    - GET /api/reports/daily_and_total_expenses
    """

    # Sums every expense and counts the distinct days they land on in a single pass
    total_spending, active_days = db.query(
        func.sum(func.abs(models.Transaction.amount)),
        func.count(func.distinct(func.date(models.Transaction.date)))
    ).one()

    # Checks if theres any transactions
    if not active_days:
        return (0.0, 0.0)

    # Returns the total amount spent divided by the number of applicable days to get the average
    return (total_spending / active_days), total_spending

# Endpoint to get the total amount spent for a specified month/year combination, and the highest spending category
@router.get("/monthly", response_model=tuple[float, list])
async def get_monthly_spending(
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get monthly spending for a specified month in a year

    Returns:
    - A tuple of (total spent that month, [category name, category total]), or (0.0, []) when
      the month holds no transactions
    - Uncategorized transactions count toward the total but can't win the category

    Examples:
    - GET /api/reports/monthly?month=3&year=2025
    """

    # Sums the month in the database instead of pulling its transactions back to add them up
    monthly_spending = total_spending_for_period(db, year=year, month=month)

    # Returns a default tuple if no transactions are found for this month, implying no spending
    if monthly_spending is None:
        return (0.0, [])

    return monthly_spending, highest_spending_category(db, year=year, month=month)

# Endpoint to get the total amount spent for each month in a year, and the highest spending category
@router.get("/yearly", response_model=tuple[list[float], list])
async def get_yearly_spending(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get monthly spending for a specified year

    Returns:
    - A tuple of ([12 monthly totals, Jan..Dec], [category name, category total])
    - The first element is an empty list when the year holds no spending, so the frontend can
      skip it without checking 12 zeroes

    Examples:
    - GET /api/reports/yearly?year=2025
    """

    month_number = extract('month', models.Transaction.date)

    # Groups the whole year by month in one query rather than one query per month, so only
    # months that were actually spent in come back
    monthly_totals = spending_period_filter(
        db.query(
            month_number.label('month'),
            func.sum(func.abs(models.Transaction.amount))
        ),
        year=year
    ).group_by(month_number).all()

    # Drops each returned month into a full 12 month list, leaving untouched months at 0.0
    spending_per_month: list[float] = [0.0] * 12
    for month, month_total in monthly_totals:
        spending_per_month[int(month) - 1] = month_total

    # Quick last minute check to ensure there was atleast one real transaction made,
    # returns an empty list otherwise for the frontend to easily process the data
    return (
        spending_per_month if sum(spending_per_month) > 0.0 else [],
        highest_spending_category(db, year=year)
    )

# Endpoint to get the total amount spent per category using an optimized database query
@router.get("/category_spending", response_model=list[tuple])
async def get_total_spending_per_category(
    db: Session = Depends(get_db)
):
    """
    Get the total spent in every category, highest first

    Returns:
    - A list of (category name, total spent) tuples ordered from highest to lowest
    - Categories that were never spent in are left out, since the inner join only returns
      categories holding transactions

    Examples:
    - GET /api/reports/category_spending
    """

    # Groups every transaction under its category and sums each group in the database
    spending_per_category = db.query(
        models.Category.name,
        func.sum(func.abs(models.Transaction.amount)).label('total_spending')
    ).join(
        models.Transaction,
        models.Category.id == models.Transaction.category_id
    ).group_by(
        models.Category.id,
        models.Category.name
    ).order_by(
        func.sum(func.abs(models.Transaction.amount)).desc()
    ).all()

    return spending_per_category
