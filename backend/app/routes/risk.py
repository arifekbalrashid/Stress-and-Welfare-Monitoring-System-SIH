"""Risk prediction routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.risk_prediction import RiskPrediction
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/history")
async def risk_history(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(require_personnel),
):
    p = await Personnel.find_one(Personnel.user_id == current_user.id)
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    total = await RiskPrediction.find(RiskPrediction.personnel_id == p.id).count()
    predictions = (
        await RiskPrediction.find(RiskPrediction.personnel_id == p.id)
        .sort(-RiskPrediction.created_at)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    return APIResponse(data={
        "items": [
            {
                "id": str(pred.id),
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
