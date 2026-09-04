"""
SAATHI Backend — ML Service
Bridges the trained ML models with the FastAPI backend.
Loads models, constructs feature vectors from DB data, stores predictions.
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.personnel import Personnel
from app.models.operational_data import OperationalData
from app.models.wellness_checkin import WellnessCheckin
from app.models.risk_prediction import RiskPrediction, RiskLevel, RiskTrend
from app.models.model_version import ModelVersion, ModelStatus
from app.models.recommendation import Recommendation
from app.config import get_settings
import google.genai as genai
from google.genai import types

# ── Path setup ──────────────────────────────────────────────────────

# ML module lives at <project_root>/ml/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # backend/app/services -> project root
ML_DIR = PROJECT_ROOT / "ml"
ARTIFACTS_DIR = ML_DIR / "artifacts"

# Add ML dir to sys.path so we can import predict module
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))


# ── Singleton predictor ─────────────────────────────────────────────

_predictor = None


def _get_predictor():
    """Lazy-load the predictor singleton."""
    global _predictor
    if _predictor is None:
        from predict import ModelPredictor
        _predictor = ModelPredictor(model_type="xgboost", artifacts_dir=str(ARTIFACTS_DIR))
    return _predictor


def reload_predictor():
    """Force reload after retraining."""
    global _predictor
    _predictor = None
    return _get_predictor()


# ── Feature construction from DB ────────────────────────────────────

def _build_features_from_db(personnel_id: int, db: Session) -> dict:
    """Construct the 13-feature vector for a given personnel from their latest DB records.

    Returns a dict with feature names as keys and numeric values (or None if unavailable).
    """
    # Latest operational data
    op = (
        db.query(OperationalData)
        .filter(OperationalData.personnel_id == personnel_id)
        .order_by(desc(OperationalData.period_end))
        .first()
    )

    # Latest wellness check-in
    wc = (
        db.query(WellnessCheckin)
        .filter(WellnessCheckin.personnel_id == personnel_id)
        .order_by(desc(WellnessCheckin.submitted_at))
        .first()
    )

    # Previous risk prediction (for previous_risk_score)
    prev_pred = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.personnel_id == personnel_id)
        .order_by(desc(RiskPrediction.created_at))
        .first()
    )

    # Average duty hours over last 4 weeks (up to 4 records)
    recent_ops = (
        db.query(OperationalData)
        .filter(OperationalData.personnel_id == personnel_id)
        .order_by(desc(OperationalData.period_end))
        .limit(4)
        .all()
    )

    avg_duty_4w = None
    if recent_ops:
        duties = [r.duty_hours for r in recent_ops if r.duty_hours is not None]
        if duties:
            avg_duty_4w = sum(duties) / len(duties)

    # Workload / recovery change pct (compare last two records)
    workload_change_pct = None
    recovery_change_pct = None
    if len(recent_ops) >= 2:
        # We need wellness data from two periods for change computation
        recent_wellness = (
            db.query(WellnessCheckin)
            .filter(WellnessCheckin.personnel_id == personnel_id)
            .order_by(desc(WellnessCheckin.submitted_at))
            .limit(2)
            .all()
        )
        if len(recent_wellness) >= 2:
            curr_wl = recent_wellness[0].workload_score
            prev_wl = recent_wellness[1].workload_score
            if prev_wl and prev_wl > 0:
                workload_change_pct = ((curr_wl - prev_wl) / prev_wl) * 100

            curr_rc = recent_wellness[0].recovery_score
            prev_rc = recent_wellness[1].recovery_score
            if prev_rc and prev_rc > 0:
                recovery_change_pct = ((curr_rc - prev_rc) / prev_rc) * 100

    features = {
        "duty_hours": op.duty_hours if op else None,
        "night_shifts": op.night_shifts if op else None,
        "consecutive_duty_days": op.consecutive_duty_days if op else None,
        "rest_hours": op.rest_hours if op else None,
        "deployment_days": op.deployment_days if op else None,
        "leave_gap_days": op.leave_gap_days if op else None,
        "sleep_quality": wc.sleep_quality if wc else None,
        "workload_score": wc.workload_score if wc else None,
        "recovery_score": wc.recovery_score if wc else None,
        "average_duty_hours_4w": round(avg_duty_4w, 1) if avg_duty_4w is not None else None,
        "workload_change_pct": round(workload_change_pct, 1) if workload_change_pct is not None else None,
        "recovery_change_pct": round(recovery_change_pct, 1) if recovery_change_pct is not None else None,
        "previous_risk_score": prev_pred.risk_score if prev_pred else None,
    }

    return features


# ── Prediction ──────────────────────────────────────────────────────

def _risk_level_to_enum(level_str: str) -> RiskLevel:
    """Map string risk level to ORM enum."""
    mapping = {
        "Low": RiskLevel.LOW,
        "Moderate": RiskLevel.MODERATE,
        "Elevated": RiskLevel.ELEVATED,
        "High": RiskLevel.HIGH,
    }
    return mapping.get(level_str, RiskLevel.LOW)


def _trend_to_enum(trend_str: str) -> RiskTrend:
    mapping = {
        "increasing": RiskTrend.INCREASING,
        "stable": RiskTrend.STABLE,
        "decreasing": RiskTrend.DECREASING,
    }
    return mapping.get(trend_str, RiskTrend.STABLE)


FEATURE_LABELS = {
    "duty_hours": "Long duty hours",
    "night_shifts": "Frequent night shifts",
    "consecutive_duty_days": "Extended continuous duty",
    "rest_hours": "Insufficient rest",
    "deployment_days": "Extended deployment",
    "leave_gap_days": "Extended leave gap",
    "sleep_quality": "Poor sleep quality",
    "workload_score": "High perceived workload",
    "recovery_score": "Poor recovery",
    "average_duty_hours_4w": "Consistently high duty hours",
    "workload_change_pct": "Increasing workload trend",
    "recovery_change_pct": "Decreasing recovery trend",
    "previous_risk_score": "Past elevated risk",
}

def format_shap_factors(raw_shap: dict) -> dict:
    if not raw_shap or "error" in raw_shap:
        return {"factors": []}
    
    # Normalize absolute values so they sum to 1.0 (100%)
    total_abs = sum(abs(v) for v in raw_shap.values())
    
    factors = []
    for feat, impact in raw_shap.items():
        norm_impact = round(abs(impact) / total_abs, 3) if total_abs > 0 else 0.0
        factors.append({
            "feature": feat,
            "label": FEATURE_LABELS.get(feat, feat.replace("_", " ").title()),
            "impact": norm_impact
        })
    return {"factors": factors}

def predict_for_personnel(personnel_id: int, db: Session) -> dict:
    """Run a prediction for a single personnel and store in DB.

    Returns the prediction result dict.
    """
    predictor = _get_predictor()

    # Build features
    features = _build_features_from_db(personnel_id, db)
    previous_score = features.get("previous_risk_score")

    # Has wellness data?
    has_wellness = any(
        features.get(k) is not None
        for k in ["sleep_quality", "workload_score", "recovery_score"]
    )

    # Run prediction
    result = predictor.predict(features, previous_score=previous_score)

    # Get or create active model version
    model_version = db.query(ModelVersion).filter(ModelVersion.status == ModelStatus.ACTIVE).first()
    if not model_version:
        # Create a placeholder if none exists
        model_version = ModelVersion(
            model_type="xgboost",
            version_tag="v1.0",
            feature_set_version="v1",
            status=ModelStatus.ACTIVE,
            trained_at=datetime.utcnow(),
        )
        db.add(model_version)
        db.flush()

    # Format SHAP factors
    formatted_shap = format_shap_factors(result.get("shap_factors"))

    # Store prediction
    prediction = RiskPrediction(
        personnel_id=personnel_id,
        risk_score=result["risk_score"],
        risk_level=_risk_level_to_enum(result["risk_level"]),
        trend=_trend_to_enum(result["trend"]),
        shap_factors=formatted_shap,
        confidence=result["confidence"],
        model_version_id=model_version.id,
        has_wellness_data=has_wellness,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    # ---- Dynamic AI Recommendations ----
    try:
        settings = get_settings()
        if settings.GEMINI_API_KEY:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Extract top 3 factors for context
            top_factors = [f"{f['label']} ({int(f['impact']*100)}%)" for f in formatted_shap.get("factors", [])[:3]]
            factor_text = ", ".join(top_factors) if top_factors else "general operational stress"
            
            action_goal = "reduce this stress" if prediction.risk_level in (RiskLevel.ELEVATED, RiskLevel.HIGH) else "maintain their wellbeing and manage minor stressors"
            
            prompt = (
                f"The personnel has a {prediction.risk_level.value} stress risk. "
                f"The primary contributing factors identified by our ML model are: {factor_text}. "
                f"Generate exactly 3 practical, supportive suggestions on how they can {action_goal}. "
                f"Return ONLY a JSON array of objects, with each object having 'category' (one of: workload, rest, leave, support) "
                f"and 'text' (a 1-sentence suggestion). No markdown formatting around the output."
            )
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            
            try:
                suggestions = json.loads(response.text)
                for idx, sug in enumerate(suggestions):
                    rec = Recommendation(
                        risk_prediction_id=prediction.id,
                        category=sug.get("category", "support"),
                        recommendation_text=sug.get("text", "Consider speaking with a welfare officer."),
                        priority=idx + 1
                    )
                    db.add(rec)
                db.commit()
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Failed to generate AI recommendations: {e}")

    return {
        "prediction_id": prediction.id,
        "personnel_id": personnel_id,
        **result,
        "shap_factors": formatted_shap,
        "has_wellness_data": has_wellness,
    }


def run_batch_prediction(db: Session) -> dict:
    """Run predictions for all active personnel.

    Returns summary with counts.
    """
    personnel_list = db.query(Personnel).all()
    results = {"total": len(personnel_list), "predicted": 0, "errors": []}

    for p in personnel_list:
        try:
            predict_for_personnel(p.id, db)
            results["predicted"] += 1
        except Exception as e:
            results["errors"].append({"personnel_id": p.id, "error": str(e)})

    return results


# ── Training trigger ────────────────────────────────────────────────

def trigger_training(db: Session) -> dict:
    """Trigger model training by running the train.py script.

    Creates a ModelVersion record, runs training, updates with metrics.
    """
    # Create model version record (status=TRAINING)
    mv = ModelVersion(
        model_type="xgboost",
        version_tag="v1.0",
        feature_set_version="v1",
        status=ModelStatus.TRAINING,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    try:
        # Run training script
        train_script = str(ML_DIR / "train.py")
        result = subprocess.run(
            [sys.executable, train_script, "--artifacts-dir", str(ARTIFACTS_DIR)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
            cwd=str(ML_DIR),
        )

        if result.returncode != 0:
            mv.status = ModelStatus.ARCHIVED
            db.commit()
            return {
                "model_version_id": mv.id,
                "status": "failed",
                "error": result.stderr[-2000:] if result.stderr else "Unknown error",
                "stdout": result.stdout[-2000:] if result.stdout else "",
            }

        # Load training report
        report_path = ARTIFACTS_DIR / "training_report_v1.json"
        metrics = {}
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)
            metrics = report.get("xgboost", {}).get("metrics", {})

        # Archive any previously active model
        db.query(ModelVersion).filter(
            ModelVersion.status == ModelStatus.ACTIVE,
            ModelVersion.id != mv.id,
        ).update({"status": ModelStatus.ARCHIVED})

        # Update model version
        mv.status = ModelStatus.ACTIVE
        mv.metrics = metrics
        mv.artifact_path = str(ARTIFACTS_DIR)
        mv.trained_at = datetime.utcnow()
        db.commit()

        # Reload predictor with new model
        reload_predictor()

        return {
            "model_version_id": mv.id,
            "status": "active",
            "metrics": metrics,
            "stdout": result.stdout[-3000:] if result.stdout else "",
        }

    except subprocess.TimeoutExpired:
        mv.status = ModelStatus.ARCHIVED
        db.commit()
        return {"model_version_id": mv.id, "status": "timeout", "error": "Training exceeded 5 minute limit"}
    except Exception as e:
        mv.status = ModelStatus.ARCHIVED
        db.commit()
        return {"model_version_id": mv.id, "status": "error", "error": str(e)}


def get_model_info() -> dict:
    """Get info about the currently loaded model."""
    try:
        predictor = _get_predictor()
        return predictor.get_model_info()
    except FileNotFoundError:
        return {
            "model_type": None,
            "model_version": None,
            "status": "not_trained",
            "message": "No trained model artifacts found. Run training first.",
        }
