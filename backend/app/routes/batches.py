from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import Optional, List
from app.schemas.schemas import BatchCreate, BatchUpdate
from app.database.connection import get_db
from app.ml_engine.risk_engine import ExpiryRiskEngine

router = APIRouter(prefix="/batches", tags=["Batches"])

@router.get("/")
def get_batches(
    medicine_id: Optional[str] = None,
    risk_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_db)
):
    query = {}
    if medicine_id:
        query["medicine_id"] = medicine_id

    batches = list(db.batches.find(query, {"_id": 0}).skip(skip).limit(limit))
    now = datetime.utcnow()

    enriched_batches = []
    for b in batches:
        # Get medicine details for pricing and velocity
        med = db.medicines.find_one({"medicine_id": b["medicine_id"]}, {"_id": 0}) or {}
        b["medicine_name"] = med.get("medicine_name", "Unknown Medicine")
        b["category"] = med.get("category", "N02BE")
        purchase_price = float(med.get("purchase_price", 10.0))
        b["purchase_price"] = purchase_price
        b["selling_price"] = float(med.get("selling_price", 20.0))

        # Dynamic risk assessment: daily sales is roughly monthly turnover / 30
        daily_sales = max(0.5, float(med.get("reorder_threshold", 30)) / 30.0)
        risk_data = ExpiryRiskEngine.calculate_batch_risk(
            quantity_remaining=float(b.get("quantity_remaining", 0)),
            purchase_price=purchase_price,
            expiry_date_str=b.get("expiry_date", now.strftime("%Y-%m-%d")),
            average_daily_sales=daily_sales,
            reference_date=now
        )
        b.update(risk_data)

        if not risk_filter or b["risk_level"].lower() == risk_filter.lower():
            enriched_batches.append(b)

    # Sort FEFO by default (earliest expiry first)
    enriched_batches.sort(key=lambda x: x.get("expiry_date", ""))
    return {
        "total": len(enriched_batches),
        "items": enriched_batches
    }

@router.get("/{batch_id}")
def get_batch_by_id(batch_id: str, db = Depends(get_db)):
    batch = db.batches.find_one({"batch_id": batch_id}, {"_id": 0})
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    med = db.medicines.find_one({"medicine_id": batch["medicine_id"]}, {"_id": 0}) or {}
    batch["medicine"] = med
    now = datetime.utcnow()
    daily_sales = max(0.5, float(med.get("reorder_threshold", 30)) / 30.0)
    risk_data = ExpiryRiskEngine.calculate_batch_risk(
        quantity_remaining=float(batch.get("quantity_remaining", 0)),
        purchase_price=float(med.get("purchase_price", 10.0)),
        expiry_date_str=batch.get("expiry_date", now.strftime("%Y-%m-%d")),
        average_daily_sales=daily_sales,
        reference_date=now
    )
    batch.update(risk_data)
    return batch

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_batch(batch_in: BatchCreate, db = Depends(get_db)):
    med = db.medicines.find_one({"medicine_id": batch_in.medicine_id})
    if not med:
        raise HTTPException(status_code=404, detail="Referenced medicine does not exist")

    b_id = batch_in.batch_id or f"BAT-{batch_in.medicine_id}-{int(datetime.utcnow().timestamp())}"
    existing = db.batches.find_one({"batch_id": b_id})
    if existing:
        raise HTTPException(status_code=400, detail="Batch ID already exists")

    doc = batch_in.dict()
    doc["batch_id"] = b_id
    if doc.get("quantity_remaining") is None:
        doc["quantity_remaining"] = doc["quantity_received"]
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()

    db.batches.insert_one(doc)
    doc.pop("_id", None)
    return doc

@router.put("/{batch_id}")
def update_batch(batch_id: str, batch_in: BatchUpdate, db = Depends(get_db)):
    existing = db.batches.find_one({"batch_id": batch_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Batch not found")

    update_fields = {k: v for k, v in batch_in.dict().items() if v is not None}
    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()
        db.batches.update_one({"batch_id": batch_id}, {"$set": update_fields})

    updated = db.batches.find_one({"batch_id": batch_id}, {"_id": 0})
    return updated
