import json
import os
from datetime import datetime, timedelta
from backend.app.database.connection import db_manager, get_db
from backend.app.services.auth_service import hash_password

def seed_database():
    print("Initiating database seeding...")
    connected = db_manager.connect()
    if not connected:
        print("Cannot seed: MongoDB connection failed.")
        return False
    
    db = get_db()
    
    # 1. Seed Admin User
    admin_email = "admin@pharmacy.com"
    existing_user = db.users.find_one({"email": admin_email})
    if not existing_user:
        hashed_password = hash_password("admin123")
        db.users.insert_one({
            "user_id": "USR-001",
            "name": "Dr. Sarah Mitchell",
            "email": admin_email,
            "password_hash": hashed_password,
            "role": "Chief Pharmacist",
            "created_at": datetime.utcnow()
        })
        print(f"Created default admin user: {admin_email}")
    else:
        print("Admin user already exists.")

    # 2. Seed Suppliers
    suppliers = [
        {"supplier_id": "SUP-01", "name": "Apex Pharma Logistics", "lead_time_days": 3, "contact": "orders@apexpharma.com", "rating": 4.8},
        {"supplier_id": "SUP-02", "name": "MedDistribute National", "lead_time_days": 4, "contact": "supply@meddistribute.com", "rating": 4.6},
        {"supplier_id": "SUP-03", "name": "BioHealth Direct", "lead_time_days": 5, "contact": "sales@biohealth.com", "rating": 4.9}
    ]
    for sup in suppliers:
        db.suppliers.update_one({"supplier_id": sup["supplier_id"]}, {"$set": sup}, upsert=True)
    print("Suppliers seeded.")

    # 3. Seed Medicines from Catalogue Mapping
    mapping_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "dataset", "processed", "medicine_catalogue_mapping.json")
    if os.path.exists(mapping_path):
        with open(mapping_path, "r", encoding="utf-8") as f:
            medicines = json.load(f)
        
        now = datetime.utcnow()
        for med in medicines:
            med["created_at"] = now
            med["updated_at"] = now
            db.medicines.update_one({"medicine_id": med["medicine_id"]}, {"$set": med}, upsert=True)
        print(f"Seeded {len(medicines)} medicines from catalogue mapping.")

        # 4. Seed Representative Batches for FEFO & Expiry Demonstration
        batch_configs = [
            # High Risk Batch (< 25 days left, 110 units remaining, substantial surplus at risk)
            {
                "batch_id": "BAT-2026-N02BE-A",
                "medicine_id": "MED-N02BE-01",
                "batch_number": "BN-26-8801",
                "quantity_received": 150,
                "quantity_remaining": 110,
                "purchase_date": (now - timedelta(days=340)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=350)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=22)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-01"
            },
            # Medium Risk Batch (55 days left)
            {
                "batch_id": "BAT-2026-N02BE-B",
                "medicine_id": "MED-N02BE-01",
                "batch_number": "BN-26-8802",
                "quantity_received": 150,
                "quantity_remaining": 120,
                "purchase_date": (now - timedelta(days=120)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=150)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=55)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-01"
            },
            # Safe Long-dated Batch (420 days left)
            {
                "batch_id": "BAT-2026-N02BE-C",
                "medicine_id": "MED-N02BE-01",
                "batch_number": "BN-26-9901",
                "quantity_received": 200,
                "quantity_remaining": 200,
                "purchase_date": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=40)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=420)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-02"
            },
            # Diclofenac Batches
            {
                "batch_id": "BAT-2026-M01AB-A",
                "medicine_id": "MED-M01AB-01",
                "batch_number": "DF-26-104",
                "quantity_received": 80,
                "quantity_remaining": 65,
                "purchase_date": (now - timedelta(days=200)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=220)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=35)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-02"
            },
            {
                "batch_id": "BAT-2026-M01AB-B",
                "medicine_id": "MED-M01AB-01",
                "batch_number": "DF-26-208",
                "quantity_received": 100,
                "quantity_remaining": 95,
                "purchase_date": (now - timedelta(days=20)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=380)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-01"
            },
            # Ibuprofen Batches
            {
                "batch_id": "BAT-2026-M01AE-A",
                "medicine_id": "MED-M01AE-01",
                "batch_number": "IB-26-440",
                "quantity_received": 90,
                "quantity_remaining": 60,
                "purchase_date": (now - timedelta(days=180)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=200)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=40)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-01"
            },
            # Salbutamol Inhalers
            {
                "batch_id": "BAT-2026-R03-A",
                "medicine_id": "MED-R03-01",
                "batch_number": "SB-26-501",
                "quantity_received": 50,
                "quantity_remaining": 25,
                "purchase_date": (now - timedelta(days=150)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=180)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=45)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-03"
            },
            # Cetirizine Batches
            {
                "batch_id": "BAT-2026-R06-A",
                "medicine_id": "MED-R06-01",
                "batch_number": "CT-26-702",
                "quantity_received": 120,
                "quantity_remaining": 85,
                "purchase_date": (now - timedelta(days=90)).strftime("%Y-%m-%d"),
                "manufacturing_date": (now - timedelta(days=100)).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=240)).strftime("%Y-%m-%d"),
                "supplier_id": "SUP-02"
            }
        ]
        for b in batch_configs:
            db.batches.update_one({"batch_id": b["batch_id"]}, {"$set": b}, upsert=True)
        print(f"Seeded {len(batch_configs)} inventory batches with varied expiry timelines.")

    print("Database seeding completed successfully!")
    return True

if __name__ == "__main__":
    seed_database()
