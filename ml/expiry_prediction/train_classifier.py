import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, accuracy_score

def generate_reproducible_batch_dataset(n_samples=5000, seed=42):
    """
    Generates a realistic synthetic batch profile dataset based on real ATC demand characteristics.
    Used for training the candidate batch expiry classification models.
    """
    np.random.seed(seed)
    
    categories = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']
    # Category average velocities derived from real Pharma Sales data
    velocity_priors = {
        'M01AB': (5.0, 2.7),
        'M01AE': (3.9, 2.1),
        'N02BA': (3.9, 2.4),
        'N02BE': (29.9, 15.6),
        'N05B': (8.9, 5.6),
        'N05C': (0.6, 1.1),
        'R03': (5.5, 6.4),
        'R06': (2.9, 2.4)
    }

    records = []
    for _ in range(n_samples):
        cat = np.random.choice(categories)
        mean_vel, std_vel = velocity_priors[cat]
        avg_daily_sales = max(0.1, np.random.normal(mean_vel, std_vel))
        
        # Batch size (typically 1 to 4 weeks of supply)
        expected_monthly = avg_daily_sales * 30
        batch_qty = max(10, np.random.exponential(expected_monthly))
        remaining_qty = np.random.uniform(5, batch_qty)
        
        # Days remaining: from 5 to 365 days
        days_remaining = int(np.random.uniform(5, 365))
        
        # Trend ratio: recent 7d velocity vs 30d velocity (0.5 to 1.5)
        demand_trend = np.random.normal(1.0, 0.2)
        sales_variability = max(0.05, np.random.normal(0.3, 0.1))
        
        expected_demand = avg_daily_sales * demand_trend * days_remaining
        unsold_qty = max(0, remaining_qty - expected_demand)
        unsold_ratio = unsold_qty / max(1.0, remaining_qty)
        
        # Ground truth label assignment based on actual batch depletion threshold:
        # High Risk: unsold >= 50% OR (days_remaining <= 30 and unsold > 20%)
        # Medium Risk: 20% <= unsold < 50% OR (30 < days_remaining <= 60 and unsold > 10%)
        # Low Risk: unsold < 20%
        if unsold_ratio >= 0.50 or (days_remaining <= 30 and unsold_ratio > 0.20):
            label = 2  # High Risk
        elif unsold_ratio >= 0.20 or (days_remaining <= 60 and unsold_ratio > 0.10):
            label = 1  # Medium Risk
        else:
            label = 0  # Low Risk

        records.append({
            'category': cat,
            'current_quantity': round(remaining_qty, 1),
            'avg_daily_sales': round(avg_daily_sales, 2),
            'days_remaining': days_remaining,
            'demand_trend': round(demand_trend, 3),
            'sales_variability': round(sales_variability, 3),
            'expected_demand': round(expected_demand, 1),
            'unsold_ratio': round(unsold_ratio, 3),
            'risk_label': label
        })

    df = pd.DataFrame(records)
    return df

def train_expiry_classifier():
    print("=" * 70)
    print("BATCH EXPIRY RISK CLASSIFICATION: TRAINING & EVALUATION")
    print("=" * 70)
    
    df = generate_reproducible_batch_dataset(n_samples=5000, seed=42)
    os.makedirs(os.path.join("dataset", "processed"), exist_ok=True)
    df.to_csv(os.path.join("dataset", "processed", "simulated_batch_outcomes.csv"), index=False)
    print(f"Generated simulated batch outcomes: {len(df)} records.")
    print("Class distribution:")
    label_names = {0: "Low Risk", 1: "Medium Risk", 2: "High Risk"}
    print(df['risk_label'].value_counts().rename(index=label_names))

    # Feature matrix
    # One-hot encode category
    df_encoded = pd.get_dummies(df, columns=['category'], drop_first=False)
    feature_cols = [c for c in df_encoded.columns if c not in ['risk_label', 'unsold_ratio']]
    
    X = df_encoded[feature_cols]
    y = df_encoded['risk_label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    classifiers = {
        "Decision_Tree": DecisionTreeClassifier(max_depth=6, random_state=42),
        "Random_Forest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
    }

    results = {}
    best_f1 = 0
    best_clf_name = None
    best_model = None

    for name, clf in classifiers.items():
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average='weighted'))
        rec = float(recall_score(y_test, y_pred, average='weighted'))
        f1 = float(f1_score(y_test, y_pred, average='weighted'))
        
        # High Risk specific recall (crucial to avoid expired wastage)
        high_risk_recall = float(recall_score(y_test, y_pred, labels=[2], average='macro'))
        cm = confusion_matrix(y_test, y_pred).tolist()

        results[name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "high_risk_recall": round(high_risk_recall, 4),
            "confusion_matrix": cm
        }

        print(f"\n{name:15} -> Accuracy: {acc:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | High-Risk Recall: {high_risk_recall:.4f}")

        if f1 > best_f1:
            best_f1 = f1
            best_clf_name = name
            best_model = clf

    print(f"\n--> Best Expiry Classifier: {best_clf_name} (F1 Score: {best_f1:.4f})")

    # Save model and artifacts
    os.makedirs(os.path.join("ml", "saved_models"), exist_ok=True)
    model_path = os.path.join("ml", "saved_models", "expiry_classifier.joblib")
    joblib.dump({
        "model": best_model,
        "model_name": best_clf_name,
        "feature_names": feature_cols,
        "label_mapping": label_names,
        "metrics": results[best_clf_name],
        "all_classifiers": results
    }, model_path)

    metrics_path = os.path.join("ml", "saved_models", "expiry_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved best classifier to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    print("=" * 70)
    return results

if __name__ == "__main__":
    train_expiry_classifier()
