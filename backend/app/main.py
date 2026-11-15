from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.app.config import settings
from backend.app.database.connection import db_manager, get_db
from backend.app.routes import auth, medicines, batches, sales, forecasts, expiry, inventory, reports

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.cors_origins_list,
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

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Pharmacy Forecasting & Inventory API",
        "environment": settings.ENVIRONMENT
    }

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
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
