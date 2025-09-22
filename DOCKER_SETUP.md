# Personal Finance Tracker - Docker Setup

## Quick Start with Nginx

### Option 1: Full Docker Stack (Recommended for Production-like Testing)
```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost (via Nginx)
# Direct Frontend: http://localhost:3000
# Direct Backend: http://localhost:8000
# API Docs: http://localhost/docs
```

### Option 2: Development Mode (Current Setup)
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev

# Access: Frontend at http://localhost:3000
```

## Nginx Configuration

The Nginx setup provides:

### Routing Rules:
- `http://localhost/` → React Frontend (port 3000)
- `http://localhost/api/` → FastAPI Backend (port 8000)
- `http://localhost/docs` → FastAPI Documentation
- `http://localhost/redoc` → Alternative API Docs

### Features:
- ✅ **Reverse Proxy**: Single entry point for both frontend and backend
- ✅ **Hot Reload**: Supports Vite HMR through WebSocket proxying
- ✅ **CORS Handling**: Proper headers for API requests
- ✅ **File Upload**: 50MB limit for bank statement uploads
- ✅ **Static Files**: Optimized caching for assets
- ✅ **Health Check**: `/health` endpoint for monitoring

## Docker Services

### Frontend Container:
- **Image**: Node.js 18 Alpine
- **Port**: 3000
- **Features**: Hot reload, volume mounting for development

### Backend Container:
- **Image**: Python 3.11 Slim
- **Port**: 8000  
- **Features**: Auto-reload, SQLite database persistence

### Nginx Container:
- **Image**: Nginx Alpine
- **Port**: 80 (main entry point)
- **Config**: Custom reverse proxy rules

## Commands

### Start Full Stack:
```bash
docker-compose up --build
```

### Start in Background:
```bash
docker-compose up -d --build
```

### Stop Services:
```bash
docker-compose down
```

### View Logs:
```bash
docker-compose logs -f [service_name]
```

### Rebuild Single Service:
```bash
docker-compose up --build [service_name]
```

## Development Workflow

1. **Code Changes**: Edit files normally
2. **Frontend**: Vite auto-reloads via HMR
3. **Backend**: FastAPI auto-reloads on file changes
4. **Nginx**: Proxies requests automatically

## Benefits of This Setup

- 🌐 **Production-like Environment**: Nginx handles routing like production
- 🔄 **Single Entry Point**: All requests through http://localhost
- 🚀 **Hot Reload**: Development speed maintained
- 📦 **Containerized**: Consistent environment across machines
- 🔧 **Easy Scaling**: Add more services easily