"""Personnel routes — own profile, risk, dashboard data, support requests."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.risk_prediction import RiskPrediction
from app.models.recommendation import Recommendation
from app.models.operational_data import OperationalData
from app.models.wellness_checkin import WellnessCheckin
from app.models.audit_log import AuditLog
from app.models.risk_prediction import RiskLevel, RiskTrend
from app.schemas.common import APIResponse
from pydantic import BaseModel
from datetime import datetime, date



router = APIRouter()


@router.get("/me")
def get_me(current_user: User = Depends(require_personnel), db: Session = Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")
    return APIResponse(data={
        "id": p.id,
        "service_id": p.service_id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "rank": p.rank,
        "unit_name": p.unit.name if p.unit else None,
        "date_of_joining": str(p.date_of_joining) if p.date_of_joining else None,
        "email": current_user.email,
        "username": current_user.username,
    })


@router.get("/me/risk")
def get_my_risk(request: Request, current_user: User = Depends(require_personnel), db: Session = Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    prediction = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.personnel_id == p.id)
        .order_by(RiskPrediction.created_at.desc())
        .first()
    )
    if not prediction:
        return APIResponse(data=None, message="No risk assessment available yet")

    recs = db.query(Recommendation).filter(Recommendation.risk_prediction_id == prediction.id).all()

    recs_list = [
        {"category": r.category, "text": r.recommendation_text, "priority": r.priority}
        for r in recs
    ]
    shap_factors = prediction.shap_factors

    lang = request.headers.get("Accept-Language", "en").split(",")[0]
    if not lang.startswith("en"):
        from app.services.translation import translate_strings
        texts = [r["text"] for r in recs_list] + [r["category"] for r in recs_list] + [f["label"] for f in shap_factors.get("factors", [])]
        translated = translate_strings(texts, lang)
        
        if len(translated) == len(texts):
            num_recs = len(recs_list)
            for i, r in enumerate(recs_list):
                r["text"] = translated[i]
                r["category"] = translated[num_recs + i]
            for i, f in enumerate(shap_factors.get("factors", [])):
                f["label"] = translated[(num_recs * 2) + i]

    return APIResponse(data={
        "id": prediction.id,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level.value,
        "trend": prediction.trend.value,
        "shap_factors": shap_factors,
        "confidence": prediction.confidence,
        "has_wellness_data": prediction.has_wellness_data,
        "created_at": prediction.created_at.isoformat(),
        "recommendations": recs_list,
    })


@router.get("/me/dashboard")
def get_dashboard(request: Request, current_user: User = Depends(require_personnel), db: Session = Depends(get_db)):
    """Aggregated dashboard data: risk history, recent changes, latest check-in status."""
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    # Risk history for trend chart (monthly average, up to last 8 months)
    from collections import defaultdict
    predictions = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.personnel_id == p.id)
        .order_by(RiskPrediction.created_at.asc())
        .all()
    )
    monthly = defaultdict(list)
    for pred in predictions:
        key = pred.created_at.strftime("%Y-%m")
        monthly[key].append(pred)

    risk_history = []
    for month_key in sorted(monthly.keys()):
        preds = monthly[month_key]
        avg_score = sum(p.risk_score for p in preds) / len(preds)
        if avg_score < 25: level = "low"
        elif avg_score < 50: level = "moderate"
        elif avg_score < 75: level = "elevated"
        else: level = "high"
        
        last_date = max(p.created_at for p in preds).isoformat()
        risk_history.append({"score": avg_score, "level": level, "date": last_date})
    
    risk_history = risk_history[-8:]

    # Recent changes — compare last 2 operational data periods
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.personnel_id == p.id)
        .order_by(OperationalData.period_end.desc())
        .limit(2)
        .all()
    )
    recent_changes = []
    if len(ops) >= 2:
        curr, prev = ops[0], ops[1]
        def _change(label, curr_val, prev_val, unit="", higher_is_worse=True):
            if curr_val is None or prev_val is None or prev_val == 0:
                return None
            diff = curr_val - prev_val
            pct = round((diff / prev_val) * 100)
            if abs(pct) < 3:
                return None
            direction = "up" if diff > 0 else "down"
            is_negative = (higher_is_worse and diff > 0) or (not higher_is_worse and diff < 0)
            if unit == "days" or unit == "shifts":
                return {"label": label, "direction": direction, "value": f"{abs(round(diff))} {unit}", "negative": is_negative}
            return {"label": label, "direction": direction, "value": f"{abs(pct)}%", "negative": is_negative}

        changes = [
            _change("Duty workload", curr.duty_hours, prev.duty_hours),
            _change("Night shifts", curr.night_shifts, prev.night_shifts, "shifts"),
            _change("Rest hours", curr.rest_hours, prev.rest_hours, higher_is_worse=False),
            _change("Leave gap", curr.leave_gap_days, prev.leave_gap_days, "days"),
            _change("Deployment", curr.deployment_days, prev.deployment_days, "days"),
            _change("Consecutive duty", curr.consecutive_duty_days, prev.consecutive_duty_days, "days"),
        ]
        recent_changes = [c for c in changes if c is not None][:4]
        
    lang = request.headers.get("Accept-Language", "en").split(",")[0]
    if not lang.startswith("en") and recent_changes:
        from app.services.translation import translate_strings
        texts = [c["label"] for c in recent_changes]
        translated = translate_strings(texts, lang)
        if len(translated) == len(texts):
            for i, c in enumerate(recent_changes):
                c["label"] = translated[i]

    # Latest check-in
    latest_checkin = (
        db.query(WellnessCheckin)
        .filter(WellnessCheckin.personnel_id == p.id)
        .order_by(WellnessCheckin.submitted_at.desc())
        .first()
    )
    checkin_status = None
    if latest_checkin:
        checkin_status = {
            "submitted_at": latest_checkin.submitted_at.isoformat(),
        }

    # Access log for this personnel (limited, user-facing)
    access_logs = (
        db.query(AuditLog)
        .filter(AuditLog.resource_type == "personnel", AuditLog.resource_id == p.id)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
        .all()
    )
    access_history = [
        {
            "action": log.action,
            "actor_role": "Welfare Officer",
            "date": log.created_at.isoformat(),
        }
        for log in access_logs
    ]

    return APIResponse(data={
        "risk_history": risk_history,
        "recent_changes": recent_changes,
        "checkin_status": checkin_status,
        "access_history": access_history,
    })


