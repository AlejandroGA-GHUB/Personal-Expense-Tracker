"""
FastAPI main application for distributed personal finance tracker.
Serves both API endpoints and React frontend files.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

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
        print("Starting Personal Finance Tracker...")
    
    try:
        init_database()
        if DEBUG_MODE:
            db_info = get_database_info()
            print(f"Database: {db_info.get('database_file', 'finance.db')}")
            print(f"Transactions: {db_info.get('transactions', 0)}")
            print(f"Categories: {db_info.get('categories', 0)}")
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization failed: {e}")  # Always show errors
        raise
    
    yield
    
    # Shutdown
    if DEBUG_MODE:
        print("Shutting down Personal Finance Tracker...")

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

# Serve the built React app (single-server production mode).
#
# Resolved from this file rather than the working directory, so it doesn't matter
# whether uvicorn was started from backend/ or the repo root. Vite outputs to
# frontend/dist with hashed bundles under dist/assets - not the dist/static that
# Create React App used to produce.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

# Absent until someone runs `npm run build`; the dev setup (React on :3000
# proxying to :8000) never touches this branch.
if FRONTEND_INDEX.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Client-side routing is served from the 404 handler rather than a catch-all
    # "/{full_path:path}" route. A catch-all matches every path, which stops Starlette
    # from ever reaching its trailing-slash redirect - "/api/categories" would 404
    # instead of redirecting to "/api/categories/", breaking API calls that omit the
    # slash. Handling it here means the SPA only answers once real routing found nothing.
    @app.exception_handler(StarletteHTTPException)
    async def serve_react_app(request: Request, exc: StarletteHTTPException):
        """Serve the React app for unmatched non-API routes, leave everything else alone"""
        if (exc.status_code == 404
                and request.method == "GET"
                and not request.url.path.startswith("/api")):
            return FileResponse(FRONTEND_INDEX)

        # Anything else keeps its real status, so the API still behaves like an API
        return await http_exception_handler(request, exc)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
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
        print("Development mode - API: http://localhost:8000/api/docs")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info" if DEBUG_MODE else "warning"
    )
