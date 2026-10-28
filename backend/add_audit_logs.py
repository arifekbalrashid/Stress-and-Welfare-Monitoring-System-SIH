import sys
import os
import asyncio
sys.path.append(os.getcwd())
from datetime import datetime, timedelta
from app.database.connection import init_db
from app.models.audit_log import AuditLog
from app.models.user import User

async def main():
    await init_db()
    admin_user = await User.find_one(User.username == "admin")
    if not admin_user:
        print("Admin user not found")
        sys.exit(1)

    logs = [
        AuditLog(
            actor_user_id=admin_user.id,
            action="view_risk_profile",
            resource_type="personnel",
            resource_id=None,
            reason="Routine check for high-risk personnel",
            created_at=datetime.utcnow() - timedelta(hours=2)
        ),
        AuditLog(
            actor_user_id=admin_user.id,
            action="export_data",
            resource_type="unit_roster",
            resource_id=None,
            reason="Monthly commanding officer report",
            created_at=datetime.utcnow() - timedelta(hours=1)
        ),
        AuditLog(
            actor_user_id=admin_user.id,
            action="import_operational_data",
            resource_type="operational_data",
            resource_id=None,
            reason="Imported 45 records from august_roster.csv",
            created_at=datetime.utcnow() - timedelta(minutes=15)
        )
    ]

    for log in logs:
        await log.insert()
    print("Added dummy audit logs")

if __name__ == "__main__":
    asyncio.run(main())
