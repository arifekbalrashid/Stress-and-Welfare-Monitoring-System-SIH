"""Consent routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.rbac import require_personnel
from app.models.user import User
from app.models.personnel import Personnel
from app.models.consent import Consent, ConsentDataType, ConsentStatus
from app.schemas.consent import ConsentRequest
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("")
def get_consents(current_user: User = Depends(require_personnel), db: Session = Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    consents = db.query(Consent).filter(Consent.personnel_id == p.id).all()
    return APIResponse(data=[
        {
            "id": c.id,
            "data_type": c.data_type.value,
            "status": c.status.value,
            "granted_at": c.granted_at.isoformat() if c.granted_at else None,
            "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
        }
        for c in consents
    ])


@router.post("")
def grant_consent(body: ConsentRequest, current_user: User = Depends(require_personnel), db: Session = Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    try:
        data_type = ConsentDataType(body.data_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data type")

    existing = db.query(Consent).filter(
        Consent.personnel_id == p.id, Consent.data_type == data_type
    ).first()

    if existing:
        existing.status = ConsentStatus.GRANTED
        existing.granted_at = datetime.utcnow()
        existing.withdrawn_at = None
    else:
        existing = Consent(
            personnel_id=p.id, data_type=data_type,
            status=ConsentStatus.GRANTED, granted_at=datetime.utcnow()
        )
        db.add(existing)

    db.commit()
    return APIResponse(message="Consent granted")


@router.post("/withdraw")
def withdraw_consent(body: ConsentRequest, current_user: User = Depends(require_personnel), db: Session = Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel record not found")

    try:
        data_type = ConsentDataType(body.data_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data type")

    existing = db.query(Consent).filter(
        Consent.personnel_id == p.id, Consent.data_type == data_type
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="No consent record found")

    existing.status = ConsentStatus.WITHDRAWN
    existing.withdrawn_at = datetime.utcnow()
    db.commit()
    return APIResponse(message="Consent withdrawn")
