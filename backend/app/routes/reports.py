from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional
from app.database.connection import get_db
from app.ml_engine.risk_engine import ExpiryRiskEngine

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/sales")
def get_sales_report(days: int = 30, db = Depends(get_db)):
    sales = list(db.sales.find({}, {"_id": 0}))
    total_sales_value = sum(s.get("total_amount", 0) for s in sales)
    
    # Category sales breakdown
    category_totals = {}
    for s in sales:
        for it in s.get("items", []):
            med = db.medicines.find_one({"medicine_id": it.get("medicine_id")}, {"_id": 0}) or {}
            cat = med.get("category", "OTHER")
            category_totals[cat] = category_totals.get(cat, 0.0) + it.get("subtotal", 0.0)

    return {
        "report_period_days": days,
        "total_revenue": round(total_sales_value, 2),
        "total_transactions": len(sales),
        "sales_by_category": category_totals,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/inventory")
def get_inventory_report(db = Depends(get_db)):
    medicines = list(db.medicines.find({}, {"_id": 0}))
    batches = list(db.batches.find({}, {"_id": 0}))
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")

    report_items = []
    total_inventory_cost = 0.0
    total_inventory_sales_potential = 0.0

    for med in medicines:
        m_id = med["medicine_id"]
        med_batches = [b for b in batches if b.get("medicine_id") == m_id]
        total_qty = sum(float(b.get("quantity_remaining", 0)) for b in med_batches)
        usable_qty = sum(float(b.get("quantity_remaining", 0)) for b in med_batches if b.get("expiry_date", "") > today_str)
        cost_val = total_qty * float(med.get("purchase_price", 0))
        sales_val = usable_qty * float(med.get("selling_price", 0))
        total_inventory_cost += cost_val
        total_inventory_sales_potential += sales_val

        report_items.append({
            "medicine_id": m_id,
            "medicine_name": med.get("medicine_name"),
            "category": med.get("category"),
            "total_quantity": total_qty,
            "usable_quantity": usable_qty,
            "purchase_price": med.get("purchase_price"),
            "selling_price": med.get("selling_price"),
            "inventory_valuation": round(cost_val, 2),
            "expected_revenue": round(sales_val, 2)
        })

    return {
        "total_sku_count": len(medicines),
        "total_inventory_valuation": round(total_inventory_cost, 2),
        "potential_retail_revenue": round(total_inventory_sales_potential, 2),
        "projected_profit": round(total_inventory_sales_potential - total_inventory_cost, 2),
        "details": report_items,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/expiry")
def get_expiry_report(db = Depends(get_db)):
    batches = list(db.batches.find({}, {"_id": 0}))
    now = datetime.utcnow()

    expiry_loss_estimate = 0.0
    quarantine_items = []
    high_risk_items = []

    for b in batches:
        med = db.medicines.find_one({"medicine_id": b["medicine_id"]}, {"_id": 0}) or {}
        purchase_price = float(med.get("purchase_price", 10.0))
        risk = ExpiryRiskEngine.calculate_batch_risk(
            quantity_remaining=float(b.get("quantity_remaining", 0)),
            purchase_price=purchase_price,
            expiry_date_str=b.get("expiry_date", ""),
            average_daily_sales=float(med.get("reorder_threshold", 30)) / 10.0,
            reference_date=now
        )
        if risk["risk_level"] in ["High Risk", "Expired"]:
            item_detail = {
                "batch_id": b["batch_id"],
                "batch_number": b.get("batch_number"),
                "medicine_name": med.get("medicine_name"),
                "expiry_date": b.get("expiry_date"),
                "days_until_expiry": risk["days_until_expiry"],
                "estimated_unsold_quantity": risk["estimated_unsold_quantity"],
                "inventory_value_at_risk": risk["inventory_value_at_risk"],
                "action": risk["recommended_action"]
            }
            if risk["risk_level"] == "Expired":
                quarantine_items.append(item_detail)
            else:
                high_risk_items.append(item_detail)
            expiry_loss_estimate += risk["inventory_value_at_risk"]

    return {
        "projected_expiry_loss": round(expiry_loss_estimate, 2),
        "expired_quarantine_batches_count": len(quarantine_items),
        "high_risk_batches_count": len(high_risk_items),
        "quarantine_batches": quarantine_items,
        "high_risk_batches": high_risk_items,
        "generated_at": datetime.utcnow().isoformat()
    }
