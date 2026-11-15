from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
from typing import List, Optional
from backend.app.schemas.schemas import MedicineCreate, MedicineUpdate
from backend.app.database.connection import get_db

router = APIRouter(prefix="/medicines", tags=["Medicines"])

@router.get("/")
def get_medicines(
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_db)
):
    query = {}
    if category:
        query["category"] = category.upper()
    if search:
        query["$or"] = [
            {"medicine_name": {"$regex": search, "$options": "i"}},
            {"composition": {"$regex": search, "$options": "i"}},
            {"manufacturer": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.medicines.find(query, {"_id": 0}).skip(skip).limit(limit)
    medicines = list(cursor)

    # Roll up available batches and usable stock
    for med in medicines:
        m_id = med["medicine_id"]
        batches = list(db.batches.find({"medicine_id": m_id}, {"_id": 0}))
        total_stock = sum(b.get("quantity_remaining", 0) for b in batches)
        med["total_stock"] = total_stock
        med["batch_count"] = len(batches)
        med["is_low_stock"] = total_stock <= med.get("reorder_threshold", 30)

    total_count = db.medicines.count_documents(query)
    return {
        "total": total_count,
        "items": medicines
    }

@router.get("/{medicine_id}")
def get_medicine_by_id(medicine_id: str, db = Depends(get_db)):
    med = db.medicines.find_one({"medicine_id": medicine_id}, {"_id": 0})
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    # Attach batches
    batches = list(db.batches.find({"medicine_id": medicine_id}, {"_id": 0}))
    med["batches"] = batches
    med["total_stock"] = sum(b.get("quantity_remaining", 0) for b in batches)
    return med

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_medicine(med_in: MedicineCreate, db = Depends(get_db)):
    m_id = med_in.medicine_id or f"MED-{med_in.category}-{int(datetime.utcnow().timestamp())}"
    existing = db.medicines.find_one({"medicine_id": m_id})
    if existing:
        raise HTTPException(status_code=400, detail="Medicine ID already exists")

    doc = med_in.dict()
    doc["medicine_id"] = m_id
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    db.medicines.insert_one(doc)
    doc.pop("_id", None)
    return doc

@router.put("/{medicine_id}")
def update_medicine(medicine_id: str, med_in: MedicineUpdate, db = Depends(get_db)):
    existing = db.medicines.find_one({"medicine_id": medicine_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Medicine not found")

    update_fields = {k: v for k, v in med_in.dict().items() if v is not None}
    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()
        db.medicines.update_one({"medicine_id": medicine_id}, {"$set": update_fields})

    updated = db.medicines.find_one({"medicine_id": medicine_id}, {"_id": 0})
    return updated

@router.delete("/{medicine_id}")
def delete_medicine(medicine_id: str, db = Depends(get_db)):
    result = db.medicines.delete_one({"medicine_id": medicine_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Medicine not found")
    # Also remove associated batches
    db.batches.delete_many({"medicine_id": medicine_id})
    return {"message": "Medicine and associated batches deleted successfully"}
