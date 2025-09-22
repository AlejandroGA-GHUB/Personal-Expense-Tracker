# Personal Finance Tracker

A modern 3-tier web application for tracking personal finances with bank statement uploads, transaction categorization, and financial reporting.

## Frontend Dependencies Documentation

### Installed Packages

#### Core Dependencies
```bash
npm install react@^18.2.0 react-dom@^18.2.0
```
- **react**: React framework for building user interfaces
- **react-dom**: React package for working with the DOM

#### Navigation & Routing
```bash
npm install react-router-dom@^7.9.1
```
- **react-router-dom**: Client-side routing for single-page applications

#### API Communication
```bash
npm install axios@^1.12.2
```
- **axios**: Promise-based HTTP client for making API requests to FastAPI backend

#### Data Visualization & Charts  
```bash
npm install chart.js@^4.5.0 react-chartjs-2@^5.3.0
```
- **chart.js**: Powerful charting library for creating financial charts
- **react-chartjs-2**: React wrapper for Chart.js integration

#### Development Tools
```bash
npm install --save-dev vite@^4.4.5 @vitejs/plugin-react@^4.0.3
npm install --save-dev eslint@^8.45.0 eslint-plugin-react@^7.32.2
npm install --save-dev eslint-plugin-react-hooks@^4.6.0 eslint-plugin-react-refresh@^0.4.3
```

### Installation Summary

To replicate this frontend setup:

```bash
# 1. Create Vite React project structure (already done)
# 2. Install all dependencies
cd frontend
npm install

# 3. Additional packages for finance tracker
npm install axios chart.js react-chartjs-2 react-router-dom

# 4. Start development server
npm run dev
```

### Package Purposes

| Package | Purpose | Usage in Finance Tracker |
|---------|---------|--------------------------|
| `axios` | HTTP Client | API calls to FastAPI backend (transactions, uploads) |
| `chart.js` | Charting Engine | Financial data visualization core |
| `react-chartjs-2` | React Charts | Pie charts (categories), Line charts (trends), Bar charts (monthly) |
| `react-router-dom` | Navigation | Routing between Dashboard, Reports, Upload pages |
| `vite` | Build Tool | Fast development server and optimized production builds |

### Chart Types for Finance Features
- **Pie Charts**: Spending breakdown by category
- **Line Charts**: Spending trends over time
- **Bar Charts**: Monthly/yearly comparisons  
- **Doughnut Charts**: Account balance visualization

## Tech Stack Summary

### Frontend (Port 3000)
- React 18 + Vite
- Chart.js for financial visualizations
- Axios for API communication
- React Router for navigation

### Backend (Port 8000)  
- FastAPI with Python
- SQLite database
- JWT authentication
- Automatic API docs

### Key Commands
```bash
# Frontend development
cd frontend && npm run dev

# Backend development  
cd backend && uvicorn app.main:app --reload

# Access points
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```