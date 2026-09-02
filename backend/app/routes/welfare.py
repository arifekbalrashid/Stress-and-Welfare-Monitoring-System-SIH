"""Welfare officer routes — cases and interventions."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.auth.rbac import require_welfare_officer
from app.models.user import User
from app.models.personnel import Personnel, ReviewStatus
from app.models.unit import Unit
from app.models.risk_prediction import RiskPrediction, RiskLevel, RiskTrend
from app.models.recommendation import Recommendation
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.models.audit_log import AuditLog
from app.models.consent import Consent, ConsentStatus, ConsentDataType
from app.schemas.welfare import InterventionCreate, CaseStatusUpdate
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/cases")
def get_cases(
    risk_level: str = None,
    trend: str = None,
    review_status: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_welfare_officer),
    db: Session = Depends(get_db),
):
    """List personnel with risk predictions, filterable by risk level, trend, and review status."""
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_

    # Subquery to get latest prediction per personnel
    latest_pred = (
        db.query(
            RiskPrediction.personnel_id,
            func.max(RiskPrediction.id).label("max_id")
        )
        .group_by(RiskPrediction.personnel_id)
        .subquery()
    )

    query = (
        db.query(RiskPrediction, Personnel, Unit)
        .join(latest_pred, and_(
            RiskPrediction.id == latest_pred.c.max_id,
            RiskPrediction.personnel_id == latest_pred.c.personnel_id
        ))
        .join(Personnel, Personnel.id == RiskPrediction.personnel_id)
        .outerjoin(Unit, Unit.id == Personnel.unit_id)
    )

    # Scope to welfare officer's assigned unit (if set)
    if current_user.assigned_unit_id:
        query = query.filter(Personnel.unit_id == current_user.assigned_unit_id)

    if risk_level:
        try:
            rl = RiskLevel(risk_level)
            query = query.filter(RiskPrediction.risk_level == rl)
        except ValueError:
            pass

    if trend:
        try:
            rt = RiskTrend(trend)
            query = query.filter(RiskPrediction.trend == rt)
        except ValueError:
            pass
            
    if review_status:
        try:
            rs = ReviewStatus(review_status)
            query = query.filter(Personnel.review_status == rs)
        except ValueError:
            pass

    total = query.count()
    
    # Calculate summary counts across all non-filtered items
    all_query = (
        db.query(RiskPrediction.risk_level, RiskPrediction.trend)
        .join(latest_pred, and_(
            RiskPrediction.id == latest_pred.c.max_id,
            RiskPrediction.personnel_id == latest_pred.c.personnel_id
        ))
    )
    all_results = all_query.all()
    
    summary = {
        "total_assessed": len(all_results),
        "high": sum(1 for r in all_results if r[0] == RiskLevel.HIGH),
        "elevated": sum(1 for r in all_results if r[0] == RiskLevel.ELEVATED),
        "moderate": sum(1 for r in all_results if r[0] == RiskLevel.MODERATE),
        "low": sum(1 for r in all_results if r[0] == RiskLevel.LOW),
        "increasing": sum(1 for r in all_results if r[1] == RiskTrend.INCREASING)
    }

    # Workflow-oriented default sorting
    from sqlalchemy import case
    status_order = case(
        (Personnel.review_status == ReviewStatus.NEEDS_REVIEW, 1),
        (Personnel.review_status == ReviewStatus.UNDER_REVIEW, 2),
        (Personnel.review_status == ReviewStatus.MONITORING, 3),
        (Personnel.review_status == ReviewStatus.INTERVENTION_RECORDED, 4),
        (Personnel.review_status == ReviewStatus.FOLLOW_UP, 5),
        (Personnel.review_status == ReviewStatus.CLOSED, 6),
        else_=7
    )
    trend_order = case(
        (RiskPrediction.trend == RiskTrend.INCREASING, 1),
        else_=2
    )
    results = (
        query.order_by(status_order, trend_order, RiskPrediction.risk_score.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    cases = []
    for pred, pers, unit in results:
        cases.append({
            "personnel_id": pers.id,
            "service_id": pers.service_id,
            "first_name": pers.first_name,
            "last_name": pers.last_name,
            "rank": pers.rank,
            "unit_name": unit.name if unit else None,
            "risk_score": pred.risk_score,
            "risk_level": pred.risk_level.value,
            "trend": pred.trend.value,
            "review_status": pers.review_status.value,
            "confidence": pred.confidence,
            "last_prediction_at": pred.created_at.isoformat(),
        })

    return APIResponse(data={"items": cases, "total": total, "page": page, "page_size": page_size, "summary": summary})


@router.get("/cases/{personnel_id}")
def get_case_detail(
    personnel_id: int,
    current_user: User = Depends(require_welfare_officer),
    db: Session = Depends(get_db),
):
    """Full case detail with SHAP, recommendations, and intervention history."""
    pers = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    if not pers:
        raise HTTPException(status_code=404, detail="Personnel not found")

    prediction = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.personnel_id == personnel_id)
        .order_by(RiskPrediction.created_at.desc())
        .first()
    )

    recs = []
    if prediction:
        recs = db.query(Recommendation).filter(Recommendation.risk_prediction_id == prediction.id).all()

    interventions = (
        db.query(Intervention)
        .filter(Intervention.personnel_id == personnel_id)
        .order_by(Intervention.created_at.desc())
        .limit(20)
        .all()
    )

    # Context & Data availability
    from app.models.operational_data import OperationalData
    from app.models.wellness_checkin import WellnessCheckin

    op_data = db.query(OperationalData).filter(OperationalData.personnel_id == personnel_id).order_by(OperationalData.period_start.desc()).first()
    
    # Check consent for wellness
    consent = db.query(Consent).filter(Consent.personnel_id == personnel_id, Consent.data_type == ConsentDataType.WELLNESS_CHECKIN).first()
    wellness_data = None
    if consent and consent.status == ConsentStatus.GRANTED:
        wellness_data = db.query(WellnessCheckin).filter(WellnessCheckin.personnel_id == personnel_id).order_by(WellnessCheckin.submitted_at.desc()).first()
        
    data_availability = {
        "operational": op_data is not None,
        "wellness": wellness_data is not None,
        "historical": True
    }

    # Audit log — record this case view
    audit = AuditLog(
        actor_user_id=current_user.id,
        action="view_case",
        resource_type="personnel",
        resource_id=personnel_id,
    )
    db.add(audit)
    db.commit()

    return APIResponse(data={
        "personnel_id": pers.id,
        "service_id": pers.service_id,
        "first_name": pers.first_name,
        "last_name": pers.last_name,
        "rank": pers.rank,
        "unit_name": pers.unit.name if pers.unit else None,
        "risk_score": prediction.risk_score if prediction else None,
        "risk_prediction_id": prediction.id if prediction else None,
        "risk_level": prediction.risk_level.value if prediction else None,
        "trend": prediction.trend.value if prediction else None,
        "review_status": pers.review_status.value,
        "shap_factors": prediction.shap_factors if prediction else None,
        "confidence": prediction.confidence if prediction else None,
        "has_wellness_data": prediction.has_wellness_data if prediction else None,
        "last_prediction_at": prediction.created_at.isoformat() if prediction else None,
        "data_availability": data_availability,
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
                "id": i.id,
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
def log_intervention(
    body: InterventionCreate,
    current_user: User = Depends(require_welfare_officer),
    db: Session = Depends(get_db),
):
    try:
        itype = InterventionType(body.intervention_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention type")

    intervention = Intervention(
        personnel_id=body.personnel_id,
        welfare_officer_id=current_user.id,
        risk_prediction_id=body.risk_prediction_id,
        intervention_type=itype,
        notes=body.notes,
        status=InterventionStatus.PLANNED,
        follow_up_date=body.follow_up_date,
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    return APIResponse(data={"id": intervention.id}, message="Intervention logged")


@router.post("/cases/{personnel_id}/status")
def update_case_status(
    personnel_id: int,
    body: CaseStatusUpdate,
    current_user: User = Depends(require_welfare_officer),
    db: Session = Depends(get_db),
):
    pers = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    if not pers:
        raise HTTPException(status_code=404, detail="Personnel not found")

    try:
        new_status = ReviewStatus(body.review_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review status")

    pers.review_status = new_status
    db.commit()

    return APIResponse(message=f"Case status updated to {new_status.value}")


# ---- Support Requests (Welfare Officer inbox) ----

from app.models.support_request import SupportRequest, SupportStatus
from app.schemas.welfare import SupportRequestStatusUpdate


@router.get("/support-requests")
def list_support_requests(
    status: str = None,
    category: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_welfare_officer),
    db: Session = Depends(get_db),
):
    """List all support requests submitted by personnel, with optional filters."""
    query = db.query(SupportRequest, Personnel).join(
        Personnel, Personnel.id == SupportRequest.personnel_id
    )

    # Scope to welfare officer's assigned unit (if set)
    if current_user.assigned_unit_id:
        query = query.filter(Personnel.unit_id == current_user.assigned_unit_id)

    if status:
        try:
            query = query.filter(SupportRequest.status == SupportStatus(status))
        except ValueError:
            pass

    if category:
        from app.models.support_request import SupportCategory
        try:
            query = query.filter(SupportRequest.category == SupportCategory(category))
        except ValueError:
            pass

    total = query.count()

    # Summary counts (unfiltered)
    all_requests = db.query(SupportRequest.status).all()
    summary = {
        "total": len(all_requests),
        "submitted": sum(1 for r in all_requests if r[0] == SupportStatus.SUBMITTED),
        "acknowledged": sum(1 for r in all_requests if r[0] == SupportStatus.ACKNOWLEDGED),
        "in_progress": sum(1 for r in all_requests if r[0] == SupportStatus.IN_PROGRESS),
        "resolved": sum(1 for r in all_requests if r[0] == SupportStatus.RESOLVED),
        "closed": sum(1 for r in all_requests if r[0] == SupportStatus.CLOSED),
    }

    # Sort: newest unresolved first
    from sqlalchemy import case as sql_case
    status_order = sql_case(
        (SupportRequest.status == SupportStatus.SUBMITTED, 1),
        (SupportRequest.status == SupportStatus.ACKNOWLEDGED, 2),
        (SupportRequest.status == SupportStatus.IN_PROGRESS, 3),
        (SupportRequest.status == SupportStatus.RESOLVED, 4),
        (SupportRequest.status == SupportStatus.CLOSED, 5),
        else_=6,
    )

    results = (
        query.order_by(status_order, SupportRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for sr, pers in results:
        items.append({
            "id": sr.id,
            "personnel_id": pers.id,
            "service_id": pers.service_id,
            "first_name": pers.first_name,
            "last_name": pers.last_name,
            "rank": pers.rank,
            "unit_name": pers.unit.name if pers.unit else None,
            "category": sr.category.value,
            "description": sr.description,
            "status": sr.status.value,
            "assigned_to": sr.assigned_to,
            "created_at": sr.created_at.isoformat(),
            "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
        })

    return APIResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": summary,
    })


@router.post("/support-requests/{request_id}/status")
def update_support_request_status(
    request_id: int,
    body: SupportRequestStatusUpdate,
    current_user: User = Depends(require_welfare_officer),
    db: Session = Depends(get_db),
):
    """Update a support request's status (acknowledge, in_progress, resolved, closed)."""
    sr = db.query(SupportRequest).filter(SupportRequest.id == request_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Support request not found")

    try:
        new_status = SupportStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    sr.status = new_status

    # Auto-assign to the current welfare officer if not already assigned
    if sr.assigned_to is None:
        sr.assigned_to = current_user.id

    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        action=f"support_request_{new_status.value}",
        resource_type="support_request",
        resource_id=sr.id,
    )
    db.add(audit)
    db.commit()

    return APIResponse(message=f"Support request updated to {new_status.value}")
