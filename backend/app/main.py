"""
FastAPI main application for distributed personal finance tracker.
Serves both API endpoints and React frontend files.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from contextlib import asynccontextmanager

# Import database and routes
from .database import init_database, get_database_info
from .routes import transactions, charts, reports, categories

# Configuration
DEBUG_MODE = True  # Set to False to reduce console output

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup: Initialize database
    if DEBUG_MODE:
        print("🚀 Starting Personal Finance Tracker...")
    
    try:
        init_database()
        if DEBUG_MODE:
            db_info = get_database_info()
            print(f"📁 Database: {db_info.get('database_file', 'finance.db')}")
            print(f"📊 Transactions: {db_info.get('transactions', 0)}")
            print(f"📂 Categories: {db_info.get('categories', 0)}")
            print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")  # Always show errors
        raise
    
    yield
    
    # Shutdown
    if DEBUG_MODE:
        print("🛑 Shutting down Personal Finance Tracker...")

# Create FastAPI app
app = FastAPI(
    title="Personal Finance Tracker",
    description="Distributed 3-tier personal finance management application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        db_info = get_database_info()
        return {
            "status": "healthy",
            "database": db_info.get("status", "connected"),
            "transactions": db_info.get("transactions", 0),
            "categories": db_info.get("categories", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

# Serve React static files (for production)
frontend_build_path = "../../frontend/build"
if os.path.exists(frontend_build_path):
    app.mount("/static", StaticFiles(directory=f"{frontend_build_path}/static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        index_path = f"{frontend_build_path}/index.html"
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    if os.path.exists(frontend_build_path):
        return FileResponse(f"{frontend_build_path}/index.html")
    else:
        return {
            "message": "Personal Finance Tracker API",
            "version": "1.0.0",
            "docs": "/api/docs",
            "health": "/api/health"
        }

# Development server
if __name__ == "__main__":
    if DEBUG_MODE:
        print("🔧 Development mode - API: http://localhost:8000/api/docs")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info" if DEBUG_MODE else "warning"
    )
