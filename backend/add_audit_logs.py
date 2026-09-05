import sys
import os
sys.path.append(os.getcwd())
from datetime import datetime, timedelta
from app.database.connection import SessionLocal
from app.models.audit_log import AuditLog
from app.models.user import User

db = SessionLocal()
admin_user = db.query(User).filter(User.username == "admin").first()
if not admin_user:
    print("Admin user not found")
    sys.exit(1)

logs = [
    AuditLog(
        actor_user_id=admin_user.id,
        action="view_risk_profile",
        resource_type="personnel",
        resource_id=1,
        reason="Routine check for high-risk personnel",
        created_at=datetime.utcnow() - timedelta(hours=2)
    ),
    AuditLog(
        actor_user_id=admin_user.id,
        action="export_data",
        resource_type="unit_roster",
        resource_id=2,
        reason="Monthly commanding officer report",
        created_at=datetime.utcnow() - timedelta(hours=1)
    ),
    AuditLog(
        actor_user_id=admin_user.id,
        action="import_operational_data",
        resource_type="operational_data",
        resource_id=0,
        reason="Imported 45 records from august_roster.csv",
        created_at=datetime.utcnow() - timedelta(minutes=15)
    )
]

db.add_all(logs)
db.commit()
print("Added dummy audit logs")
