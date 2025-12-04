"""
Report routes for personal finance tracker
"""
from fastapi import APIRouter, Depends
from typing import Dict
from .. import models

from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..utils.reports_util import monthly_spending_category_util, yearly_spending_category_util

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
    Note: Returns a tuple containing the sum of all the users expenses, as well as the daily average
    
    Examples:
    - GET /api/reports/daily_and_total_expense
    """

    # Gets all transactions from the db, crud get_transactions not called for now as it uses pagination (Will become a crud operation)
    transactions = db.query(models.Transaction).all()

    # Checks if theres any transactions
    if len(transactions) == 0:
        return (0.0, 0.0)

    total_spending = 0
    amount_spent_per_day = {}

    # Loops transactions to build the total amount spent per day for the final conversion
    for transaction in transactions:
        if transaction.date.date() in amount_spent_per_day:
            amount_spent_per_day[transaction.date.date()] += abs(transaction.amount)
        else:
            amount_spent_per_day[transaction.date.date()] = abs(transaction.amount)
    
    # Adds the amount spent for each day together
    total_spending = sum(amount_spent_per_day.values())

    # Returns the total amount spent divided by the number of applicable days to get the average
    return (total_spending / len(amount_spent_per_day)), total_spending

# Endpoint to get the total amount spent for a specified month/year combination, and the highest spending category
@router.get("/monthly", response_model=tuple[float, list])
async def get_monthly_spending(
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get monthly spending for a specified month in a year

    (add)
    """

    # Queries the database to extract the specified monthly transactions for the given year (Will become a crud operation)
    specified_transactions = db.query(models.Transaction).filter(
        extract('month', models.Transaction.date) == month, 
        extract('year', models.Transaction.date) == year
    ).all()

    # Returns a default tuple if no transactions are found for this month, implying no spending
    if len(specified_transactions) == 0:
        return (0.0, [])
    
    highest_spending_category = monthly_spending_category_util(specified_transactions, db)
    
    # Calculates the sum from the returned list of all the valid transactions via a generator
    avg_monthly_spending = sum(abs(specified_transaction.amount) for specified_transaction in specified_transactions)
        
    return avg_monthly_spending, highest_spending_category

# Endpoint to get the total amount spent for each month in a year, and the highest spending category
@router.get("/yearly", response_model=tuple[list[float], list])
async def get_yearly_spending(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get monthly spending for a specified year

    (add)
    """

    transactions_per_month: list[list[models.Transaction]] = []
    for i in range(12):
        # Queries the database to extract the specified monthly transactions for the given year (Will become a crud operation)
        specified_transactions = db.query(models.Transaction).filter(
            extract('month', models.Transaction.date) == i + 1, 
            extract('year', models.Transaction.date) == year
        ).all()
        # Appends the monthly transaction list to the transactions_per_month list
        transactions_per_month.append(specified_transactions)

    # List to hold the amount spent for each month in the year
    spending_per_month: list[float] = []

    highest_spending_category = yearly_spending_category_util(transactions_per_month, db)

    # Iterates over each month in the year, calculating the sum via a generator, or applying 0.0 to the month by default
    # if there's no entries
    for monthly_transactions in transactions_per_month:
        if len(monthly_transactions) == 0:
            spending_per_month.append(0.0)
        else:
            spending_per_month.append(sum(abs(current_transaction.amount) for current_transaction in monthly_transactions))
    
    # Quick last minute check to ensure there was atleast one real transaction made,
    # returns an empty list otherwise for the frontend to easily process the data
    return spending_per_month if sum(spending_per_month) > 0.0 else [], highest_spending_category

# Endpoint to get the total amount spent per category using an optimized database query
# will update all report endpoints soon to optimized queries, as opposed to my current more raw implementation
@router.get("/category_spending", response_model=list[tuple])
async def get_total_spending_per_category(
    db: Session = Depends(get_db)
):

    highest_category = db.query(
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

    return highest_category
