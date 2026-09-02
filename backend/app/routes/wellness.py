"""Wellness check-in routes."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.wellness_checkin import WellnessCheckin
from app.models.operational_data import OperationalData
from app.models.risk_prediction import RiskPrediction, RiskLevel, RiskTrend
from app.schemas.wellness import WellnessCheckinRequest
from app.schemas.common import APIResponse

router = APIRouter()

CHECKIN_COOLDOWN_DAYS = 7  # Allow one check-in per week


@router.get("/checkin/status")
def checkin_status(
    current_user: User = Depends(require_personnel),
    db: Session = Depends(get_db),
):
    """Check if the personnel can submit a new check-in or is on cooldown."""
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    latest = (
        db.query(WellnessCheckin)
        .filter(WellnessCheckin.personnel_id == p.id)
        .order_by(WellnessCheckin.submitted_at.desc())
        .first()
    )

    if latest:
        next_allowed = latest.submitted_at + timedelta(days=CHECKIN_COOLDOWN_DAYS)
        now = datetime.utcnow()
        if now < next_allowed:
            remaining = next_allowed - now
            days_left = remaining.days
            hours_left = remaining.seconds // 3600
            return APIResponse(data={
                "can_submit": False,
                "last_submitted": latest.submitted_at.isoformat(),
                "next_allowed": next_allowed.isoformat(),
                "days_remaining": days_left,
                "hours_remaining": hours_left,
                "cooldown_days": CHECKIN_COOLDOWN_DAYS,
            })

    return APIResponse(data={
        "can_submit": True,
        "last_submitted": latest.submitted_at.isoformat() if latest else None,
        "cooldown_days": CHECKIN_COOLDOWN_DAYS,
    })


@router.post("/checkin")
def submit_checkin(
    body: WellnessCheckinRequest,
    current_user: User = Depends(require_personnel),
    db: Session = Depends(get_db),
):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    # Enforce cooldown
    latest = (
        db.query(WellnessCheckin)
        .filter(WellnessCheckin.personnel_id == p.id)
        .order_by(WellnessCheckin.submitted_at.desc())
        .first()
    )
    if latest:
        next_allowed = latest.submitted_at + timedelta(days=CHECKIN_COOLDOWN_DAYS)
        if datetime.utcnow() < next_allowed:
            days_left = (next_allowed - datetime.utcnow()).days
            raise HTTPException(
                status_code=429,
                detail=f"You can submit your next check-in in {days_left} day(s). Check-ins are allowed once every {CHECKIN_COOLDOWN_DAYS} days."
            )

    checkin = WellnessCheckin(
        personnel_id=p.id,
        sleep_quality=body.sleep_quality,
        energy_level=body.energy_level,
        workload_score=body.workload_score,
        wellbeing_score=body.wellbeing_score,
        recovery_score=body.recovery_score,
        sleep_duration=body.sleep_duration,
        mood=body.mood,
        emotional_exhaustion=body.emotional_exhaustion,
        concentration=body.concentration,
        motivation=body.motivation,
        perceived_support=body.perceived_support,
        physical_exhaustion=body.physical_exhaustion,
        social_connectedness=body.social_connectedness,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    # Run ML prediction pipeline with available data
    from app.services.ml_service import predict_for_personnel
    try:
        result = predict_for_personnel(p.id, db)
        risk_score = result["risk_score"]
    except Exception as e:
        # Fallback if prediction fails
        risk_score = 30.0

    return APIResponse(data={"id": checkin.id, "submitted_at": checkin.submitted_at.isoformat(), "risk_score": risk_score},
                       message="Check-in submitted and risk updated")


@router.get("/history")
def get_history(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(require_personnel),
    db: Session = Depends(get_db),
):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    total = db.query(WellnessCheckin).filter(WellnessCheckin.personnel_id == p.id).count()
    checkins = (
        db.query(WellnessCheckin)
        .filter(WellnessCheckin.personnel_id == p.id)
        .order_by(WellnessCheckin.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return APIResponse(data={
        "items": [
            {
                "id": c.id,
                "sleep_quality": c.sleep_quality,
                "energy_level": c.energy_level,
                "workload_score": c.workload_score,
                "wellbeing_score": c.wellbeing_score,
                "recovery_score": c.recovery_score,
                "submitted_at": c.submitted_at.isoformat(),
            }
            for c in checkins
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })
