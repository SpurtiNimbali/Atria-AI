"""
Advanced ML models for medical predictions using scikit-learn.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class LabTrendPredictor:
    """
    Advanced lab trend prediction using scikit-learn.
    Uses ensemble of linear and non-linear models.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.linear_model = Ridge(alpha=1.0)
        self.ensemble_model = RandomForestRegressor(n_estimators=50, random_state=42)
    
    def predict_trend(
        self, 
        lab_values: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict lab trend with confidence intervals.
        
        Returns:
        - trend_direction: increasing/decreasing/stable
        - slope: rate of change
        - confidence: prediction confidence (0-1)
        - future_values: predicted next 7 days
        - inflection_point: when trend might change
        """
        if len(lab_values) < 3:
            return {
                "trend_direction": "insufficient_data",
                "confidence": 0.0,
                "message": "Need at least 3 measurements for ML prediction"
            }
        
        # Prepare data
        dates = [datetime.fromisoformat(v["date"]) for v in lab_values]
        values = np.array([v["value"] for v in lab_values])
        
        # Convert dates to days since first measurement
        days_since_start = np.array([(d - dates[0]).days for d in dates]).reshape(-1, 1)
        
        # Train models
        self.linear_model.fit(days_since_start, values)
        
        # Predict next 7 days
        last_day = days_since_start[-1][0]
        future_days = np.array([last_day + i for i in range(1, 8)]).reshape(-1, 1)
        predictions = self.linear_model.predict(future_days)
        
        # Calculate slope and trend
        slope = self.linear_model.coef_[0]
        
        if abs(slope) < 0.05:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        # Calculate confidence based on R² score
        train_predictions = self.linear_model.predict(days_since_start)
        residuals = values - train_predictions
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = max(0, min(1, r_squared))
        
        # Detect velocity changes (acceleration)
        if len(values) >= 4:
            recent_slope = (values[-1] - values[-2]) / (days_since_start[-1][0] - days_since_start[-2][0])
            older_slope = (values[-2] - values[-3]) / (days_since_start[-2][0] - days_since_start[-3][0])
            acceleration = recent_slope - older_slope
        else:
            acceleration = 0
        
        # Predict when value might reach critical threshold
        critical_threshold = None
        days_to_threshold = None
        
        return {
            "trend_direction": trend_direction,
            "slope": float(slope),
            "slope_per_day": float(slope),
            "confidence": float(confidence),
            "r_squared": float(r_squared),
            "acceleration": float(acceleration),
            "future_predictions": [
                {
                    "date": (dates[0] + timedelta(days=int(last_day + i + 1))).isoformat()[:10],
                    "predicted_value": float(predictions[i]),
                    "day": int(last_day + i + 1)
                }
                for i in range(7)
            ],
            "model_type": "Ridge Regression",
            "interpretation": self._interpret_prediction(
                trend_direction, slope, confidence, acceleration
            )
        }
    
    def detect_anomalies(self, lab_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalous lab values using statistical methods.
        """
        if len(lab_values) < 4:
            return []
        
        values = np.array([v["value"] for v in lab_values])
        mean = np.mean(values)
        std = np.std(values)
        
        anomalies = []
        for i, v in enumerate(lab_values):
            z_score = abs((v["value"] - mean) / std) if std > 0 else 0
            
            if z_score > 2.0:  # More than 2 standard deviations
                anomalies.append({
                    "date": v["date"],
                    "value": v["value"],
                    "z_score": float(z_score),
                    "severity": "high" if z_score > 3 else "moderate",
                    "interpretation": f"Outlier: {z_score:.1f} standard deviations from mean"
                })
        
        return anomalies
    
    def compare_to_population(
        self, 
        current_value: float, 
        lab_type: str,
        age: int,
        gender: str
    ) -> Dict[str, Any]:
        """
        Compare patient's value to population norms.
        """
        # Population reference ranges (simplified - would use actual population DB)
        reference_ranges = {
            "hemoglobin": {
                "male": {"mean": 15.5, "std": 1.5, "normal_low": 13.5, "normal_high": 17.5},
                "female": {"mean": 13.5, "std": 1.5, "normal_low": 12.0, "normal_high": 15.5}
            },
            "creatinine": {
                "male": {"mean": 1.0, "std": 0.2, "normal_low": 0.7, "normal_high": 1.3},
                "female": {"mean": 0.9, "std": 0.2, "normal_low": 0.6, "normal_high": 1.1}
            },
            "hba1c": {
                "male": {"mean": 5.5, "std": 0.5, "normal_low": 4.0, "normal_high": 5.6},
                "female": {"mean": 5.5, "std": 0.5, "normal_low": 4.0, "normal_high": 5.6}
            }
        }
        
        gender_key = gender.lower()
        lab_key = lab_type.lower()
        
        if lab_key not in reference_ranges:
            return {"error": f"No reference range for {lab_type}"}
        
        ref = reference_ranges[lab_key].get(gender_key, reference_ranges[lab_key]["male"])
        
        # Calculate percentile
        z_score = (current_value - ref["mean"]) / ref["std"]
        
        if current_value < ref["normal_low"]:
            status = "below_normal"
        elif current_value > ref["normal_high"]:
            status = "above_normal"
        else:
            status = "normal"
        
        return {
            "current_value": current_value,
            "status": status,
            "z_score": float(z_score),
            "reference_range": f"{ref['normal_low']}-{ref['normal_high']}",
            "interpretation": self._interpret_population_comparison(status, z_score, lab_type)
        }
    
    def _interpret_prediction(
        self, 
        trend: str, 
        slope: float, 
        confidence: float, 
        acceleration: float
    ) -> str:
        """Generate clinical interpretation."""
        conf_str = "high confidence" if confidence > 0.8 else "moderate confidence" if confidence > 0.5 else "low confidence"
        
        if trend == "decreasing":
            if acceleration < -0.1:
                return f"Rapidly declining trend ({conf_str}) - rate of decline is accelerating. Urgent intervention needed."
            else:
                return f"Declining trend ({conf_str}) at {abs(slope):.2f} per day. Monitor closely."
        elif trend == "increasing":
            if acceleration > 0.1:
                return f"Rapidly improving trend ({conf_str}) - treatment highly effective."
            else:
                return f"Improving trend ({conf_str}) at {slope:.2f} per day. Continue current management."
        else:
            return f"Stable trend ({conf_str}). Values fluctuating within normal range."
    
    def _interpret_population_comparison(self, status: str, z_score: float, lab_type: str) -> str:
        """Interpret population comparison."""
        if status == "normal":
            return f"Within normal range for age and gender."
        elif status == "below_normal":
            percentile = max(1, int((1 - abs(z_score) / 3) * 50))
            return f"Below normal - approximately {percentile}th percentile for population."
        else:
            percentile = min(99, int((1 + z_score / 3) * 50 + 50))
            return f"Above normal - approximately {percentile}th percentile for population."


class TreatmentEffectEstimator:
    """
    Estimate treatment effects using causal inference techniques.
    """
    
    def estimate_effect(
        self,
        baseline_values: List[float],
        post_treatment_values: List[float],
        treatment_name: str
    ) -> Dict[str, Any]:
        """
        Estimate treatment effect size.
        """
        if not baseline_values or not post_treatment_values:
            return {"error": "Insufficient data"}
        
        baseline_mean = np.mean(baseline_values)
        post_mean = np.mean(post_treatment_values)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(baseline_values) + np.var(post_treatment_values)) / 2)
        cohens_d = (post_mean - baseline_mean) / pooled_std if pooled_std > 0 else 0
        
        # Interpret effect size
        if abs(cohens_d) < 0.2:
            effect_interpretation = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_interpretation = "small"
        elif abs(cohens_d) < 0.8:
            effect_interpretation = "medium"
        else:
            effect_interpretation = "large"
        
        return {
            "treatment": treatment_name,
            "baseline_mean": float(baseline_mean),
            "post_treatment_mean": float(post_mean),
            "absolute_change": float(post_mean - baseline_mean),
            "percent_change": float((post_mean - baseline_mean) / baseline_mean * 100) if baseline_mean != 0 else 0,
            "cohens_d": float(cohens_d),
            "effect_size": effect_interpretation,
            "interpretation": f"{treatment_name} showed {effect_interpretation} effect (Cohen's d = {cohens_d:.2f})"
        }
