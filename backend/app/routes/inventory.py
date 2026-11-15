from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import math
from typing import Optional, List
from backend.app.database.connection import get_db
from backend.app.ml_engine.forecaster import MLForecaster

router = APIRouter(prefix="/inventory", tags=["Inventory Optimization & Restocking"])

@router.get("/summary")
def get_inventory_summary(db = Depends(get_db)):
    """
    Overview of total medicines, total available stock units, inventory valuation,
    low-stock counts, and category breakdown.
    """
    medicines = list(db.medicines.find({}, {"_id": 0}))
    batches = list(db.batches.find({}, {"_id": 0}))
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")

    total_stock_units = 0.0
    usable_stock_units = 0.0
    inventory_valuation = 0.0
    potential_revenue = 0.0
    low_stock_medicines = 0
    overstock_medicines = 0

    category_stock = {}

    for med in medicines:
        m_id = med["medicine_id"]
        cat = med.get("category", "OTHER")
        p_price = float(med.get("purchase_price", 10.0))
        s_price = float(med.get("selling_price", 20.0))
        reorder_th = med.get("reorder_threshold", 30)

        med_batches = [b for b in batches if b.get("medicine_id") == m_id]
        med_total_stock = sum(float(b.get("quantity_remaining", 0)) for b in med_batches)
        med_usable_stock = sum(float(b.get("quantity_remaining", 0)) for b in med_batches if b.get("expiry_date", "") > today_str)

        total_stock_units += med_total_stock
        usable_stock_units += med_usable_stock
        inventory_valuation += (med_total_stock * p_price)
        potential_revenue += (med_usable_stock * s_price)

        if med_usable_stock <= reorder_th:
            low_stock_medicines += 1
        elif med_usable_stock >= reorder_th * 4:
            overstock_medicines += 1

        category_stock[cat] = category_stock.get(cat, 0.0) + med_usable_stock

    return {
        "total_medicines": len(medicines),
        "total_batches": len(batches),
        "total_stock_units": round(total_stock_units, 1),
        "usable_stock_units": round(usable_stock_units, 1),
        "inventory_valuation": round(inventory_valuation, 2),
        "potential_revenue": round(potential_revenue, 2),
        "potential_gross_margin": round(potential_revenue - inventory_valuation, 2),
        "low_stock_medicines": low_stock_medicines,
        "overstock_medicines": overstock_medicines,
        "category_distribution": category_stock
    }

@router.get("/recommendations")
def get_restocking_recommendations(db = Depends(get_db)):
    """
    Intelligent Restocking Engine:
    Reorder Quantity = (Predicted Demand during Lead Time + Safety Stock) - Available Usable Stock - Incoming Orders
    """
    medicines = list(db.medicines.find({}, {"_id": 0}))
    batches = list(db.batches.find({}, {"_id": 0}))
    suppliers = {s["supplier_id"]: s for s in db.suppliers.find({}, {"_id": 0})}
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")

    recommendations = []

    for med in medicines:
        m_id = med["medicine_id"]
        cat = med.get("category", "N02BE")
        lead_time = int(med.get("lead_time_days", 3))
        safety_stock = float(med.get("safety_stock", 20))
        p_price = float(med.get("purchase_price", 10.0))

        # Usable stock: non-expired batches
        med_batches = [b for b in batches if b.get("medicine_id") == m_id]
        usable_stock = sum(float(b.get("quantity_remaining", 0)) for b in med_batches if b.get("expiry_date", "") > today_str)

        incoming_stock = 0.0
        pending_purchases = list(db.purchases.find({"medicine_id": m_id, "status": "Pending"}, {"_id": 0}))
        incoming_stock = sum(float(p.get("quantity_purchased", 0)) for p in pending_purchases)

        # ML Forecast for demand during lead time + review period
        forecast = MLForecaster.generate_forecast(category=cat, horizon_days=max(7, lead_time + 7))
        daily_velocity = forecast["average_daily_demand"]
        lead_time_demand = daily_velocity * lead_time

        # Reorder formula
        gross_need = lead_time_demand + safety_stock
        current_assets = usable_stock + incoming_stock
        raw_reorder_qty = gross_need - current_assets
        reorder_qty = max(0.0, raw_reorder_qty)

        if usable_stock == 0:
            status_urgency = "Critical Stockout"
            priority = 1
        elif usable_stock <= (safety_stock * 0.5):
            status_urgency = "Urgent Restock"
            priority = 2
        elif usable_stock <= safety_stock:
            status_urgency = "Restock Needed"
            priority = 3
        elif usable_stock >= (safety_stock + lead_time_demand * 4):
            status_urgency = "Overstocked"
            priority = 5
        else:
            status_urgency = "Adequate"
            priority = 4

        sup_id = med_batches[0].get("supplier_id", "SUP-01") if med_batches else "SUP-01"
        sup = suppliers.get(sup_id, {"name": "Primary Supplier", "lead_time_days": lead_time})

        suggested_qty = int(math.ceil(reorder_qty))

        recommendations.append({
            "medicine_id": m_id,
            "medicine_name": med.get("medicine_name"),
            "category": cat,
            "usable_stock": round(usable_stock, 1),
            "safety_stock": round(safety_stock, 1),
            "incoming_stock": round(incoming_stock, 1),
            "lead_time_days": lead_time,
            "average_daily_demand": round(daily_velocity, 2),
            "predicted_lead_time_demand": round(lead_time_demand, 1),
            "suggested_order_quantity": suggested_qty,
            "estimated_order_cost": round(suggested_qty * p_price, 2),
            "status": status_urgency,
            "priority": priority,
            "preferred_supplier": sup.get("name"),
            "supplier_id": sup_id
        })

    recommendations.sort(key=lambda x: (x["priority"], -x["suggested_order_quantity"]))
    return {
        "total_evaluated": len(recommendations),
        "items": recommendations
    }
