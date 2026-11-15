from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import Optional, List
from app.schemas.schemas import ExpiryAnalysisRequest
from app.database.connection import get_db
from app.ml_engine.risk_engine import ExpiryRiskEngine

router = APIRouter(prefix="/expiry", tags=["Expiry Risk Monitoring"])

@router.get("/alerts")
def get_expiry_alerts(
    risk_level: Optional[str] = None,
    db = Depends(get_db)
):
    """
    Returns active batch-level expiry alerts computed via velocity and days-to-expiry engine.
    """
    now = datetime.utcnow()
    batches = list(db.batches.find({}, {"_id": 0}))

    alerts = []
    for b in batches:
        med = db.medicines.find_one({"medicine_id": b["medicine_id"]}, {"_id": 0}) or {}
        purchase_price = float(med.get("purchase_price", 10.0))
        selling_price = float(med.get("selling_price", 20.0))
        qty_rem = float(b.get("quantity_remaining", 0))
        daily_sales = max(0.5, float(med.get("reorder_threshold", 30)) / 30.0)

        risk = ExpiryRiskEngine.calculate_batch_risk(
            quantity_remaining=qty_rem,
            purchase_price=purchase_price,
            expiry_date_str=b.get("expiry_date", ""),
            average_daily_sales=daily_sales,
            reference_date=now
        )

        alert = {
            "alert_id": f"ALT-{b['batch_id']}",
            "batch_id": b["batch_id"],
            "batch_number": b.get("batch_number"),
            "medicine_id": b["medicine_id"],
            "medicine_name": med.get("medicine_name", "Unknown Medicine"),
            "category": med.get("category", "N02BE"),
            "quantity_remaining": qty_rem,
            "expiry_date": b.get("expiry_date"),
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "days_until_expiry": risk["days_until_expiry"],
            "risk_level": risk["risk_level"],
            "risk_score": risk["risk_score"],
            "estimated_unsold_quantity": risk["estimated_unsold_quantity"],
            "inventory_value_at_risk": risk["inventory_value_at_risk"],
            "recommended_action": risk["recommended_action"],
            "generated_at": now.isoformat()
        }

        if not risk_level or risk["risk_level"].lower() == risk_level.lower():
            alerts.append(alert)

    risk_order = {"Expired": 0, "High Risk": 1, "Medium Risk": 2, "Low Risk": 3}
    alerts.sort(key=lambda x: (risk_order.get(x["risk_level"], 4), x["days_until_expiry"]))

    return {
        "total_alerts": len(alerts),
        "alerts": alerts
    }

@router.get("/summary")
def get_expiry_summary(db = Depends(get_db)):
    """Executive KPI summary of inventory at risk of expiry."""
    now = datetime.utcnow()
    batches = list(db.batches.find({}, {"_id": 0}))

    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    expired_count = 0
    total_val_at_risk = 0.0
    total_unsold_units = 0.0

    for b in batches:
        med = db.medicines.find_one({"medicine_id": b["medicine_id"]}, {"_id": 0}) or {}
        purchase_price = float(med.get("purchase_price", 10.0))
        daily_sales = max(0.5, float(med.get("reorder_threshold", 30)) / 30.0)
        risk = ExpiryRiskEngine.calculate_batch_risk(
            quantity_remaining=float(b.get("quantity_remaining", 0)),
            purchase_price=purchase_price,
            expiry_date_str=b.get("expiry_date", ""),
            average_daily_sales=daily_sales,
            reference_date=now
        )

        lvl = risk["risk_level"]
        if lvl == "High Risk":
            high_risk_count += 1
            total_val_at_risk += risk["inventory_value_at_risk"]
            total_unsold_units += risk["estimated_unsold_quantity"]
        elif lvl == "Medium Risk":
            medium_risk_count += 1
            total_val_at_risk += risk["inventory_value_at_risk"]
            total_unsold_units += risk["estimated_unsold_quantity"]
        elif lvl == "Expired":
            expired_count += 1
            total_val_at_risk += risk["inventory_value_at_risk"]
            total_unsold_units += risk["estimated_unsold_quantity"]
        else:
            low_risk_count += 1

    return {
        "high_risk_batches": high_risk_count,
        "medium_risk_batches": medium_risk_count,
        "low_risk_batches": low_risk_count,
        "expired_batches": expired_count,
        "total_inventory_value_at_risk": round(total_val_at_risk, 2),
        "total_estimated_unsold_units": round(total_unsold_units, 1),
        "evaluated_at": now.isoformat()
    }

@router.post("/analyze")
def analyze_batches(req: ExpiryAnalysisRequest, db = Depends(get_db)):
    """Triggers batch re-analysis and saves latest alerts in database."""
    now = datetime.utcnow()
    query = {}
    if req.batch_id:
        query["batch_id"] = req.batch_id
    elif req.medicine_id:
        query["medicine_id"] = req.medicine_id

    batches = list(db.batches.find(query, {"_id": 0}))
    updated_alerts = []

    for b in batches:
        med = db.medicines.find_one({"medicine_id": b["medicine_id"]}, {"_id": 0}) or {}
        purchase_price = float(med.get("purchase_price", 10.0))
        daily_sales = max(0.5, float(med.get("reorder_threshold", 30)) / 30.0)
        risk = ExpiryRiskEngine.calculate_batch_risk(
            quantity_remaining=float(b.get("quantity_remaining", 0)),
            purchase_price=purchase_price,
            expiry_date_str=b.get("expiry_date", ""),
            average_daily_sales=daily_sales,
            reference_date=now
        )
        alert_doc = {
            "alert_id": f"ALT-{b['batch_id']}",
            "batch_id": b["batch_id"],
            "medicine_id": b["medicine_id"],
            "risk_level": risk["risk_level"],
            "estimated_unsold_quantity": risk["estimated_unsold_quantity"],
            "days_until_expiry": risk["days_until_expiry"],
            "inventory_value_at_risk": risk["inventory_value_at_risk"],
            "recommended_action": risk["recommended_action"],
            "generated_at": now
        }
        db.expiry_alerts.update_one({"alert_id": alert_doc["alert_id"]}, {"$set": alert_doc}, upsert=True)
        updated_alerts.append(alert_doc)

    return {
        "message": f"Successfully analyzed {len(updated_alerts)} batches",
        "alerts_updated": len(updated_alerts)
    }
