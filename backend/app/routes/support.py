"""Support request routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.support_request import SupportRequest, SupportCategory, SupportStatus
from app.schemas.admin import SupportRequestCreate
from app.schemas.common import APIResponse

router = APIRouter()


@router.post("/request")
def submit_request(
    body: SupportRequestCreate,
    current_user: User = Depends(require_personnel),
    db: Session = Depends(get_db),
):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    try:
        category = SupportCategory(body.category)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category")

    sr = SupportRequest(
        personnel_id=p.id,
        category=category,
        description=body.description,
        status=SupportStatus.SUBMITTED,
    )
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return APIResponse(data={"id": sr.id}, message="Request submitted")


@router.get("/requests")
def get_requests(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(require_personnel),
    db: Session = Depends(get_db),
):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    total = db.query(SupportRequest).filter(SupportRequest.personnel_id == p.id).count()
    items = (
        db.query(SupportRequest)
        .filter(SupportRequest.personnel_id == p.id)
        .order_by(SupportRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return APIResponse(data={
        "items": [
            {
                "id": r.id, "category": r.category.value,
                "description": r.description, "status": r.status.value,
                "created_at": r.created_at.isoformat(),
            }
            for r in items
        ],
        "total": total, "page": page, "page_size": page_size,
    })
