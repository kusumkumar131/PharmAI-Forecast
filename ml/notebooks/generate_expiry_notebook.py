import json
import os

def create_expiry_notebook():
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Medicine Batch Expiry-Risk Prediction & FEFO Prioritization\n",
                    "## Algions AI Labs Assessment: Decision-Support Optimization\n",
                    "\n",
                    "### 1. Problem Formulation & Business Risk Engine\n",
                    "Pharmaceutical inventory carries significant financial and clinical risk:\n",
                    "- Expired stock causes direct fiscal write-offs.\n",
                    "- Dispensing expired medication poses serious patient safety hazards and regulatory penalties.\n",
                    "\n",
                    "We formulate a dual-layered strategy:\n",
                    "1. **Deterministic Inventory Velocity Engine**: Calculates remaining days $T_{exp} - T_{today}$, historical sales velocity, expected sales before expiry, estimated unsold quantity, and dollar inventory value-at-risk.\n",
                    "2. **Machine Learning Classifier**: Multi-class classifier (Low Risk, Medium Risk, High Risk) trained on batch attributes (quantity, velocity, variability, shelf-life).\n",
                    "\n",
                    "$$\\text{Expected Demand Before Expiry} = \\text{Average Daily Demand} \\times \\text{Days Remaining}$$\n",
                    "$$\\text{Estimated Unsold Quantity} = \\max(0, \\text{Remaining Quantity} - \\text{Expected Demand})$$\n",
                    "$$\\text{Inventory Value at Risk} = \\text{Estimated Unsold Quantity} \\times \\text{Purchase Price}$$\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "import json\n",
                    "import joblib\n",
                    "\n",
                    "plt.style.use('seaborn-v0_8-whitegrid')\n",
                    "plt.rcParams['figure.figsize'] = (10, 5)\n",
                    "\n",
                    "# Load classification metrics\n",
                    "with open('../saved_models/expiry_metrics.json', 'r') as f:\n",
                    "    metrics = json.load(f)\n",
                    "\n",
                    "df_results = pd.DataFrame(metrics).T\n",
                    "df_results[['accuracy', 'precision', 'recall', 'f1_score', 'high_risk_recall']]"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 2. Confusion Matrix & High-Risk Batch Recall\n",
                    "In medicine stock control, **High-Risk Batch Recall** is of paramount importance: missing an expiring batch leads to product wastage or illegal dispensing.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "labels = ['Low Risk', 'Medium Risk', 'High Risk']\n",
                    "cm = np.array(metrics['XGBoost']['confusion_matrix'])\n",
                    "\n",
                    "plt.figure(figsize=(7, 5))\n",
                    "sns.heatmap(cm, annot=True, fmt='d', cmap='Reds', xticklabels=labels, yticklabels=labels)\n",
                    "plt.title('XGBoost Batch Expiry Risk: Confusion Matrix', fontsize=13, fontweight='bold')\n",
                    "plt.xlabel('Predicted Operational Category', fontsize=11)\n",
                    "plt.ylabel('Actual Depletion Outcome', fontsize=11)\n",
                    "plt.tight_layout()\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 3. First-Expiry, First-Out (FEFO) Recommendation Logic\n",
                    "Demonstrating batch allocation order when dispensing medication. Expiring lots are liquidated first before opening newer long-dated stock.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from datetime import datetime, timedelta\n",
                    "import sys\n",
                    "sys.path.append('../..')\n",
                    "from ml.expiry_prediction.risk_engine import ExpiryRiskEngine\n",
                    "\n",
                    "today = datetime(2026, 11, 15)\n",
                    "batches = [\n",
                    "    {'batch': 'BN-26-8801', 'qty': 65, 'exp': '2026-12-07', 'price': 12.5, 'vel': 2.5},\n",
                    "    {'batch': 'BN-26-8802', 'qty': 120, 'exp': '2027-01-09', 'price': 12.5, 'vel': 2.5},\n",
                    "    {'batch': 'BN-26-9901', 'qty': 200, 'exp': '2028-01-11', 'price': 12.5, 'vel': 2.5}\n",
                    "]\n",
                    "\n",
                    "eval_records = []\n",
                    "for b in batches:\n",
                    "    res = ExpiryRiskEngine.calculate_batch_risk(\n",
                    "        quantity_remaining=b['qty'],\n",
                    "        purchase_price=b['price'],\n",
                    "        expiry_date_str=b['exp'],\n",
                    "        average_daily_sales=b['vel'],\n",
                    "        reference_date=today\n",
                    "    )\n",
                    "    res['batch_number'] = b['batch']\n",
                    "    eval_records.append(res)\n",
                    "\n",
                    "df_fefo = pd.DataFrame(eval_records)\n",
                    "df_fefo[['batch_number', 'days_until_expiry', 'risk_level', 'estimated_unsold_quantity', 'inventory_value_at_risk', 'recommended_action']]"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 4. Decision-Support & Clinical Advisory Statement\n",
                    "> **ADVISORY NOTICE**: The batch risk predictions, suggested stock rotation order, and FEFO alerts generated by this platform are exclusively **operational decision-support guidance** for inventory management. Under no circumstances should these predictions be construed as clinical diagnosis, medical advice, or therapeutic recommendations."
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python"},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open("ml/notebooks/04_expiry_prediction.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)
    print("Created ml/notebooks/04_expiry_prediction.ipynb")

if __name__ == "__main__":
    create_expiry_notebook()
