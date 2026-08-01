"""
Shared query helpers for the report routes
"""
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from .. import models

# Helper function to narrow a transaction query down to a year, and optionally a single month
def spending_period_filter(query, year: int = None, month: int = None):
    """
    Apply a year/month filter to an existing transaction query

    Returns:
    - The same query with the period filters applied, unchanged if both are None
    - Shared by the total and the top category so both are guaranteed to cover the exact
      same period
    """

    if year is not None:
        query = query.filter(extract('year', models.Transaction.date) == year)
    if month is not None:
        query = query.filter(extract('month', models.Transaction.date) == month)

    return query

# Helper function to sum all spending in a period with a single aggregate query
def total_spending_for_period(
    db: Session,
    year: int = None,
    month: int = None
) -> float | None:
    """
    Get the total spent in a period

    Returns:
    - The summed spending for the period
    - None (not 0.0) when the period holds no transactions, so callers can tell an empty
      period apart from a real total
    """

    # Builds the SUM query first, then narrows it to the requested period
    query = spending_period_filter(
        db.query(func.sum(func.abs(models.Transaction.amount))), year, month
    )

    return query.scalar()

# Helper function to find the single highest spending category in a period
def highest_spending_category(
    db: Session,
    year: int = None,
    month: int = None
) -> list:
    """
    Get the top spending category for a period

    Returns:
    - [category name, total spent] for the highest spending category
    - An empty list when nothing in the period carries a category, since the inner join drops
      uncategorized transactions while they still count toward the period total
    """

    total = func.sum(func.abs(models.Transaction.amount))

    # Joins categories to their transactions so the sum can be grouped per category
    query = db.query(
        models.Category.name,
        total.label('total_spending')
    ).join(
        models.Transaction,
        models.Category.id == models.Transaction.category_id
    )

    query = spending_period_filter(query, year, month)

    # Takes the highest total, the category id breaks ties so the winner stays deterministic
    # instead of SQLite being free to return either row
    top = query.group_by(
        models.Category.id,
        models.Category.name
    ).order_by(
        total.desc(),
        models.Category.id.asc()
    ).first()

    return [top[0], top[1]] if top else []
