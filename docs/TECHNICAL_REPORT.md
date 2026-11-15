# ALGIONS AI LABS PRIVATE LIMITED
## Advanced Individual Project Assessment: Technical Report
### Pharmacy Medicine Demand & Expiry-Risk Forecasting

---

## Candidate & Assessment Profile
- **Assigned Project**: Pharmacy Medicine Demand & Expiry-Risk Forecasting
- **Internship Role**: AI & Machine Learning
- **Assessment Scope**: Decision-support ML solution with reproducible data preparation, defensible evaluation, and working inference interface.

---

## 1. Executive Summary & Problem Framing

### 1.1 Business Context
Retail and hospital pharmacies navigate a persistent double-bind:
1. **Overstocking**: Accumulating excess medicine batches leads to inventory holding costs and expiry write-offs (expired stock cannot legally be dispensed).
2. **Understocking**: Stockouts of critical analgesics, antibiotics, or respiratory inhalers cause lost revenue and compromise patient care continuity.

### 1.2 Decision-Support Framing & Unit of Prediction
- **System Nature**: Operational decision-support platform designed to assist pharmacy supply officers and pharmacists in procurement and batch rotation. It provides **operational guidance, never medical treatment advice**.
- **Prediction Units**:
  - *Demand Forecasting Target*: Daily units dispensed $y_t$ across 8 World Health Organization (WHO) Anatomical Therapeutic Chemical (ATC) therapeutic groups and mapped clinical medicine formulations.
  - *Forecasting Horizons*: **7 Days** (Weekly restock), **30 Days** (Monthly replenishment cycle), and **90 Days** (Quarterly procurement).
  - *Expiry-Risk Target*: Estimated unsold units at expiry date $T_{exp}$, monetary Inventory Value-at-Risk ($), and operational risk classification (**High Risk**, **Medium Risk**, **Low Risk**, **Expired**).
- **Point in Time of Prediction**: Predictions are generated daily based strictly on historical observations $t \le T_{now}$.

---

## 2. Dataset Sourcing, Attribution & Quality Assurance

### 2.1 Provenance & Licensing
- **Primary Sales Dataset**: Authentic Pharma Sales Data ([Kaggle Dataset](https://www.kaggle.com/datasets/milanzdravkovic/pharma-sales-data) / [GitHub Repository](https://github.com/mcallara/pharma-sales-data)).
- **Timeframe**: January 2, 2014 to October 8, 2019 (2,106 continuous daily records).
- **Structure**: Continuous daily transactions across 8 WHO ATC therapeutic classes.

| ATC Code | Drug Group | Representative Real Medicines | Primary Clinical Indication |
|:---|:---|:---|:---|
| **M01AB** | Acetic acid derivatives (NSAIDs) | Diclofenac Sodium 50mg | Rheumatoid arthritis, osteoarthritis, acute pain |
| **M01AE** | Propionic acid derivatives (NSAIDs) | Ibuprofen 400mg | Musculoskeletal pain, dysmenorrhea, fever |
| **N02BA** | Salicylic acid derivatives | Aspirin Cardio 75mg | Mild analgesia, antiplatelet cardioprotection |
| **N02BE** | Anilides | Paracetamol (Acetaminophen) 500mg | First-line antipyretic & general analgesic |
| **N05B** | Anxiolytics (Psycholeptics) | Diazepam 5mg | Anxiety disorders, acute muscle spasm |
| **N05C** | Hypnotics & Sedatives | Zolpidem 10mg | Short-term management of severe insomnia |
| **R03** | Obstructive airway diseases | Salbutamol Inhaler 100mcg | Bronchospasm, bronchial asthma, COPD |
| **R06** | Antihistamines for systemic use | Cetirizine 10mg | Allergic rhinitis, urticaria, allergy relief |

### 2.2 Data Integrity & Zero-Sales Sparsity
Statistical inspection confirms:
- **Completeness**: 0 missing values across all 2,106 daily records.
- **Data Types**: Float64 sales volumes, DateTime index.
- **Zero-Sales Analysis**:
  - `N02BE` (Paracetamol): Only 26 zero days (1.23%) — high-volume chronic consumption.
  - `M01AB` (Diclofenac): 40 zero days (1.90%), mean 5.03 units/day.
  - `R03` (Respiratory): 484 zero days (22.98%), intermittent episodic demand.
  - `N05C` (Hypnotics): 1,430 zero days (67.90%), highly sparse intermittent sales.

> **Metric Selection Justification**: Because intermittent medicines contain frequent zero-sales days, traditional **MAPE (Mean Absolute Percentage Error)** divides by zero ($y_t = 0$) and explodes. Hence, **WAPE (Weighted Absolute Percentage Error)**, **MAE**, and **RMSE** are utilized as the standard mathematical evaluation metrics:
> $$\text{WAPE} = \frac{\sum_{i=1}^n |y_i - \hat{y}_i|}{\sum_{i=1}^n y_i} \times 100\%$$

---

## 3. Leakage-Safe Chronological Split & Feature Engineering

### 3.1 Chronological Split Strategy
To prevent target leakage and simulate real deployment:
- **Training Set**: 2014-02-01 to 2018-12-31 (1,795 continuous days, ~86% of data).
- **Held-Out Test Set**: 2019-01-01 to 2019-10-08 (281 continuous days, ~14% of data).
- **Strict Rule**: Shuffling is completely prohibited. Test data was never seen during model training or parameter selection.

### 3.2 Feature Engineering Pipeline
For each therapeutic category, temporal and autoregressive features were extracted:
1. **Calendar Features**: Day of week (0–6), Day of month (1–31), Month (1–12), Year, Quarter, Weekend Indicator, Month-end flag.
2. **Autoregressive Lags**:
   - `lag_1`: Short-term sales momentum.
   - `lag_7`: Weekly seasonality cycle (same day of previous week).
   - `lag_14`: Bi-weekly refill cycle.
   - `lag_30`: Monthly prior baseline.
3. **Rolling Window Features** (shifted by 1 day to strictly eliminate target leakage):
   - `rolling_mean_7`: 7-day smoothed demand velocity.
   - `rolling_mean_14`: 14-day smoothed demand velocity.
   - `rolling_mean_30`: 30-day baseline moving average.
   - `rolling_std_7` & `rolling_std_30`: Local demand volatility and dispersion.

---

## 4. Model Development & Test Benchmark Comparison

We evaluated 4 distinct models across all 8 therapeutic categories on the **held-out 2019 test set (281 days)**:
1. **Baseline**: 30-day Historical Moving Average.
2. **Linear / Ridge Regression**: Regularized linear autoregression.
3. **Random Forest Regressor**: 100 estimators, max depth 8, non-linear ensemble.
4. **XGBoost Regressor**: Gradient-boosted decision trees (learning rate 0.05, max depth 5).

### 4.1 Test Benchmark Results Table (Held-Out 2019 Test Set)

| ATC Category | Model | Test MAE | Test RMSE | Test WAPE (%) | Status / Outcome |
|:---|:---|:---:|:---:|:---:|:---|
| **N02BE** (Paracetamol) | Baseline 30d MA | 9.836 | 13.432 | 34.62% | Benchmark |
| | Ridge Regression | 8.783 | 11.766 | 30.92% | Strong |
| | **Random Forest** | **8.732** | **11.698** | **30.74%** | **Best Performer (★)** |
| | XGBoost | 8.907 | 12.199 | 31.36% | High accuracy |
| **M01AB** (Diclofenac) | Baseline 30d MA | 2.248 | 2.899 | 41.64% | Benchmark |
| | **Ridge Regression** | **2.210** | **2.844** | **40.93%** | **Best Performer (★)** |
| | Random Forest | 2.242 | 2.895 | 41.52% | Close second |
| | XGBoost | 2.274 | 2.891 | 42.11% | Consistent |
| **M01AE** (Ibuprofen) | Baseline 30d MA | 1.761 | 2.300 | 45.64% | Benchmark |
| | **Ridge Regression** | **1.652** | **2.168** | **42.80%** | **Best Performer (★)** |
| | Random Forest | 1.722 | 2.230 | 44.61% | Solid |
| | XGBoost | 1.736 | 2.240 | 44.98% | Solid |
| **N05C** (Zolpidem) | Baseline 30d MA | 0.877 | 1.126 | 125.78% | Benchmark |
| | Ridge Regression | 0.858 | 1.113 | 123.00% | High error on zeros |
| | Random Forest | 0.819 | 1.113 | 117.35% | Tree splits handle zeros |
| | **XGBoost** | **0.812** | **1.114** | **116.44%** | **Best Performer (★)** |
| **R06** (Cetirizine) | Baseline 30d MA | 1.834 | 2.409 | 48.00% | Benchmark |
| | Ridge Regression | 1.772 | 2.350 | 46.38% | Strong |
| | **Random Forest** | **1.767** | **2.348** | **46.25%** | **Best Performer (★)** |
| | XGBoost | 1.797 | 2.365 | 47.02% | Close |

### 4.2 Key Forecasting Insights
- Machine learning models beat the moving average baseline across **100% of the categories**.
- For high-volume medicines (`N02BE`), tree ensembles reduced WAPE from 34.62% down to 30.74%.
- For highly intermittent, zero-dense hypnotics (`N05C`), gradient boosting (XGBoost) demonstrated superior performance by learning discrete non-linear threshold triggers.

---

## 5. Batch Expiry-Risk Prediction & Classification

### 5.1 Velocity & Inventory Risk Mechanics
The inventory risk engine computes batch depletion before the manufacturer's expiration date:
$$\text{Days Remaining} = \max(0, T_{exp} - T_{today})$$
$$\text{Expected Demand Before Expiry} = \text{Average Daily Sales} \times \text{Days Remaining}$$
$$\text{Estimated Unsold Quantity} = \max(0, Q_{remaining} - \text{Expected Demand})$$
$$\text{Inventory Value at Risk} = \text{Estimated Unsold Quantity} \times \text{Purchase Price}$$

### 5.2 Classifier Architecture & Evaluation
A multi-class classifier was developed to flag batches requiring urgent intervention:
- **Features**: Category, Current Batch Quantity, Average Daily Sales, Days Remaining, Demand Trend (7d vs 30d), Sales Variability.
- **Labels**: Low Risk, Medium Risk, High Risk.

#### Classification Benchmark on Test Set (1,000 Batches):
| Classifier | Accuracy | Precision (Weighted) | Recall (Weighted) | F1-Score | High-Risk Recall |
|:---|:---:|:---:|:---:|:---:|:---:|
| Decision Tree | 97.50% | 0.9716 | 0.9750 | 0.9722 | 75.76% |
| Random Forest | 96.70% | 0.9625 | 0.9670 | 0.9624 | 48.48% |
| **XGBoost Classifier** | **98.60%** | **0.9849** | **0.9860** | **0.9848** | **84.85%** |

> **Operational Impact**: High-risk batch recall (84.85%) is prioritized: in medicine management, false negatives (failing to identify an expiring batch) lead to hazardous stock or complete financial write-offs.

---

## 6. Supply Chain Restocking & FEFO Inventory Optimization

### 6.1 Reorder Recommendation Engine
The replenishment module calculates optimal reorder quantities using:
$$Q_{\text{reorder}} = \max\Big(0, (D_{\text{lead}} + SS) - S_{\text{usable}} - PO_{\text{incoming}}\Big)$$
Where:
- $D_{\text{lead}} = \text{Predicted Daily Demand} \times \text{Supplier Lead Time (Days)}$.
- $SS = \text{Safety Stock}$ (buffer for unexpected demand surges).
- $S_{\text{usable}} = \text{Available Usable Stock}$ (strictly excludes expired batches).
- $PO_{\text{incoming}} = \text{Pending Purchase Orders}$.

### 6.2 First-Expiry, First-Out (FEFO) Protocol
When dispensing medicines at Point of Sale:
1. Batches are sorted in ascending order of expiration date ($\min T_{exp}$).
2. The system checks $T_{exp} > T_{today}$ (expired stock is locked from sale).
3. Units are deducted atomically from the earliest expiring batch before touching newer lots.

---

## 7. System Architecture & API Endpoints

```
React (Vite + Tailwind CSS + Recharts)
           │
           │ REST API (JSON)
           ▼
FastAPI Backend (Port 8000)
    ├── /api/auth          (JWT Authentication & RBAC)
    ├── /api/medicines     (Master Catalogue CRUD)
    ├── /api/batches       (Batch Lifecycle & Expiry Badges)
    ├── /api/sales         (FEFO Dispensing & Atomic Stock Decrement)
    ├── /api/forecasts     (Live ML Inference from Joblib Artifacts)
    ├── /api/expiry        (Value at Risk & FEFO Guidance)
    ├── /api/inventory     (Summary & Restocking Recommendations)
    └── /api/reports       (Audit & Valuation Statements)
           │
     ┌─────┴──────────────┐
     ▼                    ▼
MongoDB Atlas / Local    ML Engine
(7 Indexed Collections)  (Joblib Models & Metrics)
```

---

## 8. Responsible AI, Bias & Failure Modes

1. **Human-in-the-Loop Oversight**: Restocking suggestions and expiry alerts are **decision-support prompts**. Purchase orders and batch quarantines must always be confirmed by a licensed pharmacist.
2. **Clinical Non-Interference**: Demand spikes caused by disease outbreaks or policy changes may exceed statistical lag models; pharmacists are instructed to review external epidemiological signals.
3. **Data Privacy**: No patient medical records (PHI/PII) or prescription IDs are ingested or stored in the forecasting models.

---

## 9. Verification & Acceptance Demonstration

### Test 1: Unit & Integration Tests (100% Pass)
```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_api_endpoints.py -v
```
All 8 integration tests verify:
- API and MongoDB connectivity.
- Live model loading and non-hardcoded forecast generation.
- Atomic inventory decrements under FEFO logic.

### Test 2: Training Pipeline Reproduction
```powershell
.\.venv\Scripts\python.exe ml\demand_forecasting\train_models.py
.\.venv\Scripts\python.exe ml\expiry_prediction\train_classifier.py
```

### Test 3: Live Application Access
- **Frontend Dashboard**: `http://127.0.0.1:5173`
- **FastAPI OpenAPI Interactive Docs**: `http://127.0.0.1:8000/docs`
- **Default Pharmacist Credentials**: `admin@pharmacy.com` / `admin123`
