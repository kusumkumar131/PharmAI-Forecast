import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

def calculate_wape(y_true, y_pred):
    """Weighted Absolute Percentage Error (WAPE). Robust against zero actuals."""
    total_actual = np.sum(y_true)
    if total_actual == 0:
        return 0.0
    return float(np.sum(np.abs(y_true - y_pred)) / total_actual * 100)

def train_and_evaluate():
    print("=" * 70)
    print("PHARMACEUTICAL DEMAND FORECASTING: MODEL TRAINING & BENCHMARKING")
    print("=" * 70)

    features_path = os.path.join("dataset", "processed", "engineered_features.csv")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Engineered features not found at {features_path}. Run preprocessing first.")

    df = pd.read_csv(features_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    atc_categories = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']
    
    # Chronological Train-Test Split (strictly avoiding future leakage)
    # Train: 2014-02 to 2018-12-31 (~80%)
    # Test:  2019-01-01 to 2019-10-08 (~20%)
    split_date = pd.to_datetime("2019-01-01")
    train_df = df[df.index < split_date]
    test_df = df[df.index >= split_date]

    print(f"Total samples: {len(df)}")
    print(f"Train period : {train_df.index.min().date()} to {train_df.index.max().date()} ({len(train_df)} days)")
    print(f"Test period  : {test_df.index.min().date()} to {test_df.index.max().date()} ({len(test_df)} days)")

    os.makedirs(os.path.join("ml", "saved_models"), exist_ok=True)
    all_metrics = {}

    for atc in atc_categories:
        print(f"\n--- Training Models for Category: {atc} ---")
        target_col = f"{atc}_target"
        
        # Features for this category
        cat_feature_cols = [
            'day_of_week', 'day_of_month', 'month', 'year', 'quarter', 'is_weekend', 'is_month_end',
            f'{atc}_lag_1', f'{atc}_lag_7', f'{atc}_lag_14', f'{atc}_lag_30',
            f'{atc}_rolling_mean_7', f'{atc}_rolling_mean_14', f'{atc}_rolling_mean_30',
            f'{atc}_rolling_std_7', f'{atc}_rolling_std_30'
        ]

        X_train = train_df[cat_feature_cols]
        y_train = train_df[target_col]
        X_test = test_df[cat_feature_cols]
        y_test = test_df[target_col]

        models = {
            "Baseline_30d_MA": None,
            "Ridge_Regression": Ridge(alpha=1.0, random_state=42),
            "Random_Forest": RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=3, random_state=42, n_jobs=-1),
            "XGBoost": XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
        }

        cat_metrics = {}
        best_model_name = None
        best_wape = float("inf")
        trained_objects = {}

        for name, model in models.items():
            if name == "Baseline_30d_MA":
                # Baseline is the rolling mean of the last 30 days
                preds = test_df[f"{atc}_rolling_mean_30"].values
            else:
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                # Clip negative predictions as sales cannot be negative
                preds = np.clip(preds, a_min=0, a_max=None)
                trained_objects[name] = model

            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(root_mean_squared_error(y_test, preds))
            wape = calculate_wape(y_test.values, preds)

            cat_metrics[name] = {
                "MAE": round(mae, 3),
                "RMSE": round(rmse, 3),
                "WAPE_percent": round(wape, 2)
            }
            print(f"  {name:18} -> MAE: {mae:6.3f} | RMSE: {rmse:6.3f} | WAPE: {wape:6.2f}%")

            if wape < best_wape:
                best_wape = wape
                best_model_name = name

        print(f"  --> Best Model: {best_model_name} (WAPE: {best_wape:.2f}%)")
        cat_metrics["best_model"] = best_model_name
        cat_metrics["feature_names"] = cat_feature_cols

        # Save the best model
        if best_model_name in trained_objects:
            model_file = os.path.join("ml", "saved_models", f"demand_{atc}_{best_model_name.lower()}.joblib")
            joblib.dump({
                "model": trained_objects[best_model_name],
                "model_name": best_model_name,
                "category": atc,
                "feature_names": cat_feature_cols,
                "metrics": cat_metrics[best_model_name]
            }, model_file)
            print(f"  Saved best model to {model_file}")

        # Also save XGBoost by default as the primary ML engine
        if "XGBoost" in trained_objects:
            xgb_file = os.path.join("ml", "saved_models", f"demand_{atc}_xgboost.joblib")
            joblib.dump({
                "model": trained_objects["XGBoost"],
                "model_name": "XGBoost",
                "category": atc,
                "feature_names": cat_feature_cols,
                "metrics": cat_metrics["XGBoost"]
            }, xgb_file)

        all_metrics[atc] = cat_metrics

    # Save complete benchmark metrics to JSON
    metrics_path = os.path.join("ml", "saved_models", "model_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    print("\n" + "=" * 70)
    print(f"All models trained, evaluated, and saved successfully!")
    print(f"Benchmark summary written to: {metrics_path}")
    print("=" * 70)
    return all_metrics

if __name__ == "__main__":
    train_and_evaluate()
