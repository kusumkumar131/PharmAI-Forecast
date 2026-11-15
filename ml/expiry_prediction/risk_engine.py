from datetime import datetime, date
from typing import Dict, Any

class ExpiryRiskEngine:
    @staticmethod
    def calculate_batch_risk(
        quantity_remaining: float,
        purchase_price: float,
        expiry_date_str: str,
        average_daily_sales: float,
        reference_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Calculates deterministic batch velocity, expected sales, unsold quantity,
        value-at-risk, and operational risk category.
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        try:
            exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except Exception:
            exp_date = reference_date

        days_remaining = (exp_date.date() - reference_date.date()).days

        if days_remaining <= 0:
            return {
                "days_until_expiry": days_remaining,
                "risk_level": "Expired",
                "risk_score": 1.0,
                "expected_sales_before_expiry": 0.0,
                "estimated_unsold_quantity": round(quantity_remaining, 1),
                "inventory_value_at_risk": round(quantity_remaining * purchase_price, 2),
                "recommended_action": "Quarantine / Discard immediately. Do not dispense expired medication under any circumstances."
            }

        daily_sales = max(0.01, float(average_daily_sales))
        expected_sales = daily_sales * days_remaining
        unsold_qty = max(0.0, quantity_remaining - expected_sales)
        unsold_ratio = unsold_qty / max(1.0, quantity_remaining)
        value_at_risk = unsold_qty * purchase_price

        # Risk classification rule
        if days_remaining <= 30 and unsold_ratio > 0.2:
            risk_level = "High Risk"
            risk_score = 0.9
            action = "Urgent FEFO prioritization: Mark for expedited dispensing or supplier return before 30-day cutoff."
        elif unsold_ratio >= 0.50:
            risk_level = "High Risk"
            risk_score = 0.85
            action = "High surplus risk: Estimated >50% batch surplus will expire unsold at current sales velocity. Apply FEFO promotion or stock transfer."
        elif unsold_ratio >= 0.20 or days_remaining <= 60:
            risk_level = "Medium Risk"
            risk_score = 0.55
            action = "Monitor dispensing velocity. Prioritize in FEFO queue before opening newer long-dated batches."
        else:
            risk_level = "Low Risk"
            risk_score = 0.15
            action = "Optimal turnover: Expected sales comfortably exceed remaining inventory before expiry date."

        return {
            "days_until_expiry": days_remaining,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "expected_sales_before_expiry": round(expected_sales, 1),
            "estimated_unsold_quantity": round(unsold_qty, 1),
            "unsold_ratio": round(unsold_ratio, 3),
            "inventory_value_at_risk": round(value_at_risk, 2),
            "recommended_action": action
        }
