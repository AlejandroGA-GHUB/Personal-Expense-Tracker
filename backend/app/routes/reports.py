"""
Report routes for personal finance tracker
"""
from fastapi import APIRouter

# Create router instance
router = APIRouter()

# Placeholder endpoint
@router.get("/")
async def get_reports():
    """Get reports - placeholder"""
    return {"message": "Reports endpoint - coming soon"}
