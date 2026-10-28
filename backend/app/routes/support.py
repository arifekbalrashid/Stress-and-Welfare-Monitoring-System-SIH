"""Support request routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.support_request import SupportRequest, SupportCategory, SupportStatus
from app.schemas.admin import SupportRequestCreate
from app.schemas.common import APIResponse

router = APIRouter()


@router.post("/request")
async def submit_request(
    body: SupportRequestCreate,
    current_user: User = Depends(require_personnel),
):
    p = await Personnel.find_one(Personnel.user_id == current_user.id)
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
    await sr.insert()
    return APIResponse(data={"id": str(sr.id)}, message="Request submitted")


@router.get("/requests")
async def get_requests(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(require_personnel),
):
    p = await Personnel.find_one(Personnel.user_id == current_user.id)
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    total = await SupportRequest.find(SupportRequest.personnel_id == p.id).count()
    items = (
        await SupportRequest.find(SupportRequest.personnel_id == p.id)
        .sort(-SupportRequest.created_at)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    return APIResponse(data={
        "items": [
            {
                "id": str(r.id),
                "category": r.category.value,
                "description": r.description,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })
