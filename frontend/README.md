# Personal Finance Tracker - Frontend

## Overview
React-based frontend application for the Personal Finance Tracker built with Vite for fast development and optimized builds.

## Tech Stack
- **Framework**: React 18.2.0
- **Build Tool**: Vite 4.4.5
- **Language**: JavaScript (JSX)
- **Styling**: CSS3

## Dependencies

### Core Dependencies
```json
{
  "react": "^18.2.0",              // React framework
  "react-dom": "^18.2.0",          // React DOM rendering
  "react-router-dom": "^7.9.1"     // Client-side routing
}
```

### API & Data Visualization
```json
{
  "axios": "^1.12.2",              // HTTP client for API calls
  "chart.js": "^4.5.0",            // Charting library
  "react-chartjs-2": "^5.3.0"      // React wrapper for Chart.js
}
```

### Development Dependencies
```json
{
  "@vitejs/plugin-react": "^4.0.3", // Vite React plugin
  "vite": "^4.4.5",                 // Build tool and dev server
  "eslint": "^8.45.0",              // Code linting
  "eslint-plugin-react": "^7.32.2", // React-specific linting rules
  "eslint-plugin-react-hooks": "^4.6.0", // React hooks linting
  "eslint-plugin-react-refresh": "^0.4.3" // Fast refresh support
}
```

## Installation

### Prerequisites
- Node.js v18+ 
- npm v8+

### Setup Commands
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development Server
- **URL**: http://localhost:3000
- **API Proxy**: Automatically proxies `/api/*` requests to `http://localhost:8000`

## Project Structure
```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Charts.jsx      # Chart components using Chart.js
│   │   ├── Navbar.jsx      # Navigation component
│   │   ├── Reports.jsx     # Financial reports display
│   │   └── UploadForm.jsx  # File upload component
│   ├── pages/              # Page-level components
│   │   ├── Dashboard.jsx   # Main dashboard view
│   │   ├── Home.jsx        # Landing page
│   │   └── Login.jsx       # Authentication page
│   ├── App.jsx             # Main application component
│   ├── index.jsx           # Application entry point
│   ├── App.css             # Component-specific styles
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
└── vite.config.js          # Vite configuration
```

## Available Scripts
- `npm run dev` - Start development server with hot reload
- `npm run build` - Build optimized production bundle
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint code quality checks

## Configuration
- **Vite Config**: `vite.config.js` - Build tool settings and dev server proxy
- **ESLint**: React-specific linting rules enabled
- **Port**: Development server runs on port 3000
- **API Integration**: Backend API calls via axios to FastAPI (port 8000)

## Dependencies Purpose

| Package | Purpose | Usage |
|---------|---------|-------|
| `axios` | HTTP Client | API calls to FastAPI backend |
| `chart.js` | Charting | Financial data visualization |
| `react-chartjs-2` | React Charts | React wrapper for Chart.js |
| `react-router-dom` | Routing | Navigation between pages |
| `vite` | Build Tool | Fast development and optimized builds |

## Chart.js Integration
The app uses Chart.js for financial visualizations:
- **Pie Charts**: Spending by category
- **Line Charts**: Spending trends over time  
- **Bar Charts**: Monthly/yearly comparisons
- **Doughnut Charts**: Account balances

## API Integration
All backend communication uses axios with the configured proxy:
```javascript
// API calls automatically proxy to http://localhost:8000
axios.get('/api/transactions')
axios.post('/api/upload', formData)
```