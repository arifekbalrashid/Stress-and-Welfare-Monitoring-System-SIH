"""Welfare officer routes — cases and interventions."""

from fastapi import APIRouter, Depends, HTTPException
from beanie.operators import In
from beanie import PydanticObjectId

from app.auth.rbac import require_welfare_officer
from app.models.user import User
from app.models.personnel import Personnel, ReviewStatus
from app.models.unit import Unit
from app.models.risk_prediction import RiskPrediction, RiskLevel, RiskTrend
from app.models.recommendation import Recommendation
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.models.audit_log import AuditLog
from app.models.consent import Consent, ConsentStatus, ConsentDataType
from app.models.operational_data import OperationalData
from app.models.wellness_checkin import WellnessCheckin
from app.models.support_request import SupportRequest, SupportCategory, SupportStatus
from app.schemas.welfare import InterventionCreate, CaseStatusUpdate, SupportRequestStatusUpdate
from app.schemas.common import APIResponse

router = APIRouter()


async def _resolve_personnel(personnel_id: str) -> Personnel | None:
    try:
        p = await Personnel.get(personnel_id)
        if p:
            return p
    except Exception:
        pass
    return await Personnel.find_one(Personnel.service_id == personnel_id)


@router.get("/cases")
async def get_cases(
    risk_level: str = None,
    trend: str = None,
    review_status: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_welfare_officer),
):
    """List personnel with risk predictions, filterable by risk level, trend, and review status."""
    # Find personnel
    if current_user.assigned_unit_id:
        personnel_list = await Personnel.find(Personnel.unit_id == current_user.assigned_unit_id).to_list()
    else:
        personnel_list = await Personnel.find().to_list()

    personnel_ids = [p.id for p in personnel_list]
    personnel_map = {p.id: p for p in personnel_list}

    # Fetch all units
    units = await Unit.find().to_list()
    unit_map = {u.id: u for u in units}

    # Fetch predictions for these personnel
    all_preds = await RiskPrediction.find(
        In(RiskPrediction.personnel_id, personnel_ids)
    ).sort(-RiskPrediction.created_at).to_list()

    latest_pred_by_person = {}
    for pred in all_preds:
        if pred.personnel_id not in latest_pred_by_person:
            latest_pred_by_person[pred.personnel_id] = pred

    # Summary across all assessed personnel
    summary = {
        "total_assessed": len(latest_pred_by_person),
        "high": sum(1 for p in latest_pred_by_person.values() if (p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)) == RiskLevel.HIGH.value),
        "elevated": sum(1 for p in latest_pred_by_person.values() if (p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)) == RiskLevel.ELEVATED.value),
        "moderate": sum(1 for p in latest_pred_by_person.values() if (p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)) == RiskLevel.MODERATE.value),
        "low": sum(1 for p in latest_pred_by_person.values() if (p.risk_level.value if hasattr(p.risk_level, "value") else str(p.risk_level)) == RiskLevel.LOW.value),
        "increasing": sum(1 for p in latest_pred_by_person.values() if (p.trend.value if hasattr(p.trend, "value") else str(p.trend)) == RiskTrend.INCREASING.value),
    }

    # Filter
    filtered_cases = []
    for pid, pred in latest_pred_by_person.items():
        pers = personnel_map.get(pid)
        if not pers:
            continue

        pl_val = pred.risk_level.value if hasattr(pred.risk_level, "value") else str(pred.risk_level)
        tr_val = pred.trend.value if hasattr(pred.trend, "value") else str(pred.trend)
        rs_val = pers.review_status.value if hasattr(pers.review_status, "value") else str(pers.review_status)

        if risk_level and pl_val != risk_level:
            continue
        if trend and tr_val != trend:
            continue
        if review_status and rs_val != review_status:
            continue

        unit = unit_map.get(pers.unit_id)
        filtered_cases.append({
            "personnel_id": str(pers.id),
            "service_id": pers.service_id,
            "first_name": pers.first_name,
            "last_name": pers.last_name,
            "rank": pers.rank,
            "unit_name": unit.name if unit else None,
            "risk_score": pred.risk_score,
            "risk_level": pl_val,
            "trend": tr_val,
            "review_status": rs_val,
            "confidence": pred.confidence,
            "last_prediction_at": pred.created_at.isoformat(),
            "_sort_rs": rs_val,
            "_sort_tr": tr_val,
            "_sort_score": pred.risk_score,
        })

    status_weights = {
        ReviewStatus.NEEDS_REVIEW.value: 1,
        ReviewStatus.UNDER_REVIEW.value: 2,
        ReviewStatus.MONITORING.value: 3,
        ReviewStatus.INTERVENTION_RECORDED.value: 4,
        ReviewStatus.FOLLOW_UP.value: 5,
        ReviewStatus.CLOSED.value: 6,
    }

    filtered_cases.sort(
        key=lambda x: (
            status_weights.get(x["_sort_rs"], 7),
            1 if x["_sort_tr"] == RiskTrend.INCREASING.value else 2,
            -x["_sort_score"]
        )
    )

    total = len(filtered_cases)
    start = (page - 1) * page_size
    items = filtered_cases[start : start + page_size]
    for it in items:
        it.pop("_sort_rs", None)
        it.pop("_sort_tr", None)
        it.pop("_sort_score", None)

    return APIResponse(data={"items": items, "total": total, "page": page, "page_size": page_size, "summary": summary})


@router.get("/cases/{personnel_id}")
async def get_case_detail(
    personnel_id: str,
    current_user: User = Depends(require_welfare_officer),
):
    """Full case detail with SHAP, recommendations, and intervention history."""
    pers = await _resolve_personnel(personnel_id)
    if not pers:
        raise HTTPException(status_code=404, detail="Personnel not found")

    prediction = await RiskPrediction.find(
        RiskPrediction.personnel_id == pers.id
    ).sort(-RiskPrediction.created_at).first_or_none()

    recs = []
    if prediction:
        recs = await Recommendation.find(
            Recommendation.risk_prediction_id == prediction.id
        ).to_list()

    interventions = await Intervention.find(
        Intervention.personnel_id == pers.id
    ).sort(-Intervention.created_at).limit(20).to_list()

    op_data = await OperationalData.find(
        OperationalData.personnel_id == pers.id
    ).sort(-OperationalData.period_start).first_or_none()

    consent = await Consent.find_one(
        Consent.personnel_id == pers.id,
        Consent.data_type == ConsentDataType.WELLNESS_CHECKIN
    )
    wellness_data = None
    if consent and consent.status == ConsentStatus.GRANTED:
        wellness_data = await WellnessCheckin.find(
            WellnessCheckin.personnel_id == pers.id
        ).sort(-WellnessCheckin.submitted_at).first_or_none()

    unit = await Unit.get(pers.unit_id) if pers.unit_id else None

    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        action="view_case",
        resource_type="personnel",
        resource_id=pers.id,
    )
    await audit.insert()

    return APIResponse(data={
        "personnel_id": str(pers.id),
        "service_id": pers.service_id,
        "first_name": pers.first_name,
        "last_name": pers.last_name,
        "rank": pers.rank,
        "unit_name": unit.name if unit else None,
        "risk_score": prediction.risk_score if prediction else None,
        "risk_prediction_id": str(prediction.id) if prediction else None,
        "risk_level": prediction.risk_level.value if prediction else None,
        "trend": prediction.trend.value if prediction else None,
        "review_status": pers.review_status.value,
        "shap_factors": prediction.shap_factors if prediction else None,
        "confidence": prediction.confidence if prediction else None,
        "has_wellness_data": prediction.has_wellness_data if prediction else None,
        "last_prediction_at": prediction.created_at.isoformat() if prediction else None,
        "data_availability": {
            "operational": op_data is not None,
            "wellness": wellness_data is not None,
            "historical": True
        },
        "operational_context": {
            "duty_hours": op_data.duty_hours if op_data else None,
            "night_shifts": op_data.night_shifts if op_data else None,
            "consecutive_duty_days": op_data.consecutive_duty_days if op_data else None,
            "rest_hours": op_data.rest_hours if op_data else None,
            "deployment_days": op_data.deployment_days if op_data else None,
            "leave_gap_days": op_data.leave_gap_days if op_data else None,
        } if op_data else None,
        "wellness_context": {
            "sleep_quality": wellness_data.sleep_quality if wellness_data else None,
            "energy_level": wellness_data.energy_level if wellness_data else None,
            "workload_perception": wellness_data.workload_score if wellness_data else None,
            "wellbeing": wellness_data.wellbeing_score if wellness_data else None,
            "recovery": wellness_data.recovery_score if wellness_data else None,
        } if wellness_data else None,
        "recommendations": [
            {"category": r.category, "text": r.recommendation_text, "priority": r.priority}
            for r in recs
        ],
        "interventions": [
            {
                "id": str(i.id),
                "intervention_type": i.intervention_type.value,
                "notes": i.notes,
                "status": i.status.value,
                "follow_up_date": str(i.follow_up_date) if i.follow_up_date else None,
                "created_at": i.created_at.isoformat(),
            }
            for i in interventions
        ],
    })


@router.post("/interventions")
async def log_intervention(
    body: InterventionCreate,
    current_user: User = Depends(require_welfare_officer),
):
    try:
        itype = InterventionType(body.intervention_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention type")

    # Resolve personnel_id
    pers = await _resolve_personnel(str(body.personnel_id))
    actual_pid = pers.id if pers else body.personnel_id

    intervention = Intervention(
        personnel_id=actual_pid,
        welfare_officer_id=current_user.id,
        risk_prediction_id=body.risk_prediction_id,
        intervention_type=itype,
        notes=body.notes,
        status=InterventionStatus.PLANNED,
        follow_up_date=body.follow_up_date,
    )
    await intervention.insert()
    return APIResponse(data={"id": str(intervention.id)}, message="Intervention logged")


@router.post("/cases/{personnel_id}/status")
async def update_case_status(
    personnel_id: str,
    body: CaseStatusUpdate,
    current_user: User = Depends(require_welfare_officer),
):
    pers = await _resolve_personnel(personnel_id)
    if not pers:
        raise HTTPException(status_code=404, detail="Personnel not found")

    try:
        new_status = ReviewStatus(body.review_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review status")

    pers.review_status = new_status
    await pers.save()

    return APIResponse(message=f"Case status updated to {new_status.value}")


@router.get("/support-requests")
async def list_support_requests(
    status: str = None,
    category: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_welfare_officer),
):
    """List all support requests submitted by personnel, with optional filters."""
    # Find personnel
    if current_user.assigned_unit_id:
        personnel_list = await Personnel.find(Personnel.unit_id == current_user.assigned_unit_id).to_list()
    else:
        personnel_list = await Personnel.find().to_list()

    personnel_map = {p.id: p for p in personnel_list}
    units = await Unit.find().to_list()
    unit_map = {u.id: u for u in units}

    all_srs = await SupportRequest.find().sort(-SupportRequest.created_at).to_list()

    summary = {
        "total": len(all_srs),
        "submitted": sum(1 for r in all_srs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == SupportStatus.SUBMITTED.value),
        "acknowledged": sum(1 for r in all_srs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == SupportStatus.ACKNOWLEDGED.value),
        "in_progress": sum(1 for r in all_srs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == SupportStatus.IN_PROGRESS.value),
        "resolved": sum(1 for r in all_srs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == SupportStatus.RESOLVED.value),
        "closed": sum(1 for r in all_srs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == SupportStatus.CLOSED.value),
    }

    filtered = []
    for sr in all_srs:
        pers = personnel_map.get(sr.personnel_id)
        if not pers:
            continue

        sr_st = sr.status.value if hasattr(sr.status, "value") else str(sr.status)
        sr_cat = sr.category.value if hasattr(sr.category, "value") else str(sr.category)

        if status and sr_st != status:
            continue
        if category and sr_cat != category:
            continue

        unit = unit_map.get(pers.unit_id)
        filtered.append({
            "id": str(sr.id),
            "personnel_id": str(pers.id),
            "service_id": pers.service_id,
            "first_name": pers.first_name,
            "last_name": pers.last_name,
            "rank": pers.rank,
            "unit_name": unit.name if unit else None,
            "category": sr_cat,
            "description": sr.description,
            "status": sr_st,
            "assigned_to": str(sr.assigned_to) if sr.assigned_to else None,
            "created_at": sr.created_at.isoformat(),
            "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
        })

    status_weights = {
        SupportStatus.SUBMITTED.value: 1,
        SupportStatus.ACKNOWLEDGED.value: 2,
        SupportStatus.IN_PROGRESS.value: 3,
        SupportStatus.RESOLVED.value: 4,
        SupportStatus.CLOSED.value: 5,
    }
    filtered.sort(key=lambda x: (status_weights.get(x["status"], 6), x["created_at"]), reverse=False)

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]

    return APIResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": summary,
    })


@router.post("/support-requests/{request_id}/status")
async def update_support_request_status(
    request_id: str,
    body: SupportRequestStatusUpdate,
    current_user: User = Depends(require_welfare_officer),
):
    """Update a support request's status (acknowledge, in_progress, resolved, closed)."""
    try:
        sr = await SupportRequest.get(request_id)
    except Exception:
        sr = None

    if not sr:
        raise HTTPException(status_code=404, detail="Support request not found")

    try:
        new_status = SupportStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    sr.status = new_status
    if sr.assigned_to is None:
        sr.assigned_to = current_user.id

    await sr.save()

    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        action=f"support_request_{new_status.value}",
        resource_type="support_request",
        resource_id=sr.id,
    )
    await audit.insert()

    return APIResponse(message=f"Support request updated to {new_status.value}")
