import sys
import os

# Ensure backend directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_current_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI, status
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
    connected = db_manager.connect()
    if connected:
        logger.info("Database connection established.")
    else:
        logger.warning("Database connection failed during startup. Check MongoDB status.")
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
    return {
        "status": "healthy",
        "service": "Pharmacy Forecasting & Inventory API",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/db", tags=["Health"])
@app.get("/api/health/db", tags=["Health"])
def database_health():
    try:
        db = get_db()
        if db is not None:
            db.command("ping")
            collections = db.list_collection_names()
            return {
                "status": "connected",
                "database": settings.DATABASE_NAME,
                "collections_count": len(collections),
                "collections": collections
            }
        return {"status": "disconnected", "error": "Database handle is None"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
