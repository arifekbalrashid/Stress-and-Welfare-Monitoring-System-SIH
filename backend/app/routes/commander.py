"""Commander routes — unit-level aggregates only, no individual data."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.auth.rbac import require_commander
from app.models.user import User
from app.models.personnel import Personnel
from app.models.unit import Unit
from app.models.risk_prediction import RiskPrediction, RiskLevel
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/overview")
def get_overview(current_user: User = Depends(require_commander), db: Session = Depends(get_db)):
    """Aggregate risk distribution and trends for the commander's unit(s). No individual data."""

    # Find the commander's unit
    unit = db.query(Unit).filter(Unit.commander_user_id == current_user.id).first()

    # If no assigned unit, show all units (for demo)
    if unit:
        personnel_ids = [p.id for p in db.query(Personnel.id).filter(Personnel.unit_id == unit.id).all()]
    else:
        personnel_ids = [p.id for p in db.query(Personnel.id).all()]

    if not personnel_ids:
        return APIResponse(data={
            "unit_name": unit.name if unit else "All Units",
            "total_personnel": 0,
            "risk_distribution": {"low": 0, "moderate": 0, "elevated": 0, "high": 0},
            "avg_risk_score": 0,
        })

    # Get latest prediction per personnel
    from sqlalchemy import and_
    latest_pred = (
        db.query(
            RiskPrediction.personnel_id,
            func.max(RiskPrediction.id).label("max_id")
        )
        .filter(RiskPrediction.personnel_id.in_(personnel_ids))
        .group_by(RiskPrediction.personnel_id)
        .subquery()
    )

    predictions = (
        db.query(RiskPrediction)
        .join(latest_pred, and_(
            RiskPrediction.id == latest_pred.c.max_id,
            RiskPrediction.personnel_id == latest_pred.c.personnel_id,
        ))
        .all()
    )

    dist = {"low": 0, "moderate": 0, "elevated": 0, "high": 0}
    total_score = 0
    for p in predictions:
        dist[p.risk_level.value] += 1
        total_score += p.risk_score

    avg = round(total_score / len(predictions), 1) if predictions else 0

    return APIResponse(data={
        "unit_name": unit.name if unit else "All Units",
        "total_personnel": len(personnel_ids),
        "assessed_personnel": len(predictions),
        "risk_distribution": dist,
        "avg_risk_score": avg,
    })


# ---------- Helper: resolve commander's unit + personnel ids ----------
def _get_commander_personnel(current_user: User, db: Session):
    """Return (unit, personnel_ids) for the commander."""
    # Primary: use assigned_unit_id from user record
    if current_user.assigned_unit_id:
        unit = db.query(Unit).filter(Unit.id == current_user.assigned_unit_id).first()
    else:
        # Fallback: old method via Unit.commander_user_id
        unit = db.query(Unit).filter(Unit.commander_user_id == current_user.id).first()

    if unit:
        personnel_ids = [p.id for p in db.query(Personnel.id).filter(Personnel.unit_id == unit.id).all()]
    else:
        personnel_ids = [p.id for p in db.query(Personnel.id).all()]
    return unit, personnel_ids


@router.get("/roster")
def get_roster(
    current_user: User = Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Unit personnel roster with latest operational metrics — no individual risk/wellness data."""
    from app.models.operational_data import OperationalData

    unit, personnel_ids = _get_commander_personnel(current_user, db)
    if not personnel_ids:
        return APIResponse(data={"unit_name": unit.name if unit else "All Units", "items": []})

    # Get latest operational data per personnel
    latest_op = (
        db.query(
            OperationalData.personnel_id,
            func.max(OperationalData.id).label("max_id")
        )
        .filter(OperationalData.personnel_id.in_(personnel_ids))
        .group_by(OperationalData.personnel_id)
        .subquery()
    )

    from sqlalchemy import and_
    op_rows = (
        db.query(OperationalData, Personnel)
        .join(latest_op, and_(
            OperationalData.id == latest_op.c.max_id,
            OperationalData.personnel_id == latest_op.c.personnel_id,
        ))
        .join(Personnel, Personnel.id == OperationalData.personnel_id)
        .all()
    )

    items = []
    for od, p in op_rows:
        items.append({
            "service_id": p.service_id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "rank": p.rank,
            "duty_hours": od.duty_hours,
            "night_shifts": od.night_shifts,
            "consecutive_duty_days": od.consecutive_duty_days,
            "rest_hours": od.rest_hours,
            "deployment_days": od.deployment_days,
            "leave_gap_days": od.leave_gap_days,
            "period": f"{od.period_start.isoformat()} – {od.period_end.isoformat()}",
        })

    # Sort by duty hours descending (most overworked first)
    items.sort(key=lambda x: x["duty_hours"] or 0, reverse=True)

    return APIResponse(data={
        "unit_name": unit.name if unit else "All Units",
        "items": items,
    })


@router.get("/trends")
def get_trends(
    current_user: User = Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Monthly aggregate risk trends for the commander's unit — no individual data exposed."""
    from sqlalchemy import extract, and_

    unit, personnel_ids = _get_commander_personnel(current_user, db)
    if not personnel_ids:
        return APIResponse(data={"unit_name": unit.name if unit else "All Units", "months": []})

    # Get all predictions for the unit's personnel, grouped by year-month
    predictions = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.personnel_id.in_(personnel_ids))
        .order_by(RiskPrediction.created_at)
        .all()
    )

    # Group by month
    from collections import defaultdict
    monthly = defaultdict(list)
    for pred in predictions:
        key = pred.created_at.strftime("%Y-%m")
        monthly[key].append(pred)

    months = []
    for month_key in sorted(monthly.keys()):
        preds = monthly[month_key]
        scores = [p.risk_score for p in preds]
        dist = {"low": 0, "moderate": 0, "elevated": 0, "high": 0}
        for p in preds:
            dist[p.risk_level.value] += 1

        months.append({
            "month": month_key,
            "avg_risk_score": round(sum(scores) / len(scores), 1),
            "min_risk_score": round(min(scores), 1),
            "max_risk_score": round(max(scores), 1),
            "assessed_count": len(preds),
            "risk_distribution": dist,
        })

    return APIResponse(data={
        "unit_name": unit.name if unit else "All Units",
        "months": months,
    })


@router.get("/insights")
def get_insights(
    current_user: User = Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Anonymized, actionable unit-level insights derived from operational and aggregate data."""
    from app.models.operational_data import OperationalData
    from app.models.wellness_checkin import WellnessCheckin
    from sqlalchemy import and_

    unit, personnel_ids = _get_commander_personnel(current_user, db)
    if not personnel_ids:
        return APIResponse(data={"unit_name": unit.name if unit else "All Units", "insights": []})

    total = len(personnel_ids)

    # Get latest operational data per personnel
    latest_op = (
        db.query(
            OperationalData.personnel_id,
            func.max(OperationalData.id).label("max_id")
        )
        .filter(OperationalData.personnel_id.in_(personnel_ids))
        .group_by(OperationalData.personnel_id)
        .subquery()
    )
    op_rows = (
        db.query(OperationalData)
        .join(latest_op, and_(
            OperationalData.id == latest_op.c.max_id,
            OperationalData.personnel_id == latest_op.c.personnel_id,
        ))
        .all()
    )

    # Get latest risk predictions
    latest_pred = (
        db.query(
            RiskPrediction.personnel_id,
            func.max(RiskPrediction.id).label("max_id")
        )
        .filter(RiskPrediction.personnel_id.in_(personnel_ids))
        .group_by(RiskPrediction.personnel_id)
        .subquery()
    )
    pred_rows = (
        db.query(RiskPrediction)
        .join(latest_pred, and_(
            RiskPrediction.id == latest_pred.c.max_id,
            RiskPrediction.personnel_id == latest_pred.c.personnel_id,
        ))
        .all()
    )

    # Get latest wellness checkins
    latest_wc = (
        db.query(
            WellnessCheckin.personnel_id,
            func.max(WellnessCheckin.id).label("max_id")
        )
        .filter(WellnessCheckin.personnel_id.in_(personnel_ids))
        .group_by(WellnessCheckin.personnel_id)
        .subquery()
    )
    wc_rows = (
        db.query(WellnessCheckin)
        .join(latest_wc, and_(
            WellnessCheckin.id == latest_wc.c.max_id,
            WellnessCheckin.personnel_id == latest_wc.c.personnel_id,
        ))
        .all()
    )

    insights = []

    # --- Operational insights ---
    if op_rows:
        duty_hours = [o.duty_hours for o in op_rows if o.duty_hours]
        night_shifts = [o.night_shifts for o in op_rows if o.night_shifts is not None]
        leave_gaps = [o.leave_gap_days for o in op_rows if o.leave_gap_days is not None]
        rest_hours = [o.rest_hours for o in op_rows if o.rest_hours is not None]

        if duty_hours:
            avg_duty = round(sum(duty_hours) / len(duty_hours), 1)
            over_50 = sum(1 for h in duty_hours if h > 50)
            if over_50 > 0:
                pct = round(over_50 / total * 100)
                insights.append({
                    "type": "warning",
                    "category": "workload",
                    "title": "High duty hours detected",
                    "text": f"{pct}% of your unit ({over_50}/{total}) logged over 50 duty hours in the latest period. Unit average is {avg_duty} hrs/week.",
                })

        if leave_gaps:
            avg_leave = round(sum(leave_gaps) / len(leave_gaps), 1)
            over_45 = sum(1 for g in leave_gaps if g > 45)
            if over_45 > 0:
                pct = round(over_45 / total * 100)
                insights.append({
                    "type": "warning",
                    "category": "leave",
                    "title": "Extended leave gaps",
                    "text": f"{pct}% of personnel ({over_45}/{total}) haven't taken leave in over 45 days. Unit average leave gap is {avg_leave} days.",
                })

        if night_shifts:
            max_ns = max(night_shifts)
            min_ns = min(night_shifts)
            if max_ns > 0 and (max_ns - min_ns) >= 4:
                insights.append({
                    "type": "info",
                    "category": "workload",
                    "title": "Uneven night shift distribution",
                    "text": f"Night shifts range from {min_ns} to {max_ns} per month across the unit. Consider redistributing for fairness.",
                })

        if rest_hours:
            low_rest = sum(1 for r in rest_hours if r < 6)
            if low_rest > 0:
                pct = round(low_rest / total * 100)
                insights.append({
                    "type": "warning",
                    "category": "rest",
                    "title": "Insufficient rest periods",
                    "text": f"{pct}% of personnel ({low_rest}/{total}) are averaging less than 6 hours of rest per day.",
                })

    # --- Risk insights ---
    if pred_rows:
        increasing = sum(1 for p in pred_rows if p.trend.value == "increasing")
        high_elevated = sum(1 for p in pred_rows if p.risk_level.value in ("high", "elevated"))
        if increasing > 0:
            pct = round(increasing / total * 100)
            insights.append({
                "type": "warning" if pct > 30 else "info",
                "category": "trend",
                "title": "Rising risk trend",
                "text": f"{pct}% of personnel ({increasing}/{total}) show an increasing risk trend compared to the previous assessment.",
            })
        if high_elevated > 0:
            pct = round(high_elevated / total * 100)
            insights.append({
                "type": "critical" if pct > 40 else "warning",
                "category": "risk",
                "title": "Elevated/high risk personnel",
                "text": f"{pct}% of your unit ({high_elevated}/{total}) is currently assessed at elevated or high risk levels.",
            })

    # --- Wellness participation insight ---
    if wc_rows:
        participation = round(len(wc_rows) / total * 100)
        insights.append({
            "type": "info",
            "category": "engagement",
            "title": "Wellness check-in participation",
            "text": f"{participation}% of personnel ({len(wc_rows)}/{total}) have submitted at least one wellness check-in.",
        })

    # Sort: critical > warning > info
    priority = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda x: priority.get(x["type"], 3))

    return APIResponse(data={
        "unit_name": unit.name if unit else "All Units",
        "insights": insights,
    })
