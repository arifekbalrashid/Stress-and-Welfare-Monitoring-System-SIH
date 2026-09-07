"""
SAATHI ML — Prediction Module
Load trained models and generate per-sample predictions with SHAP explanations.

Usage:
    from predict import ModelPredictor

    predictor = ModelPredictor(model_type="xgboost", artifacts_dir="./artifacts")
    result = predictor.predict({"duty_hours": 60, "night_shifts": 3, ...})
    # → { "risk_score": 72.3, "risk_level": "Elevated", "confidence": 0.68,
    #     "shap_factors": { "duty_hours": 0.32, "rest_hours": -0.18, ... } }
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import joblib


# ── Constants ───────────────────────────────────────────────────────

RISK_LEVELS = ["Low", "Moderate", "Elevated", "High"]

# Midpoints for converting class probabilities → 0–100 score
# Low: 0–30, Moderate: 31–50, Elevated: 51–75, High: 76–100
RISK_MIDPOINTS = {
    "Low": 15.0,
    "Moderate": 40.5,
    "Elevated": 63.0,
    "High": 88.0,
}

DEFAULT_ARTIFACTS = os.path.join(os.path.dirname(__file__), "artifacts")
DEFAULT_FEATURES_CFG = os.path.join(os.path.dirname(__file__), "config", "model_features_v1.json")


def _load_feature_config(path: str = DEFAULT_FEATURES_CFG) -> list[str]:
    with open(path) as f:
        return json.load(f)["features"]


class ModelPredictor:
    """Load a trained SAATHI model and generate predictions."""

    def __init__(self, model_type: str = "xgboost", artifacts_dir: str = DEFAULT_ARTIFACTS):
        self.model_type = model_type
        self.artifacts_dir = Path(artifacts_dir)
        self.feature_cols = _load_feature_config()

        # Load label encoder
        le_path = self.artifacts_dir / "label_encoder_v1.joblib"
        if not le_path.exists():
            raise FileNotFoundError(f"Label encoder not found: {le_path}")
        self.label_encoder = joblib.load(str(le_path))

        # Load model
        if model_type == "xgboost":
            model_path = self.artifacts_dir / "xgboost_v1.joblib"
            if not model_path.exists():
                raise FileNotFoundError(f"XGBoost model not found: {model_path}")
            self.model = joblib.load(str(model_path))
            self.medians = None
            self._explainer = None  # lazy-loaded
        elif model_type == "logistic_regression":
            model_path = self.artifacts_dir / "logistic_regression_v1.joblib"
            if not model_path.exists():
                raise FileNotFoundError(f"LR model not found: {model_path}")
            self.model = joblib.load(str(model_path))
            # Load medians for NaN imputation
            medians_path = self.artifacts_dir / "lr_medians_v1.joblib"
            self.medians = joblib.load(str(medians_path)) if medians_path.exists() else {}
        else:
            raise ValueError(f"Unknown model_type: {model_type}. Use 'xgboost' or 'logistic_regression'.")

    def _get_shap_explainer(self):
        """Lazy-load SHAP TreeExplainer (XGBoost only)."""
        if self._explainer is None:
            import shap
            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer

    def _build_feature_vector(self, features_dict: dict) -> pd.DataFrame:
        """Build a single-row DataFrame from a features dict.

        Missing features are set to NaN.
        """
        row = {}
        for col in self.feature_cols:
            val = features_dict.get(col)
            if val is not None:
                try:
                    row[col] = float(val)
                except (ValueError, TypeError):
                    row[col] = np.nan
            else:
                row[col] = np.nan
        return pd.DataFrame([row], columns=self.feature_cols)

    def _compute_risk_score(self, probabilities: np.ndarray) -> float:
        """Convert class probabilities to a 0–100 continuous risk score.

        Weighted average of class midpoints by their predicted probability.
        """
        classes = list(self.label_encoder.classes_)
        score = 0.0
        for i, cls in enumerate(classes):
            midpoint = RISK_MIDPOINTS.get(cls, 50.0)
            score += probabilities[i] * midpoint
        return round(float(np.clip(score, 0, 100)), 1)

    def _compute_trend(self, current_score: float, previous_score: float | None) -> str:
        """Determine trend based on current vs previous score."""
        if previous_score is None:
            return "stable"
        diff = current_score - previous_score
        if diff > 5:
            return "increasing"
        elif diff < -5:
            return "decreasing"
        return "stable"

    def _score_to_level(self, score: float) -> str:
        """Map a 0–100 score to a risk level string."""
        if score <= 30:
            return "Low"
        elif score <= 50:
            return "Moderate"
        elif score <= 75:
            return "Elevated"
        return "High"

    def predict(self, features_dict: dict, previous_score: float | None = None) -> dict:
        """Generate a prediction for a single sample.

        Parameters
        ----------
        features_dict : dict — feature values (key = feature name, value = number or None)
        previous_score : float, optional — previous risk score for trend computation

        Returns
        -------
        dict with keys: risk_score, risk_level, confidence, trend, shap_factors
        """
        X = self._build_feature_vector(features_dict)

        # Impute for LR
        if self.model_type == "logistic_regression" and self.medians:
            X = X.fillna(self.medians)

        # Predict
        proba = self.model.predict_proba(X)[0]
        predicted_class_idx = int(np.argmax(proba))
        confidence = round(float(proba[predicted_class_idx]), 4)

        # Risk score from probability distribution
        risk_score = self._compute_risk_score(proba)
        risk_level = self._score_to_level(risk_score)
        trend = self._compute_trend(risk_score, previous_score)

        # SHAP explanation (XGBoost only)
        shap_factors = {}
        if self.model_type == "xgboost":
            try:
                explainer = self._get_shap_explainer()
                sv = explainer.shap_values(X)

                # sv is a list of arrays (one per class) for multi-class
                if isinstance(sv, list):
                    # Average across classes for overall feature contribution
                    combined = np.mean([np.abs(s) for s in sv], axis=0)[0]
                elif sv.ndim == 3:
                    combined = np.abs(sv[0]).mean(axis=1)
                else:
                    combined = np.abs(sv[0])

                # Build signed SHAP factors (use the predicted class SHAP values)
                if isinstance(sv, list):
                    signed_vals = sv[predicted_class_idx][0]
                elif sv.ndim == 3:
                    signed_vals = sv[0, :, predicted_class_idx]
                else:
                    signed_vals = sv[0]

                # Top factors sorted by absolute value
                indexed = list(zip(self.feature_cols, signed_vals))
                indexed.sort(key=lambda x: abs(x[1]), reverse=True)

                for feat, val in indexed[:5]:
                    shap_factors[feat] = round(float(val), 4)

            except Exception as e:
                shap_factors = {"error": str(e)}

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "trend": trend,
            "shap_factors": shap_factors,
            "probabilities": {
                cls: round(float(p), 4)
                for cls, p in zip(self.label_encoder.classes_, proba)
            },
        }

    def predict_batch(self, features_list: list[dict], previous_scores: list[float | None] | None = None) -> list[dict]:
        """Generate predictions for multiple samples.

        Parameters
        ----------
        features_list : list of dicts
        previous_scores : list of floats (or None per entry), optional

        Returns
        -------
        list of prediction dicts
        """
        if previous_scores is None:
            previous_scores = [None] * len(features_list)

        return [
            self.predict(feats, prev)
            for feats, prev in zip(features_list, previous_scores)
        ]

    def get_model_info(self) -> dict:
        """Return metadata about the loaded model."""
        report_path = self.artifacts_dir / "training_report_v1.json"
        metrics = {}
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)
            key = "xgboost" if self.model_type == "xgboost" else "logistic_regression"
            metrics = report.get(key, {}).get("metrics", {})

        return {
            "model_type": self.model_type,
            "model_version": "v1.0",
            "feature_set_version": "v1",
            "features": self.feature_cols,
            "metrics": metrics,
        }
