from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "Pharmacist"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# --- Medicine Schemas ---
class MedicineCreate(BaseModel):
    medicine_id: Optional[str] = None
    medicine_name: str
    category: str  # ATC Code (e.g. N02BE, M01AB, etc.)
    therapeutic_group: Optional[str] = ""
    manufacturer: str
    composition: str
    strength: str
    unit: str
    purchase_price: float
    selling_price: float
    reorder_threshold: Optional[int] = 30
    lead_time_days: Optional[int] = 3
    safety_stock: Optional[int] = 20
    description: Optional[str] = ""

class MedicineUpdate(BaseModel):
    medicine_name: Optional[str] = None
    category: Optional[str] = None
    therapeutic_group: Optional[str] = None
    manufacturer: Optional[str] = None
    composition: Optional[str] = None
    strength: Optional[str] = None
    unit: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    reorder_threshold: Optional[int] = None
    lead_time_days: Optional[int] = None
    safety_stock: Optional[int] = None
    description: Optional[str] = None

# --- Batch Schemas ---
class BatchCreate(BaseModel):
    batch_id: Optional[str] = None
    medicine_id: str
    batch_number: str
    quantity_received: float
    quantity_remaining: Optional[float] = None
    purchase_date: str
    manufacturing_date: str
    expiry_date: str
    supplier_id: Optional[str] = "SUP-01"

class BatchUpdate(BaseModel):
    batch_number: Optional[str] = None
    quantity_remaining: Optional[float] = None
    expiry_date: Optional[str] = None
    supplier_id: Optional[str] = None

# --- Sale Item Schema ---
class SaleItem(BaseModel):
    medicine_id: str
    quantity: float
    batch_id: Optional[str] = None

class SaleCreate(BaseModel):
    items: List[SaleItem]
    customer_name: Optional[str] = "Walk-in Patient"
    payment_method: Optional[str] = "Cash"
    notes: Optional[str] = ""

# --- Forecasting Schema ---
class ForecastRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    medicine_id: str
    horizon_days: int = Field(default=30, ge=7, le=90)
    model_type: Optional[str] = "best"

# --- Expiry Analysis Request ---
class ExpiryAnalysisRequest(BaseModel):
    batch_id: Optional[str] = None
    medicine_id: Optional[str] = None
