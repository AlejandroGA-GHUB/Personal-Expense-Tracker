# 💰 Personal Finance Tracker - Distributed 3-Tier Desktop App

A privacy-first, 3-tier personal finance tracker that runs entirely on your local computer. Built with the same web architecture (Presentation → Business Logic → Data) but deployed as distributed desktop software. Each user gets their own SQLite database and complete data ownership - no servers, no authentication, no data sharing.

## 🏗️ 3-Tier Architecture (Local Deployment)

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER'S COMPUTER (Local)                       │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐  │
│  │ PRESENTATION    │    │ BUSINESS LOGIC  │    │     DATA     │  │
│  │   React App     │◄──►│    FastAPI      │◄──►│   SQLite     │  │
│  │   (Tier 1)      │    │    (Tier 2)     │    │   (Tier 3)   │  │
│  │   Port: 3000    │    │   Port: 8000    │    │  Local File  │  │
│  └─────────────────┘    └─────────────────┘    └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘

Tier 1: Frontend UI & User Interaction
Tier 2: API Logic & Business Rules  
Tier 3: Database & Data Persistence
```

## 🔄 Complete System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION FLOWS                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 1. CSV UPLOAD   │    │ 2. VIEW CHARTS  │    │ 3. MANAGE DATA  │    │ 4. GENERATE     │
│     FLOW        │    │      FLOW       │    │     FLOW        │    │   REPORTS       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User selects    │    │ User opens      │    │ User wants to   │    │ User selects    │
│ CSV file        │    │ Dashboard/      │    │ edit/add        │    │ report type &   │
│                 │    │ Charts page     │    │ transaction     │    │ time period     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                             TIER 1: PRESENTATION LAYER                                  │
│                                (React - Port 3000)                                      │
├─────────────────┬───────────────────┬───────────────────┬───────────────────────────────┤
│ UploadForm.jsx  │ Charts.jsx        │ Transaction Forms │ Reports.jsx                   │
│ - File picker   │ - Chart.js render │ - CRUD forms      │ - Date pickers                │
│ - Progress bar  │ - Data fetch      │ - Validation      │ - Export options              │
│ - Validation    │ - Auto-refresh    │ - Category select │ - Filter controls             │
└─────────────────┴───────────────────┴───────────────────┴───────────────────────────────┘
         │                       │                       │                       │
         ▼ HTTP POST             ▼ HTTP GET              ▼ HTTP CRUD             ▼ HTTP GET
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                             TIER 2: BUSINESS LOGIC LAYER                                │
│                                (FastAPI - Port 8000)                                    │
├─────────────────┬───────────────────┬───────────────────┬───────────────────────────────┤
│ /upload         │ /charts/*         │ /transactions/*   │ /reports/*                    │
│ - Parse CSV     │ - Aggregate data  │ - CRUD operations │ - Time-based queries          │
│ - Validate data │ - Calculate totals│ - Data validation │ - Transaction filtering       │
│ - Auto-category │ - Format for UI   │ - Business rules  │ - Period calculations         │
│ - Bulk insert   │ - Cache results   │ - Error handling  │ - Export formatting           │
└─────────────────┴───────────────────┴───────────────────┴───────────────────────────────┘
         │                       │                       │                       │
         ▼ ORM Bulk Operations   ▼ ORM Aggregate Queries ▼ ORM CRUD Operations   ▼ ORM Complex Queries
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              TIER 3: DATA LAYER                                         │
│                               (SQLite Database)                                         │
├─────────────────┬───────────────────┬───────────────────┬───────────────────────────────┤
│ Bulk INSERT     │ SELECT with       │ INSERT/UPDATE/    │ Complex JOINs &               │
│ transactions    │ GROUP BY, SUM     │ DELETE single     │ aggregate functions           │
│ with categories │ ORDER BY date     │ records           │ DATE() functions              │
│                 │ WHERE clauses     │                   │ Window functions              │
└─────────────────┴───────────────────┴───────────────────┴───────────────────────────────┘
         │                       │                       │                       │        
         ▼                       ▼                       ▼                       ▼         
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  
│ Data stored &   │    │ Chart data      │    │ Updated records │    │ Report data     │  
│ auto-categorized│    │ returned to UI  │    │ reflected in UI │    │ formatted &     │  
│                 │    │                 │    │                 │    │ ready for view  │  
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘  
                                                                                          
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW PATTERNS                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ Real-time: User action → API call → Database → Immediate UI update                      |             
│ Batch: CSV upload → Background processing → Bulk database operations → Summary          |        
│ Caching: Frequent chart requests cached in memory for performance                       |                 
│ Search: Real-time filtering without database calls using client-side caching            |        
└─────────────────────────────────────────────────────────────────────────────────────────┘

## 🚀 Key Features

- **🔒 100% Private**: All data stays on your computer
- **📊 Visual Analytics**: Interactive charts and spending insights  
- **📁 CSV Import**: Upload bank statements from any financial institution
- **🏷️ Smart Categorization**: Automatic transaction categorization
- **📈 Financial Reports**: Monthly, yearly, and custom period reports
- **⚡ Fast & Local**: No internet required after installation

## 🔄 Data Flow

```
CSV Upload → FastAPI Processing → SQLite Storage → React Visualization
    ↓              ↓                   ↓               ↓
Bank Data → Transaction Parser → Local Database → Interactive Charts
```

## 📁 Project Structure

```
personal-finance-tracker/
├── 🖥️ backend/                 # FastAPI Server (Port 8000)
│   ├── app/
│   │   ├── __init__.py         # Python package initialization
│   │   ├── main.py             # API server + React serving
│   │   ├── database.py         # SQLite connection & sessions
│   │   ├── models.py           # Transaction & Category models  
│   │   ├── schemas.py          # Pydantic data validation schemas
│   │   ├── crud.py             # Database operations
│   │   ├── routes/
│   │   │   ├── __init__.py     # Routes package initialization
│   │   │   ├── transactions.py # CRUD + CSV upload endpoints
│   │   │   ├── charts.py       # Chart data API endpoints
│   │   │   └── reports.py      # Financial reports API
│   │   └── utils/
│   │       ├── categorizer.py  # Auto-categorization logic
│   │       └── csv_parser.py   # CSV file parsing utilities
│   └── requirements.txt        # Python dependencies
│
├── 🌐 frontend/                # React App (Port 3000)
│   ├── src/
│   │   ├── App.jsx             # Main app & routing
│   │   ├── App.css             # Main app styles
│   │   ├── index.jsx           # React entry point
│   │   ├── index.css           # Global styles
│   │   ├── components/
│   │   │   ├── Charts.jsx      # Chart.js visualizations
│   │   │   ├── Charts.css      # Chart component styles
│   │   │   ├── CSVUpload.jsx   # CSV file upload interface
│   │   │   ├── CSVUpload.css   # Upload component styles
│   │   │   ├── Navbar.jsx      # Navigation component
│   │   │   ├── Navbar.css      # Navigation styles
│   │   │   ├── Reports.jsx     # Reports component
│   │   │   └── Reports.css     # Reports component styles
│   │   └── pages/
│   │       ├── Dashboard.jsx   # Main financial overview
│   │       ├── Dashboard.css   # Dashboard page styles
│   │       ├── Home.jsx        # Landing page
│   │       └── Home.css        # Home page styles
│   └── package.json            # Node dependencies
│
└── 💾 finance.db               # Your personal SQLite database
```

## 🛠️ 3-Tier Tech Stack

### Tier 1: Presentation Layer (React - Port 3000)
- **React 18** - Modern UI framework for user interface
- **Chart.js + react-chartjs-2** - Interactive financial charts
- **Axios** - HTTP client for API communication with Tier 2
- **React Router** - Client-side navigation
- **Vite** - Fast development and building

### Tier 2: Business Logic Layer (FastAPI - Port 8000)  
- **FastAPI** - High-performance Python API framework
- **Pydantic (schemas.py)** - Request/response data validation
- **SQLAlchemy** - Database ORM for data operations
- **Pandas** - CSV processing and financial calculations
- **Uvicorn** - ASGI server for local hosting

### Tier 3: Data Layer (SQLite)
- **Single file database** - Easy backup and portability
- **Transaction & Category models** - Optimized for financial data
- **Local storage** - Complete user data ownership

## 📊 API Endpoints

### Charts & Analytics
```
GET  /charts/spending-by-category    # Pie chart data
GET  /charts/monthly-summary         # Monthly spending trends
GET  /charts/balance-over-time       # Account balance progression
```

### Transaction Management
```
GET    /transactions                 # List all transactions
POST   /transactions                 # Create new transaction
PUT    /transactions/{id}            # Update existing transaction
DELETE /transactions/{id}            # Delete transaction
POST   /transactions/upload          # Upload CSV file
```

### Reports: Transaction Views by Time Period
```
# Core Time-Based Transaction Reports
GET  /reports/transactions/weekly/{year}/{week}      # Weekly transaction view
GET  /reports/transactions/monthly/{year}/{month}    # Monthly transaction view  
GET  /reports/transactions/yearly/{year}             # Yearly transaction view
GET  /reports/transactions/ytd/{year}                # Year-to-Date transactions
GET  /reports/transactions/mtd/{year}/{month}        # Month-to-Date transactions

# Additional Time Period Views
GET  /reports/transactions/daily/{year}/{month}/{day} # Daily transaction view
GET  /reports/transactions/quarterly/{year}/{quarter} # Quarterly transaction view
GET  /reports/transactions/period?start={date}&end={date} # Custom period view

# Dashboard & Summary
GET  /reports/dashboard                               # Main dashboard summary
GET  /reports/current-balance                        # Real-time account balance
```

## 🚀 Quick Start

### 1. Setup Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Database**: Automatically created as `finance.db`

## 📈 Chart Types & Time-Based Visualizations

| Chart Type | Purpose | Time Periods | Data Source |
|-----------|---------|--------------|-------------|
| **Pie Charts** | Spending breakdown by category | Daily, Weekly, Monthly, Yearly | Category totals |
| **Line Charts** | Spending/Income trends over time | Daily, Weekly, Monthly, Quarterly | Time-series aggregations |
| **Bar Charts** | Period comparisons (Month/Year) | Month-to-month, Year-to-year | Period summaries |
| **Balance Charts** | Account balance progression | Daily balance tracking | Running totals |
| **Stacked Charts** | Category spending over time | Monthly category trends | Category × Time matrix |
| **Combo Charts** | Income vs Expenses comparison | Monthly income/expense overlay | Dual-axis data |
| **Trend Charts** | Financial health indicators | 3, 6, 12 month trends | Moving averages |
| **Heatmaps** | Spending intensity by day/month | Calendar view patterns | Daily spending density |

### 📊 Time-Based Chart Categories

#### **Short-Term Analysis (Daily/Weekly)**
- Daily spending patterns
- Week-over-week comparisons  
- Weekend vs weekday analysis
- Recent transaction trends

#### **Medium-Term Analysis (Monthly/Quarterly)**
- Monthly budget vs actual
- Seasonal spending patterns
- Quarterly business reviews
- Category trend analysis

#### **Long-Term Analysis (Yearly/Multi-Year)**
- Annual financial summaries
- Year-over-year growth
- Long-term trend identification
- Financial goal tracking

#### **Custom Period Analysis**
- User-defined date ranges
- Rolling period reports (30/90 days)
- Comparative period analysis
- Event-based financial impact
## 🔧 Development Commands

```bash
# Backend development
cd backend && uvicorn app.main:app --reload

# Frontend development  
cd frontend && npm run dev

# Database inspection
sqlite3 finance.db ".tables"

# Build for production
cd frontend && npm run build
```

## 📦 Future Distribution

This project is designed to be packaged as a desktop application:
- **PyInstaller** for backend executable
- **Electron** for frontend desktop wrapper
- **Single installer** for end users
- **Offline operation** - no internet required

## 🔒 Privacy & Data Ownership

- ✅ All data stored locally on your computer
- ✅ No user accounts or authentication needed
- ✅ No data sent to external servers
- ✅ Complete control over your financial information
- ✅ Easy backup (just copy the `finance.db` file)

---

*Your financial data, your computer, your control.* 🔐