from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import uuid
from typing import Optional
from app.schemas.schemas import ForecastRequest
from app.database.connection import get_db
from app.ml_engine.forecaster import MLForecaster

router = APIRouter(prefix="/forecasts", tags=["Demand Forecasting"])

@router.post("/generate")
def generate_forecast(req: ForecastRequest, db = Depends(get_db)):
    """
    Executes trained ML model inference (XGBoost, Random Forest, Ridge) on historical demand.
    Generates multi-horizon forecasts with confidence bounds and operational metrics.
    """
    med = db.medicines.find_one({"medicine_id": req.medicine_id}, {"_id": 0})
    if not med:
        raise HTTPException(status_code=404, detail=f"Medicine {req.medicine_id} not found")

    category = med.get("category", "N02BE")
    forecast_result = MLForecaster.generate_forecast(
        category=category,
        horizon_days=req.horizon_days,
        model_type=req.model_type
    )

    # Unique ID with millisecond precision and random entropy to prevent duplicate key race conditions
    now = datetime.utcnow()
    forecast_id = f"FCST-{req.medicine_id}-{int(now.timestamp() * 1000)}-{uuid.uuid4().hex[:6]}"
    forecast_doc = {
        "forecast_id": forecast_id,
        "medicine_id": req.medicine_id,
        "medicine_name": med.get("medicine_name"),
        "category": category,
        "horizon_days": req.horizon_days,
        "total_predicted_units": forecast_result["total_predicted_units"],
        "average_daily_demand": forecast_result["average_daily_demand"],
        "model_used": forecast_result["model_used"],
        "model_metrics": forecast_result["model_metrics"],
        "daily_forecast": forecast_result["daily_forecast"],
        "advisory_disclaimer": forecast_result["advisory_disclaimer"],
        "generated_at": now
    }

    # Store in MongoDB using upsert for absolute safety
    db.forecasts.update_one({"forecast_id": forecast_id}, {"$set": forecast_doc}, upsert=True)
    forecast_doc.pop("_id", None)
    return forecast_doc

@router.get("/metrics")
def get_all_model_metrics():
    """Returns test set validation metrics (MAE, RMSE, WAPE) across all candidate models."""
    MLForecaster.load_artifacts()
    return MLForecaster._metrics or {}

@router.get("/{medicine_id}")
def get_forecast_for_medicine(medicine_id: str, horizon: int = 30, db = Depends(get_db)):
    """Retrieves recent forecast or generates on-demand for a specific medicine."""
    med = db.medicines.find_one({"medicine_id": medicine_id}, {"_id": 0})
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # Check for recent cached forecast within last 24h
    recent = db.forecasts.find_one(
        {"medicine_id": medicine_id, "horizon_days": horizon},
        {"_id": 0},
        sort=[("generated_at", -1)]
    )
    if recent:
        return recent

    # Otherwise generate fresh
    category = med.get("category", "N02BE")
    res = MLForecaster.generate_forecast(category=category, horizon_days=horizon)
    res["medicine_id"] = medicine_id
    res["medicine_name"] = med.get("medicine_name")
    return res
