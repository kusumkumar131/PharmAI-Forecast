from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import Optional, List
from backend.app.schemas.schemas import SaleCreate
from backend.app.database.connection import get_db

router = APIRouter(prefix="/sales", tags=["Sales"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def record_sale(sale_in: SaleCreate, db = Depends(get_db)):
    """
    Records a sale transaction with automatic FEFO batch allocation and stock decrementing.
    Never dispenses from expired batches.
    """
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")
    transaction_id = f"TXN-{int(now.timestamp() * 1000)}"

    dispensed_items = []
    total_sale_amount = 0.0

    for item in sale_in.items:
        med = db.medicines.find_one({"medicine_id": item.medicine_id})
        if not med:
            raise HTTPException(status_code=404, detail=f"Medicine {item.medicine_id} not found")

        qty_to_fulfill = float(item.quantity)
        unit_price = float(med.get("selling_price", 0.0))

        # If batch specified manually, verify it
        if item.batch_id:
            batch = db.batches.find_one({"batch_id": item.batch_id, "medicine_id": item.medicine_id})
            if not batch:
                raise HTTPException(status_code=404, detail=f"Batch {item.batch_id} not found")
            if batch.get("expiry_date", "") <= today_str:
                raise HTTPException(status_code=400, detail=f"Cannot dispense: Batch {item.batch_id} has expired!")
            if float(batch.get("quantity_remaining", 0)) < qty_to_fulfill:
                raise HTTPException(status_code=400, detail=f"Insufficient stock in batch {item.batch_id}. Available: {batch.get('quantity_remaining')}")

            # Decrement atomically
            db.batches.update_one(
                {"batch_id": item.batch_id},
                {"$inc": {"quantity_remaining": -qty_to_fulfill}, "$set": {"updated_at": now}}
            )
            subtotal = qty_to_fulfill * unit_price
            dispensed_items.append({
                "medicine_id": item.medicine_id,
                "medicine_name": med.get("medicine_name"),
                "batch_id": item.batch_id,
                "batch_number": batch.get("batch_number"),
                "quantity": qty_to_fulfill,
                "unit_price": unit_price,
                "subtotal": round(subtotal, 2)
            })
            total_sale_amount += subtotal
        else:
            # Automatic FEFO Allocation: Find valid, non-expired batches sorted by earliest expiry
            valid_batches = list(db.batches.find({
                "medicine_id": item.medicine_id,
                "expiry_date": {"$gt": today_str},
                "quantity_remaining": {"$gt": 0}
            }).sort("expiry_date", 1))

            total_available = sum(float(b.get("quantity_remaining", 0)) for b in valid_batches)
            if total_available < qty_to_fulfill:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient usable stock for {med.get('medicine_name')}. Required: {qty_to_fulfill}, Usable Non-Expired: {total_available}"
                )

            remaining_need = qty_to_fulfill
            for b in valid_batches:
                if remaining_need <= 0:
                    break
                avail = float(b.get("quantity_remaining", 0))
                deduct = min(avail, remaining_need)

                # Atomically decrement batch
                db.batches.update_one(
                    {"batch_id": b["batch_id"]},
                    {"$inc": {"quantity_remaining": -deduct}, "$set": {"updated_at": now}}
                )

                subtotal = deduct * unit_price
                dispensed_items.append({
                    "medicine_id": item.medicine_id,
                    "medicine_name": med.get("medicine_name"),
                    "batch_id": b["batch_id"],
                    "batch_number": b.get("batch_number"),
                    "quantity": deduct,
                    "unit_price": unit_price,
                    "subtotal": round(subtotal, 2)
                })
                total_sale_amount += subtotal
                remaining_need -= deduct

    # Record complete transaction
    sale_record = {
        "transaction_id": transaction_id,
        "sale_date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "customer_name": sale_in.customer_name,
        "payment_method": sale_in.payment_method,
        "notes": sale_in.notes,
        "items": dispensed_items,
        "total_amount": round(total_sale_amount, 2),
        "created_at": now
    }
    db.sales.insert_one(sale_record)
    sale_record.pop("_id", None)

    return {
        "message": "Sale transaction processed successfully with FEFO batch deduction",
        "sale": sale_record
    }

@router.get("/")
def get_sales(
    medicine_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    db = Depends(get_db)
):
    query = {}
    if medicine_id:
        query["items.medicine_id"] = medicine_id

    cursor = db.sales.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    sales = list(cursor)
    total_count = db.sales.count_documents(query)
    return {
        "total": total_count,
        "items": sales
    }

@router.get("/summary")
def get_sales_summary(db = Depends(get_db)):
    """Summary metrics of revenue, total items sold, and top selling medicines."""
    sales = list(db.sales.find({}, {"_id": 0}))
    total_revenue = sum(s.get("total_amount", 0) for s in sales)
    total_transactions = len(sales)

    med_sales = {}
    for s in sales:
        for it in s.get("items", []):
            m_id = it.get("medicine_id")
            med_sales[m_id] = med_sales.get(m_id, 0) + it.get("quantity", 0)

    top_meds = sorted(med_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    top_selling = []
    for m_id, qty in top_meds:
        med = db.medicines.find_one({"medicine_id": m_id}, {"_id": 0}) or {}
        top_selling.append({
            "medicine_id": m_id,
            "medicine_name": med.get("medicine_name", m_id),
            "units_sold": qty
        })

    return {
        "total_revenue": round(total_revenue, 2),
        "total_transactions": total_transactions,
        "top_selling_medicines": top_selling
    }
