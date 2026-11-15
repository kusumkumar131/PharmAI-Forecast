import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_current_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_database_health():
    response = client.get("/api/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["database"] == "pharmacy_forecasting"

def test_list_medicines():
    response = client.get("/api/medicines")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) > 0

def test_list_batches():
    response = client.get("/api/batches")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert len(data["items"]) > 0
    sample_batch = data["items"][0]
    assert "days_until_expiry" in sample_batch
    assert "risk_level" in sample_batch

def test_expiry_alerts_and_summary():
    response = client.get("/api/expiry/summary")
    assert response.status_code == 200
    summary = response.json()
    assert "high_risk_batches" in summary
    assert "total_inventory_value_at_risk" in summary

    alerts_res = client.get("/api/expiry/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert "alerts" in alerts

def test_inventory_recommendations():
    response = client.get("/api/inventory/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    sample = data["items"][0]
    assert "suggested_order_quantity" in sample
    assert "predicted_lead_time_demand" in sample

def test_real_ml_demand_forecast():
    # Acceptance test: Submit real prediction for sample input through API loading saved model
    payload = {
        "medicine_id": "MED-N02BE-01",
        "horizon_days": 30
    }
    response = client.post("/api/forecasts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["medicine_name"] == "Paracetamol 500mg Tablets"
    assert "total_predicted_units" in data
    assert data["total_predicted_units"] > 0
    assert "daily_forecast" in data
    assert len(data["daily_forecast"]) == 30
    assert "model_metrics" in data
    assert "WAPE_percent" in data["model_metrics"]

def test_fefo_sale_and_inventory_decrement():
    # Acceptance test: Check stock decrementing and FEFO ordering
    batches_res = client.get("/api/batches?medicine_id=MED-N02BE-01").json()
    assert len(batches_res["items"]) > 0
    earliest_batch = batches_res["items"][0]
    initial_qty = earliest_batch["quantity_remaining"]

    sale_payload = {
        "items": [{"medicine_id": "MED-N02BE-01", "quantity": 5}],
        "customer_name": "Test Patient",
        "payment_method": "Cash"
    }
    sale_res = client.post("/api/sales", json=sale_payload)
    assert sale_res.status_code == 201
    sale_data = sale_res.json()
    assert "sale" in sale_data
    assert len(sale_data["sale"]["items"]) > 0

    # Verify inventory was decremented
    updated_batch = client.get(f"/api/batches/{earliest_batch['batch_id']}").json()
    assert updated_batch["quantity_remaining"] == initial_qty - 5
