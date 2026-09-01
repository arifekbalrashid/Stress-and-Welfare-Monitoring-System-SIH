"""Risk prediction routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.rbac import get_current_user, require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.risk_prediction import RiskPrediction
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/history")
def risk_history(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(require_personnel),
    db: Session = Depends(get_db),
):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    total = db.query(RiskPrediction).filter(RiskPrediction.personnel_id == p.id).count()
    predictions = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.personnel_id == p.id)
        .order_by(RiskPrediction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return APIResponse(data={
        "items": [
            {
                "id": pred.id,
                "risk_score": pred.risk_score,
                "risk_level": pred.risk_level.value,
                "trend": pred.trend.value,
                "confidence": pred.confidence,
                "has_wellness_data": pred.has_wellness_data,
                "created_at": pred.created_at.isoformat(),
            }
            for pred in predictions
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })
