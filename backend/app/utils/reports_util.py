from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models

def monthly_spending_category_util(
    specified_transactions: list[models.Transaction],
    db: Session
) -> list:

    category_to_spending = {}
    highest_spent_category = [0, 0]

    for current_transaction in specified_transactions:
        update_category_to_spending(current_transaction, category_to_spending, highest_spent_category)
    
    # Check if any category was found
    if highest_spent_category[0] == 0:
        return []
    
    current_category = db.query(models.Category).get(highest_spent_category[0])
    if not current_category:
        return []

    return [current_category.name, highest_spent_category[1]]


def yearly_spending_category_util(
    specified_transactions: list[list[models.Transaction]],
    db: Session
) -> list:
    category_to_spending = {}
    highest_spent_category = [0, 0]

    for monthly_transactions in specified_transactions:
        for current_transaction in monthly_transactions:
            update_category_to_spending(current_transaction, category_to_spending, highest_spent_category)
    
    # Check if any category was found
    if highest_spent_category[0] == 0:
        return []
    
    current_category = db.query(models.Category).get(highest_spent_category[0])
    if not current_category:
        return []

    return [current_category.name, highest_spent_category[1]]

# Helper function
def update_category_to_spending(
    current_transaction: models.Transaction, 
    category_to_spending: dict, highest_spent_category: list
):
    # Skip transactions without a category
    if current_transaction.category_id is None:
        return
    
    if current_transaction.category_id in category_to_spending:
        category_to_spending[current_transaction.category_id] += abs(current_transaction.amount)
        if category_to_spending[current_transaction.category_id] > highest_spent_category[1]:
            highest_spent_category[1] = category_to_spending[current_transaction.category_id]
            highest_spent_category[0] = current_transaction.category_id
    else:
        category_to_spending[current_transaction.category_id] = abs(current_transaction.amount)
        if category_to_spending[current_transaction.category_id] > highest_spent_category[1]:
            highest_spent_category[1] = category_to_spending[current_transaction.category_id]
            highest_spent_category[0] = current_transaction.category_id
       
