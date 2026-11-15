# Pharmacy Medicine Demand & Expiry-Risk Forecasting Platform
### AI-Powered Pharmacy Inventory & Decision-Support System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![XGBoost](https://img.shields.io/badge/XGBoost-Enabled-EB5424)](https://xgboost.readthedocs.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20%2F%20Local-47A248?logo=mongodb)](https://www.mongodb.com)
[![Tests](https://img.shields.io/badge/Tests-8%2F8%20Passed-success)](./backend/tests)

---

## 1. Project Overview & Business Value
Pharmacies face two critical challenges:
1. **Overstocking**: Retaining excess medication batches that expire before sale, generating financial losses and hazardous waste.
2. **Understocking**: Experiencing stockouts of high-velocity medicines, leading to lost revenue and disrupted patient care.

This project delivers an enterprise-grade, production-style web application integrating:
- **Machine Learning Demand Forecasting**: Multi-horizon predictions (7, 30, and 90 days) using XGBoost, Random Forest, and Ridge regression trained on 2,106 continuous days of pharmaceutical sales data.
- **Batch Expiry-Risk Prediction**: Calculating days-to-expiry, depletion velocity, unsold inventory surplus, and financial value-at-risk.
- **First-Expiry-First-Out (FEFO) Protocol**: Automated batch dispensing order preventing expired drug sales.
- **Intelligent Restocking Recommendations**: Calculating reorder quantities based on lead time demand, safety stock, and usable on-hand inventory.

> **Operational Decision-Support Disclaimer**:
> This platform provides operational guidance for inventory and supply-chain decision support. It does **not** provide medical advice, diagnosis, or clinical treatment prescribing.

---

## 2. Technology Stack

- **Frontend**: React.js with Vite, Tailwind CSS, Recharts, Axios, React Router DOM, Lucide React.
- **Backend**: Python 3.10, FastAPI, Pydantic v2, PyMongo, python-jose (JWT), bcrypt.
- **Machine Learning**: Pandas, NumPy, Scikit-learn, XGBoost, Joblib, Matplotlib, Seaborn, Statsmodels.
- **Database**: MongoDB (Local v8.3.7 or MongoDB Atlas connection string).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 3. Project Directory Structure

```
Pharmacy-Forecasting/
├── dataset/
│   ├── raw/
│   │   ├── salesdaily.csv              # Authentic 2,106 daily records (2014-2019)
│   │   ├── salesmonthly.csv
│   │   └── salesweekly.csv
│   ├── processed/
│   │   ├── cleaned_pharma_daily.csv
│   │   ├── engineered_features.csv     # Lags 1,7,14,30 & Rolling means
│   │   ├── medicine_catalogue_mapping.json
│   │   └── eda_plots/                  # High-resolution statistical figures
│   └── README.md
├── ml/
│   ├── notebooks/
│   │   ├── 01_data_exploration.ipynb   # Executed EDA notebook
│   │   ├── 02_data_preprocessing.ipynb # Preprocessing & feature generation
│   │   ├── 03_demand_forecasting.ipynb # Model comparisons & residual checks
│   │   └── 04_expiry_prediction.ipynb   # Expiry classifier & FEFO logic
│   ├── demand_forecasting/
│   │   └── train_models.py             # Chronological training pipeline
│   ├── expiry_prediction/
│   │   ├── risk_engine.py              # Deterministic velocity engine
│   │   └── train_classifier.py         # Multi-class expiry classifier
│   └── saved_models/                   # Serialized Joblib model artifacts
├── backend/
│   ├── app/
│   │   ├── database/
│   │   │   ├── connection.py           # MongoDB connection & index manager
│   │   │   └── seed_data.py            # Initial seed: medicines, batches, users
│   │   ├── ml_engine/
│   │   │   └── forecaster.py           # Real inference loading Joblib models
│   │   ├── routes/                     # Modular API routers
│   │   │   ├── auth.py, medicines.py, batches.py, sales.py,
│   │   │   ├── forecasts.py, expiry.py, inventory.py, reports.py
│   │   └── main.py                     # FastAPI entrypoint & CORS
│   ├── tests/
│   │   └── test_api_endpoints.py       # Automated unit & integration tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/                 # Sidebar, Header, MetricCard
│   │   ├── pages/                      # 8 enterprise pages
│   │   ├── context/                    # AuthContext (JWT)
│   │   └── App.jsx
│   └── package.json
├── docs/
│   └── TECHNICAL_REPORT.md             # Comprehensive technical engineering report
├── docker-compose.yml
├── Dockerfile.backend
└── Dockerfile.frontend
```

---

## 4. Quick Start & Execution Guide

### Step 1: Environment Setup
Ensure Python 3.10+ and Node.js v18+ are installed.

```powershell
# Activate Python Virtual Environment
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 2: Configure Environment
Copy `.env.example` to `.env`:
```powershell
Copy-Item backend\.env.example backend\.env
```
Default configuration connects to local MongoDB on `mongodb://localhost:27017` with database `pharmacy_forecasting`. Alternatively, update `MONGODB_URL` with your MongoDB Atlas URI.

### Step 3: Seed Database
Populate the database with the default admin user, medicine catalog, and representative inventory batches:
```powershell
python -m backend.app.database.seed_data
```
- **Default Pharmacist Credentials**:
  - Email: `admin@pharmacy.com`
  - Password: `admin123`

### Step 4: Run Applications

**Start Backend API (Port 8000)**:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Endpoint: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

**Start Frontend Application (Port 5173)**:
```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```
- Open browser at: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 5. Machine Learning Pipeline Reproduction

### Run Demand Forecasting Training:
```powershell
python ml\demand_forecasting\train_models.py
```
This script:
1. Loads 2,076 feature records from `dataset/processed/engineered_features.csv`.
2. Applies a strict chronological split:
   - **Train**: 2014-02-01 to 2018-12-31 (1,795 days)
   - **Held-Out Test**: 2019-01-01 to 2019-10-08 (281 days)
3. Evaluates 4 candidate models against MAE, RMSE, and WAPE.
4. Serializes the best models to `ml/saved_models/`.

### Run Expiry Risk Classifier Training:
```powershell
python ml\expiry_prediction\train_classifier.py
```
Trains Decision Tree, Random Forest, and XGBoost classifiers with a high-risk recall focus ($84.85\%$).

---

## 6. Running Automated Tests

Run the full pytest suite:
```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_api_endpoints.py -v
```
**Test Results: 8/8 Passed (100%)**:
- `test_health_check` PASSED
- `test_database_health` PASSED
- `test_list_medicines` PASSED
- `test_list_batches` PASSED
- `test_expiry_alerts_and_summary` PASSED
- `test_inventory_recommendations` PASSED
- `test_real_ml_demand_forecast` PASSED (validates live Joblib model inference)
- `test_fefo_sale_and_inventory_decrement` PASSED (validates automated FEFO stock decrement)

---

## 7. Docker Deployment

Deploy the entire full-stack cluster (MongoDB + FastAPI + React Nginx) using Docker Compose:
```powershell
docker-compose up --build -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- MongoDB: `localhost:27017`
