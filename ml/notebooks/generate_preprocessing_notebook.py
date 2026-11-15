import json
import os

def create_preprocessing_notebook():
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Pharmaceutical Sales Dataset: Preprocessing & Feature Engineering\n",
                    "## Machine Learning Pipeline for Demand Forecasting\n",
                    "\n",
                    "### 1. Preprocessing Objectives\n",
                    "1. Verify chronological continuity (2,106 days from 2014-01-02 to 2019-10-08).\n",
                    "2. Construct lag features: **Lag 1**, **Lag 7**, **Lag 14**, **Lag 30**.\n",
                    "3. Construct rolling window metrics: **Rolling Mean 7d, 14d, 30d**, **Rolling Std 7d, 30d**.\n",
                    "4. Extract calendar seasonality features: **Day of Week**, **Month**, **Year**, **Weekend Indicator**, **Quarter**.\n",
                    "5. Structure time-series dataset ready for chronological train-test splitting (strictly avoiding data leakage).\n"
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
                    "import os\n",
                    "\n",
                    "df = pd.read_csv('../../dataset/raw/salesdaily.csv')\n",
                    "df['datum'] = pd.to_datetime(df['datum'])\n",
                    "df = df.sort_values('datum').reset_index(drop=True)\n",
                    "atc_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']\n",
                    "\n",
                    "# Set date as index\n",
                    "df_ts = df.set_index('datum')\n",
                    "print(f'Continuous time-series loaded: {df_ts.shape[0]} daily records.')\n",
                    "df_ts[atc_cols].head()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 2. Calendar & Temporal Feature Engineering\n",
                    "Capturing periodic customer behavior patterns, weekly refill cycles, and seasonal flu/allergy months.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "features_df = pd.DataFrame(index=df_ts.index)\n",
                    "features_df['day_of_week'] = df_ts.index.dayofweek\n",
                    "features_df['day_of_month'] = df_ts.index.day\n",
                    "features_df['month'] = df_ts.index.month\n",
                    "features_df['year'] = df_ts.index.year\n",
                    "features_df['quarter'] = df_ts.index.quarter\n",
                    "features_df['is_weekend'] = df_ts.index.dayofweek.isin([5, 6]).astype(int)\n",
                    "features_df['is_month_end'] = df_ts.index.is_month_end.astype(int)\n",
                    "features_df.head()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 3. Autoregressive Lags & Rolling Window Features\n",
                    "Constructing multi-horizon predictive features for each therapeutic class:\n",
                    "- `lag_1`: Previous day's demand (short-term momentum)\n",
                    "- `lag_7`: Same day of previous week (captures 7-day cyclicality)\n",
                    "- `lag_14`: Two weeks prior\n",
                    "- `lag_30`: Monthly prior\n",
                    "- `rolling_mean_7`: Weekly smoothed velocity\n",
                    "- `rolling_mean_14`: Bi-weekly velocity\n",
                    "- `rolling_mean_30`: Monthly baseline velocity\n",
                    "- `rolling_std_7` & `rolling_std_30`: Local demand volatility\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "engineered_features = features_df.copy()\n",
                    "\n",
                    "for col in atc_cols:\n",
                    "    series = df_ts[col]\n",
                    "    engineered_features[f'{col}_target'] = series\n",
                    "    # Lags\n",
                    "    engineered_features[f'{col}_lag_1'] = series.shift(1)\n",
                    "    engineered_features[f'{col}_lag_7'] = series.shift(7)\n",
                    "    engineered_features[f'{col}_lag_14'] = series.shift(14)\n",
                    "    engineered_features[f'{col}_lag_30'] = series.shift(30)\n",
                    "    # Rolling features (shift by 1 to prevent target leakage)\n",
                    "    shifted_series = series.shift(1)\n",
                    "    engineered_features[f'{col}_rolling_mean_7'] = shifted_series.rolling(7, min_periods=3).mean()\n",
                    "    engineered_features[f'{col}_rolling_mean_14'] = shifted_series.rolling(14, min_periods=7).mean()\n",
                    "    engineered_features[f'{col}_rolling_mean_30'] = shifted_series.rolling(30, min_periods=14).mean()\n",
                    "    engineered_features[f'{col}_rolling_std_7'] = shifted_series.rolling(7, min_periods=3).std()\n",
                    "    engineered_features[f'{col}_rolling_std_30'] = shifted_series.rolling(30, min_periods=14).std()\n",
                    "\n",
                    "# Drop rows with NaN from initial 30-day lag warm-up\n",
                    "engineered_clean = engineered_features.dropna().copy()\n",
                    "print(f'Final Engineered Feature Set: {engineered_clean.shape[0]} rows, {engineered_clean.shape[1]} columns')\n",
                    "engineered_clean.head()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 4. Data Export and Catalog Mapping\n",
                    "Exporting cleaned datasets to `dataset/processed/` for model training and API services.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {},
                "outputs": [],
                "source": [
                    "os.makedirs('../../dataset/processed', exist_ok=True)\n",
                    "df.to_csv('../../dataset/processed/cleaned_pharma_daily.csv', index=False)\n",
                    "engineered_clean.to_csv('../../dataset/processed/engineered_features.csv')\n",
                    "print('Saved cleaned_pharma_daily.csv and engineered_features.csv successfully!')"
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

    with open("ml/notebooks/02_data_preprocessing.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)
    print("Created ml/notebooks/02_data_preprocessing.ipynb")

if __name__ == "__main__":
    create_preprocessing_notebook()
