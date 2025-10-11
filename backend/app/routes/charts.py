"""
Chart routes for personal finance tracker
"""
from fastapi import APIRouter

# Create router instance
router = APIRouter()

# Placeholder endpoint
@router.get("/")
async def get_charts():
    """Get chart data - placeholder"""
    return {"message": "Charts endpoint - coming soon"}
