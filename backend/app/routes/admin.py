"""Admin routes — user/personnel/unit management, CSV import, model status, audit logs."""

import csv
import io
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.auth.rbac import require_admin
from app.auth.password import hash_password
from app.models.user import User, UserRole
from app.models.personnel import Personnel
from app.models.unit import Unit
from app.models.operational_data import OperationalData
from app.models.model_version import ModelVersion
from app.models.audit_log import AuditLog
from app.models.support_request import SupportRequest
from app.schemas.admin import UserCreate, UserUpdate, UnitCreate
from app.schemas.personnel import PersonnelCreate
from app.schemas.common import APIResponse

router = APIRouter()


# ---- Users ----

@router.get("/users")
def list_users(page: int = 1, page_size: int = 20, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    total = db.query(User).count()
    users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()
    return APIResponse(data={
        "items": [
            {
                "id": u.id, "username": u.username, "email": u.email,
                "role": u.role.value, "is_active": u.is_active,
                "assigned_unit_id": u.assigned_unit_id,
                "assigned_unit_name": u.assigned_unit.name if u.assigned_unit else None,
            }
            for u in users
        ],
        "total": total, "page": page, "page_size": page_size,
    })


@router.post("/users")
def create_user(body: UserCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == body.username) | (User.email == body.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(username=body.username, email=body.email, password_hash=hash_password(body.password), role=role)
    if body.assigned_unit_id:
        unit = db.query(Unit).filter(Unit.id == body.assigned_unit_id).first()
        if not unit:
            raise HTTPException(status_code=400, detail="Unit not found")
        user.assigned_unit_id = body.assigned_unit_id
        # If commander, also set unit's commander_user_id
    db.add(user)
    db.commit()
    db.refresh(user)
    if role == UserRole.COMMANDER and body.assigned_unit_id:
        unit = db.query(Unit).filter(Unit.id == body.assigned_unit_id).first()
        if unit:
            unit.commander_user_id = user.id
            db.commit()
    return APIResponse(data={"id": user.id}, message="User created")


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        try:
            user.role = UserRole(body.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.assigned_unit_id is not None:
        if body.assigned_unit_id == 0:
            # 0 means unassign
            user.assigned_unit_id = None
        else:
            unit = db.query(Unit).filter(Unit.id == body.assigned_unit_id).first()
            if not unit:
                raise HTTPException(status_code=400, detail="Unit not found")
            user.assigned_unit_id = body.assigned_unit_id
            if user.role == UserRole.COMMANDER:
                unit.commander_user_id = user.id
    db.commit()
    return APIResponse(message="User updated")


# ---- Personnel ----

@router.get("/personnel")
def list_personnel(page: int = 1, page_size: int = 20, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    total = db.query(Personnel).count()
    items = (
        db.query(Personnel)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return APIResponse(data={
        "items": [
            {
                "id": p.id, "user_id": p.user_id, "service_id": p.service_id,
                "first_name": p.first_name, "last_name": p.last_name,
                "rank": p.rank, "unit_name": p.unit.name if p.unit else None,
            }
            for p in items
        ],
        "total": total, "page": page, "page_size": page_size,
    })


@router.post("/personnel")
def create_personnel(body: PersonnelCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = Personnel(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return APIResponse(data={"id": p.id}, message="Personnel created")


# ---- Units ----

@router.get("/units")
def list_units(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    units = db.query(Unit).all()
    return APIResponse(data=[
        {
            "id": u.id, "name": u.name, "location": u.location, "type": u.type,
            "personnel_count": len(u.personnel_list),
        }
        for u in units
    ])


@router.post("/units")
def create_unit(body: UnitCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    unit = Unit(**body.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return APIResponse(data={"id": unit.id}, message="Unit created")


REQUIRED_COLUMNS = {
    "service_id", "period_start", "period_end", "duty_hours", "night_shifts",
    "consecutive_duty_days", "rest_hours", "deployment_days", "leave_gap_days",
}


def _parse_rows(rows: list[dict], db: Session):
    """Parse a list of row dicts into OperationalData records."""
    imported, errors = 0, []
    affected_personnel = set()
    for i, row in enumerate(rows, start=2):
        sid = str(row.get("service_id", "")).strip()
        personnel = db.query(Personnel).filter(Personnel.service_id == sid).first()
        if not personnel:
            errors.append(f"Row {i}: service_id '{sid}' not found")
            continue
        try:
            ps = row["period_start"]
            pe = row["period_end"]
            if isinstance(ps, str):
                ps = date.fromisoformat(ps)
            if isinstance(pe, str):
                pe = date.fromisoformat(pe)
            od = OperationalData(
                personnel_id=personnel.id,
                period_start=ps,
                period_end=pe,
                duty_hours=float(row["duty_hours"]) if row.get("duty_hours") else None,
                night_shifts=int(row["night_shifts"]) if row.get("night_shifts") else None,
                consecutive_duty_days=int(row["consecutive_duty_days"]) if row.get("consecutive_duty_days") else None,
                rest_hours=float(row["rest_hours"]) if row.get("rest_hours") else None,
                deployment_days=int(row["deployment_days"]) if row.get("deployment_days") else None,
                leave_gap_days=int(row["leave_gap_days"]) if row.get("leave_gap_days") else None,
                training_hours=float(row.get("training_hours", 0)) if row.get("training_hours") else None,
                source=row.get("_source", "csv_import"),
            )
            db.add(od)
            affected_personnel.add(personnel.id)
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
    return imported, errors, affected_personnel


@router.post("/import-data")
async def import_data(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Import operational data from CSV or Excel (.xlsx) files."""
    filename = file.filename.lower()
    content = await file.read()

    if filename.endswith(".csv"):
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        columns = set(reader.fieldnames or [])
        if not REQUIRED_COLUMNS.issubset(columns):
            missing = REQUIRED_COLUMNS - columns
            raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")
        rows = list(reader)
        for r in rows:
            r["_source"] = "csv_import"

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            import openpyxl
        except ImportError:
            raise HTTPException(status_code=500, detail="openpyxl not installed — cannot read Excel files")

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        all_rows = list(ws.iter_rows(values_only=True))
        if len(all_rows) < 2:
            raise HTTPException(status_code=400, detail="File is empty or has no data rows")

        headers = [str(h).strip().lower() if h else "" for h in all_rows[0]]
        columns = set(headers)
        if not REQUIRED_COLUMNS.issubset(columns):
            missing = REQUIRED_COLUMNS - columns
            raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")

        rows = []
        for data_row in all_rows[1:]:
            row = {}
            for hi, header in enumerate(headers):
                val = data_row[hi] if hi < len(data_row) else None
                # Convert date objects to string
                if isinstance(val, (datetime, date)):
                    val = val.isoformat()[:10]
                row[header] = val
            row["_source"] = "excel_import"
            rows.append(row)
        wb.close()
    else:
        raise HTTPException(status_code=400, detail="Only CSV and Excel (.xlsx) files are accepted")

    imported, errors, affected_personnel = _parse_rows(rows, db)
    db.commit()
    
    # Trigger prediction update for affected personnel
    from app.services.ml_service import predict_for_personnel
    for pid in affected_personnel:
        try:
            predict_for_personnel(pid, db)
        except Exception:
            pass

    # Audit log
    db.add(AuditLog(
        actor_user_id=current_user.id,
        action="import_operational_data",
        resource_type="operational_data",
        resource_id=0,
        reason=f"Imported {imported} records from {file.filename}",
    ))
    db.commit()

    return APIResponse(data={"imported": imported, "errors": errors[:20]},
                       message=f"Imported {imported} records")


@router.get("/import-status")
def import_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Get the status of the latest operational data import."""
    latest_op = db.query(OperationalData).order_by(OperationalData.created_at.desc()).first()
    return APIResponse(data={
        "latest_import_date": latest_op.created_at.isoformat() if latest_op else None
    })



# ---- Manual Operational Data Entry ----

class ManualOperationalDataEntry(BaseModel):
    service_id: str
    period_start: str
    period_end: str
    duty_hours: Optional[float] = None
    night_shifts: Optional[int] = None
    consecutive_duty_days: Optional[int] = None
    rest_hours: Optional[float] = None
    deployment_days: Optional[int] = None
    leave_gap_days: Optional[int] = None



@router.post("/operational-data")
def add_operational_data(
    body: ManualOperationalDataEntry,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Manually add a single operational data record for a personnel."""
    personnel = db.query(Personnel).filter(Personnel.service_id == body.service_id).first()
    if not personnel:
        raise HTTPException(status_code=404, detail=f"Personnel with service_id '{body.service_id}' not found")

    try:
        od = OperationalData(
            personnel_id=personnel.id,
            period_start=date.fromisoformat(body.period_start),
            period_end=date.fromisoformat(body.period_end),
            duty_hours=body.duty_hours,
            night_shifts=body.night_shifts,
            consecutive_duty_days=body.consecutive_duty_days,
            rest_hours=body.rest_hours,
            deployment_days=body.deployment_days,
            leave_gap_days=body.leave_gap_days,

            source="manual",
        )
        db.add(od)
        db.commit()
        db.refresh(od)
        
        # Trigger prediction update
        from app.services.ml_service import predict_for_personnel
        predict_for_personnel(personnel.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Audit log
    db.add(AuditLog(
        actor_user_id=current_user.id,
        action="manual_entry_operational_data",
        resource_type="operational_data",
        resource_id=od.id,
        reason=f"Manual entry for {body.service_id} ({body.period_start} to {body.period_end})",
    ))
    db.commit()

    return APIResponse(
        data={"id": od.id, "personnel_name": f"{personnel.first_name} {personnel.last_name}"},
        message="Operational data record created"
    )


# ---- Model Status ----

@router.get("/model-status")
def model_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    active = db.query(ModelVersion).filter(ModelVersion.status == "active").first()
    all_versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).limit(10).all()

    return APIResponse(data={
        "active": {
            "id": active.id, "model_type": active.model_type, "version_tag": active.version_tag,
            "metrics": active.metrics, "status": active.status.value,
            "trained_at": active.trained_at.isoformat() if active.trained_at else None,
        } if active else None,
        "versions": [
            {"id": v.id, "model_type": v.model_type, "version_tag": v.version_tag, "status": v.status.value}
            for v in all_versions
        ],
    })


# ---- Audit Logs ----

@router.get("/audit-logs")
def get_audit_logs(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total = db.query(AuditLog).count()
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return APIResponse(data={
        "items": [
            {
                "id": l.id,
                "actor_user_id": l.actor_user_id,
                "actor_username": l.actor.username if l.actor else None,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "reason": l.reason,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": total, "page": page, "page_size": page_size,
    })
