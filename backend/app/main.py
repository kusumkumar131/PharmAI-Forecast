import sys
import os

# Ensure backend directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_current_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI, status, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.connection import db_manager, get_db
from app.routes import auth, medicines, batches, sales, forecasts, expiry, inventory, reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pharmacy_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Pharmacy Forecast API...")
    connected = db_manager.connect(max_retries=3, retry_delay=2.0)
    if connected:
        logger.info("Database connection established and ping verified.")
    else:
        logger.error("Database connection failed during startup. Running in degraded state.")
    yield
    logger.info("Shutting down API...")
    db_manager.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise-grade AI-powered Pharmacy Demand Forecasting & Expiry Risk Management API",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://pharmaai-eta.vercel.app",
]
for origin in settings.cors_origins_list:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all modular routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(medicines.router, prefix=settings.API_V1_STR)
app.include_router(batches.router, prefix=settings.API_V1_STR)
app.include_router(sales.router, prefix=settings.API_V1_STR)
app.include_router(forecasts.router, prefix=settings.API_V1_STR)
app.include_router(expiry.router, prefix=settings.API_V1_STR)
app.include_router(inventory.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "api_prefix": settings.API_V1_STR
    }

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    db = get_db()
    db_connected = db is not None and db_manager.is_connected()
    return {
        "status": "healthy",
        "database_connected": db_connected,
        "service": "Pharmacy Forecasting & Inventory API",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/db", tags=["Health"])
@app.get("/api/health/db", tags=["Health"])
def database_health(response: Response):
    try:
        db = get_db()
        if db is not None and db_manager.is_connected():
            collections = db.list_collection_names()
            return {
                "status": "connected",
                "database": settings.DATABASE_NAME,
                "collections_count": len(collections),
                "collections": collections
            }
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "disconnected",
            "database": settings.DATABASE_NAME,
            "error": "MongoDB ping check failed or database is not reachable"
        }
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "detail": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
