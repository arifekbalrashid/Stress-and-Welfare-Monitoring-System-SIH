"""Consent routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.consent import Consent, ConsentDataType, ConsentStatus
from app.schemas.consent import ConsentRequest
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("")
async def get_consents(current_user: User = Depends(require_personnel)):
    p = await Personnel.find_one(Personnel.user_id == current_user.id)
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    consents = await Consent.find(Consent.personnel_id == p.id).to_list()
    return APIResponse(data=[
        {
            "id": str(c.id),
            "data_type": c.data_type.value,
            "status": c.status.value,
            "granted_at": c.granted_at.isoformat() if c.granted_at else None,
            "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
        }
        for c in consents
    ])


@router.post("")
async def grant_consent(body: ConsentRequest, current_user: User = Depends(require_personnel)):
    p = await Personnel.find_one(Personnel.user_id == current_user.id)
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    try:
        data_type = ConsentDataType(body.data_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data type")

    existing = await Consent.find_one(
        Consent.personnel_id == p.id, Consent.data_type == data_type
    )

    if existing:
        existing.status = ConsentStatus.GRANTED
        existing.granted_at = datetime.utcnow()
        existing.withdrawn_at = None
        await existing.save()
    else:
        existing = Consent(
            personnel_id=p.id,
            data_type=data_type,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.utcnow()
        )
        await existing.insert()

    return APIResponse(message="Consent granted")


@router.post("/withdraw")
async def withdraw_consent(body: ConsentRequest, current_user: User = Depends(require_personnel)):
    p = await Personnel.find_one(Personnel.user_id == current_user.id)
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    try:
        data_type = ConsentDataType(body.data_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data type")

    existing = await Consent.find_one(
        Consent.personnel_id == p.id, Consent.data_type == data_type
    )

    if not existing:
        raise HTTPException(status_code=404, detail="No consent record found")

    existing.status = ConsentStatus.WITHDRAWN
    existing.withdrawn_at = datetime.utcnow()
    await existing.save()
    return APIResponse(message="Consent withdrawn")
