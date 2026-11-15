import os
import glob
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

class MLForecaster:
    _models = {}
    _metrics = None
    _features_df = None

    @classmethod
    def load_artifacts(cls):
        """Loads trained model artifacts and benchmark metrics."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_models_dir = os.path.join(current_dir, "saved_models")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        root_models_dir = os.path.join(base_dir, "ml", "saved_models")
        
        models_dir = local_models_dir if os.path.exists(local_models_dir) else root_models_dir
        
        # Load metrics
        metrics_file = os.path.join(models_dir, "model_metrics.json")
        if os.path.exists(metrics_file):
            with open(metrics_file, "r", encoding="utf-8") as f:
                cls._metrics = json.load(f)

        # Load models
        model_files = glob.glob(os.path.join(models_dir, "demand_*.joblib"))
        for mf in model_files:
            try:
                data = joblib.load(mf)
                cat = data.get("category")
                m_name = data.get("model_name", "model").lower()
                key = f"{cat}_{m_name}"
                cls._models[key] = data
            except Exception as e:
                print(f"Error loading model {mf}: {e}")

        # Load feature baseline
        local_feat_path = os.path.join(current_dir, "data", "engineered_features.csv")
        root_feat_path = os.path.join(base_dir, "dataset", "processed", "engineered_features.csv")
        feat_path = local_feat_path if os.path.exists(local_feat_path) else root_feat_path
        if os.path.exists(feat_path):
            cls._features_df = pd.read_csv(feat_path, index_col=0)
            cls._features_df.index = pd.to_datetime(cls._features_df.index)

    @classmethod
    def generate_forecast(cls, category: str, horizon_days: int = 30, model_type: str = "best") -> Dict[str, Any]:
        """
        Executes real model inference for a given therapeutic category across the requested horizon.
        Returns daily predicted values, cumulative sum, confidence bounds, and validation metrics.
        """
        if not cls._models:
            cls.load_artifacts()

        cat = category.upper()
        if cat not in cls._metrics:
            cat = "N02BE"  # Fallback to high-volume analgesic if unknown category

        cat_metrics = cls._metrics.get(cat, {})
        best_model_name = cat_metrics.get("best_model", "XGBoost")
        
        chosen_key = f"{cat}_{best_model_name.lower()}"
        if chosen_key not in cls._models:
            # Fallback to any loaded model for this category
            matching = [k for k in cls._models.keys() if k.startswith(f"{cat}_")]
            chosen_key = matching[0] if matching else list(cls._models.keys())[0]

        model_artifact = cls._models[chosen_key]
        model = model_artifact["model"]
        feature_names = model_artifact["feature_names"]
        model_name = model_artifact["model_name"]
        eval_metrics = model_artifact.get("metrics", cat_metrics.get(model_name, {}))

        # Recent baseline feature state
        if cls._features_df is not None and not cls._features_df.empty:
            last_row = cls._features_df.iloc[-1]
            base_lag_1 = float(last_row.get(f"{cat}_target", 15.0))
            base_rm_7 = float(last_row.get(f"{cat}_rolling_mean_7", 15.0))
            base_rm_30 = float(last_row.get(f"{cat}_rolling_mean_30", 15.0))
            base_rstd_7 = float(last_row.get(f"{cat}_rolling_std_7", 3.0))
            base_rstd_30 = float(last_row.get(f"{cat}_rolling_std_30", 4.0))
        else:
            base_lag_1 = 15.0
            base_rm_7 = 15.0
            base_rm_30 = 15.0
            base_rstd_7 = 3.0
            base_rstd_30 = 4.0

        daily_predictions: List[Dict[str, Any]] = []
        start_date = datetime.utcnow()
        current_lags = [base_lag_1] * 30
        running_predictions = []

        for day in range(1, horizon_days + 1):
            curr_date = start_date + timedelta(days=day)
            dow = curr_date.weekday()
            dom = curr_date.day
            month = curr_date.month
            year = curr_date.year
            quarter = (month - 1) // 3 + 1
            is_weekend = 1 if dow in [5, 6] else 0
            is_month_end = 1 if (curr_date + timedelta(days=1)).day == 1 else 0

            # Dynamic lag updates
            l1 = running_predictions[-1] if running_predictions else current_lags[-1]
            l7 = running_predictions[-7] if len(running_predictions) >= 7 else current_lags[-7]
            l14 = running_predictions[-14] if len(running_predictions) >= 14 else current_lags[-14]
            l30 = running_predictions[-30] if len(running_predictions) >= 30 else current_lags[-30]

            all_recent = (current_lags + running_predictions)[-30:]
            rm_7 = float(np.mean(all_recent[-7:]))
            rm_14 = float(np.mean(all_recent[-14:]))
            rm_30 = float(np.mean(all_recent))
            rstd_7 = float(np.std(all_recent[-7:])) if len(all_recent[-7:]) > 1 else base_rstd_7
            rstd_30 = float(np.std(all_recent)) if len(all_recent) > 1 else base_rstd_30

            feat_vector = {
                'day_of_week': dow,
                'day_of_month': dom,
                'month': month,
                'year': year,
                'quarter': quarter,
                'is_weekend': is_weekend,
                'is_month_end': is_month_end,
                f'{cat}_lag_1': l1,
                f'{cat}_lag_7': l7,
                f'{cat}_lag_14': l14,
                f'{cat}_lag_30': l30,
                f'{cat}_rolling_mean_7': rm_7,
                f'{cat}_rolling_mean_14': rm_14,
                f'{cat}_rolling_mean_30': rm_30,
                f'{cat}_rolling_std_7': rstd_7,
                f'{cat}_rolling_std_30': rstd_30
            }

            input_row = pd.DataFrame([feat_vector])[feature_names]
            raw_pred = float(model.predict(input_row)[0])
            pred_qty = max(0.0, raw_pred)
            running_predictions.append(pred_qty)

            # Confidence interval estimated from model RMSE
            rmse_band = eval_metrics.get("RMSE", 2.5)
            upper_bound = max(0.0, pred_qty + 1.96 * (rmse_band * 0.7))
            lower_bound = max(0.0, pred_qty - 1.96 * (rmse_band * 0.7))

            daily_predictions.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "day_name": curr_date.strftime("%A"),
                "predicted_quantity": round(pred_qty, 1),
                "lower_bound": round(lower_bound, 1),
                "upper_bound": round(upper_bound, 1)
            })

        total_predicted = sum(p["predicted_quantity"] for p in daily_predictions)
        avg_daily = total_predicted / horizon_days

        return {
            "category": cat,
            "horizon_days": horizon_days,
            "model_used": model_name,
            "model_metrics": eval_metrics,
            "total_predicted_units": round(total_predicted, 1),
            "average_daily_demand": round(avg_daily, 2),
            "daily_forecast": daily_predictions,
            "generated_at": datetime.utcnow().isoformat(),
            "advisory_disclaimer": "Decision-support forecast for inventory planning only. Not medical or clinical advice."
        }

# Pre-warm artifacts on import
MLForecaster.load_artifacts()
