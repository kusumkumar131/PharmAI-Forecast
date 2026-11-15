import json
import os

def create_forecasting_notebook():
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Machine Learning Demand Forecasting: Model Development & Evaluation\n",
                    "## Algions AI Labs Assessment: Pharmacy Medicine Demand & Expiry-Risk\n",
                    "\n",
                    "### 1. Problem Formulation & Split Strategy\n",
                    "- **Prediction Target**: Daily unit sales $y_t$ for each therapeutic drug category.\n",
                    "- **Forecast Horizons**: 7 days (weekly replenishment), 30 days (monthly cycle), 90 days (quarterly procurement).\n",
                    "- **Split Strategy**: Strict **chronological split**:\n",
                    "  - Train Set: 2014-02-01 to 2018-12-31 (1,795 days, ~86%)\n",
                    "  - Held-out Test Set: 2019-01-01 to 2019-10-08 (281 days, ~14%)\n",
                    "  - Strictly zero shuffling to prevent future-looking target leakage.\n",
                    "- **Evaluation Metrics**:\n",
                    "  - **MAE** (Mean Absolute Error): Average unit deviation.\n",
                    "  - **RMSE** (Root Mean Squared Error): Penalizes larger forecasting errors.\n",
                    "  - **WAPE** (Weighted Absolute Percentage Error): $\\frac{\\sum |y_i - \\hat{y}_i|}{\\sum y_i} \\times 100\\%$, indispensable for zero-sales intervals where MAPE is mathematically undefined.\n"
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
                    "\n",
                    "plt.style.use('seaborn-v0_8-whitegrid')\n",
                    "plt.rcParams['figure.figsize'] = (12, 6)\n",
                    "\n",
                    "# Load model metrics from training run\n",
                    "with open('../saved_models/model_metrics.json', 'r') as f:\n",
                    "    metrics = json.load(f)\n",
                    "\n",
                    "# Display metrics across all categories\n",
                    "rows = []\n",
                    "for cat, data in metrics.items():\n",
                    "    best = data.get('best_model')\n",
                    "    for m_name in ['Baseline_30d_MA', 'Ridge_Regression', 'Random_Forest', 'XGBoost']:\n",
                    "        m_data = data[m_name]\n",
                    "        rows.append({\n",
                    "            'Category': cat,\n",
                    "            'Model': m_name,\n",
                    "            'MAE': m_data['MAE'],\n",
                    "            'RMSE': m_data['RMSE'],\n",
                    "            'WAPE (%)': m_data['WAPE_percent'],\n",
                    "            'Is Best': '★' if m_name == best else ''\n",
                    "        })\n",
                    "metrics_df = pd.DataFrame(rows)\n",
                    "metrics_df.head(12)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 2. Model Performance Comparison Across Categories\n",
                    "Comparing WAPE error reduction between the simple 30-day Moving Average baseline and the trained machine learning models.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "pivot_wape = metrics_df.pivot(index='Category', columns='Model', values='WAPE (%)')\n",
                    "plt.figure(figsize=(12, 6))\n",
                    "pivot_wape.plot(kind='bar', figsize=(12, 6), colormap='viridis', width=0.8)\n",
                    "plt.title('Test Set WAPE (%) Comparison Across Models and Drug Categories', fontsize=13, fontweight='bold')\n",
                    "plt.ylabel('WAPE (%) [Lower is Better]', fontsize=11)\n",
                    "plt.xlabel('ATC Category', fontsize=11)\n",
                    "plt.xticks(rotation=0)\n",
                    "plt.legend(frameon=True)\n",
                    "plt.tight_layout()\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 3. Actual vs Predicted Demand on Held-Out 2019 Test Set\n",
                    "Inspecting the high-volume category `N02BE` (Anilides / Paracetamol) across the 281-day held-out test evaluation window.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import joblib\n",
                    "\n",
                    "# Load engineered features\n",
                    "df = pd.read_csv('../../dataset/processed/engineered_features.csv', index_col=0)\n",
                    "df.index = pd.to_datetime(df.index)\n",
                    "test_df = df[df.index >= '2019-01-01'].copy()\n",
                    "\n",
                    "# Load trained model for N02BE\n",
                    "model_obj = joblib.load('../saved_models/demand_N02BE_random_forest.joblib')\n",
                    "model = model_obj['model']\n",
                    "features = model_obj['feature_names']\n",
                    "\n",
                    "X_test = test_df[features]\n",
                    "test_df['predicted_sales'] = np.clip(model.predict(X_test), 0, None)\n",
                    "\n",
                    "plt.figure(figsize=(14, 6))\n",
                    "plt.plot(test_df.index, test_df['N02BE_target'], label='Actual Sales (2019 Held-Out Test)', color='#0284c7', alpha=0.6, linewidth=1.2)\n",
                    "plt.plot(test_df.index, test_df['predicted_sales'], label='Random Forest Predictions', color='#dc2626', linewidth=1.5)\n",
                    "plt.plot(test_df.index, test_df['N02BE_rolling_mean_30'], label='30d Moving Average Baseline', color='#64748b', linestyle='--', linewidth=1.2)\n",
                    "plt.title('Paracetamol (N02BE) Actual vs Predicted Demand on 2019 Held-out Test Data', fontsize=14, fontweight='bold')\n",
                    "plt.ylabel('Daily Units Sold', fontsize=11)\n",
                    "plt.legend(frameon=True)\n",
                    "plt.tight_layout()\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 4. Residual and Error Analysis\n",
                    "Analysis of prediction residuals $(y - \\hat{y})$ to confirm lack of systemic bias and verify normal distribution of errors.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {},
                "outputs": [],
                "source": [
                    "residuals = test_df['N02BE_target'] - test_df['predicted_sales']\n",
                    "fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))\n",
                    "\n",
                    "sns.histplot(residuals, kde=True, ax=ax1, color='#0d9488')\n",
                    "ax1.set_title('Residuals Distribution (Actual - Predicted)', fontsize=12, fontweight='bold')\n",
                    "ax1.set_xlabel('Residual Error (Units)')\n",
                    "\n",
                    "ax2.scatter(test_df['predicted_sales'], residuals, alpha=0.5, color='#0369a1')\n",
                    "ax2.axhline(0, color='red', linestyle='--')\n",
                    "ax2.set_title('Residuals vs Fitted Predicted Values', fontsize=12, fontweight='bold')\n",
                    "ax2.set_xlabel('Predicted Sales Units')\n",
                    "ax2.set_ylabel('Residual')\n",
                    "\n",
                    "plt.tight_layout()\n",
                    "plt.show()\n",
                    "print(f'Mean Residual: {residuals.mean():.3f} (Near zero indicates unbiased prediction)')\n",
                    "print(f'Std Deviation of Residuals: {residuals.std():.3f}')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 5. Decision-Support Advisory Declaration\n",
                    "> **IMPORTANT**: This forecasting model is an **operational decision-support tool** designed to assist inventory managers with procurement orders and safety stock planning. Forecasts reflect statistical trends and historical sales patterns; they do **not** constitute medical advice, prescribing guidance, or clinical treatment recommendations."
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

    with open("ml/notebooks/03_demand_forecasting.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)
    print("Created ml/notebooks/03_demand_forecasting.ipynb")

if __name__ == "__main__":
    create_forecasting_notebook()
