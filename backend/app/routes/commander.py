"""Commander routes — unit-level aggregates only, no individual data."""

from collections import defaultdict
from fastapi import APIRouter, Depends
from beanie.operators import In

from app.auth.rbac import require_commander
from app.models.user import User
from app.models.personnel import Personnel
from app.models.unit import Unit
from app.models.risk_prediction import RiskPrediction
from app.models.operational_data import OperationalData
from app.models.wellness_checkin import WellnessCheckin
from app.schemas.common import APIResponse

router = APIRouter()


async def _get_commander_personnel(current_user: User):
    """Return (unit, personnel_list, personnel_ids) for the commander."""
    unit = None
    if current_user.assigned_unit_id:
        unit = await Unit.find_one(Unit.id == current_user.assigned_unit_id)
    if not unit:
        unit = await Unit.find_one(Unit.commander_user_id == current_user.id)

    if unit:
        personnel_list = await Personnel.find(Personnel.unit_id == unit.id).to_list()
    else:
        personnel_list = await Personnel.find().to_list()

    personnel_ids = [p.id for p in personnel_list]
    return unit, personnel_list, personnel_ids


@router.get("/overview")
async def get_overview(current_user: User = Depends(require_commander)):
    """Aggregate risk distribution and trends for the commander's unit(s). No individual data."""
    unit, personnel_list, personnel_ids = await _get_commander_personnel(current_user)

    if not personnel_ids:
        return APIResponse(data={
            "unit_name": unit.name if unit else "All Units",
            "total_personnel": 0,
            "assessed_personnel": 0,
            "risk_distribution": {"low": 0, "moderate": 0, "elevated": 0, "high": 0},
            "avg_risk_score": 0,
        })

    all_preds = await RiskPrediction.find(
        In(RiskPrediction.personnel_id, personnel_ids)
    ).sort(-RiskPrediction.created_at).to_list()

    latest_by_person = {}
    for pred in all_preds:
        if pred.personnel_id not in latest_by_person:
            latest_by_person[pred.personnel_id] = pred

    predictions = list(latest_by_person.values())

    dist = {"low": 0, "moderate": 0, "elevated": 0, "high": 0}
    total_score = 0
    for p in predictions:
        val = p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)
        dist[val] = dist.get(val, 0) + 1
        total_score += p.risk_score

    avg = round(total_score / len(predictions), 1) if predictions else 0

    return APIResponse(data={
        "unit_name": unit.name if unit else "All Units",
        "total_personnel": len(personnel_ids),
        "assessed_personnel": len(predictions),
        "risk_distribution": dist,
        "avg_risk_score": avg,
    })


@router.get("/roster")
async def get_roster(current_user: User = Depends(require_commander)):
    """Unit personnel roster with latest operational metrics — no individual risk/wellness data."""
    unit, personnel_list, personnel_ids = await _get_commander_personnel(current_user)
    if not personnel_ids:
        return APIResponse(data={"unit_name": unit.name if unit else "All Units", "items": []})

    all_ops = await OperationalData.find(
        In(OperationalData.personnel_id, personnel_ids)
    ).sort(-OperationalData.period_end).to_list()

    latest_ops = {}
    for od in all_ops:
        if od.personnel_id not in latest_ops:
            latest_ops[od.personnel_id] = od

    person_map = {p.id: p for p in personnel_list}
    items = []
    for pid, od in latest_ops.items():
        p = person_map.get(pid)
        if not p:
            continue
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
async def get_trends(current_user: User = Depends(require_commander)):
    """Monthly aggregate risk trends for the commander's unit — no individual data exposed."""
    unit, personnel_list, personnel_ids = await _get_commander_personnel(current_user)
    if not personnel_ids:
        return APIResponse(data={"unit_name": unit.name if unit else "All Units", "months": []})

    predictions = await RiskPrediction.find(
        In(RiskPrediction.personnel_id, personnel_ids)
    ).sort(+RiskPrediction.created_at).to_list()

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
            val = p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)
            dist[val] = dist.get(val, 0) + 1

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
async def get_insights(current_user: User = Depends(require_commander)):
    """Anonymized, actionable unit-level insights derived from operational and aggregate data."""
    unit, personnel_list, personnel_ids = await _get_commander_personnel(current_user)
    if not personnel_ids:
        return APIResponse(data={"unit_name": unit.name if unit else "All Units", "insights": []})

    total = len(personnel_ids)

    # Get latest operational data per personnel
    all_ops = await OperationalData.find(
        In(OperationalData.personnel_id, personnel_ids)
    ).sort(-OperationalData.period_end).to_list()
    latest_op_map = {}
    for o in all_ops:
        if o.personnel_id not in latest_op_map:
            latest_op_map[o.personnel_id] = o
    op_rows = list(latest_op_map.values())

    # Get latest risk predictions
    all_preds = await RiskPrediction.find(
        In(RiskPrediction.personnel_id, personnel_ids)
    ).sort(-RiskPrediction.created_at).to_list()
    latest_pred_map = {}
    for p in all_preds:
        if p.personnel_id not in latest_pred_map:
            latest_pred_map[p.personnel_id] = p
    pred_rows = list(latest_pred_map.values())

    # Get latest wellness checkins
    all_wcs = await WellnessCheckin.find(
        In(WellnessCheckin.personnel_id, personnel_ids)
    ).sort(-WellnessCheckin.submitted_at).to_list()
    latest_wc_map = {}
    for w in all_wcs:
        if w.personnel_id not in latest_wc_map:
            latest_wc_map[w.personnel_id] = w
    wc_rows = list(latest_wc_map.values())

    insights = []

    # --- Operational insights ---
    if op_rows:
        duty_hours = [o.duty_hours for o in op_rows if o.duty_hours is not None]
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
        increasing = sum(1 for p in pred_rows if (p.trend.value if hasattr(p.trend, "value") else str(p.trend)) == "increasing")
        high_elevated = sum(1 for p in pred_rows if (p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)) in ("high", "elevated"))
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
