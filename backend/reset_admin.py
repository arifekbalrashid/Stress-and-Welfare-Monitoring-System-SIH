import asyncio
from app.database.connection import init_db
from app.auth.password import hash_password
from app.models.user import User

async def main():
    await init_db()
    admin = await User.find_one(User.username == "admin")
    if admin:
        admin.password_hash = hash_password("admin123")
        await admin.save()
        print("Successfully reset admin password to 'admin123'")
    else:
        print("Admin user not found")

if __name__ == "__main__":
    asyncio.run(main())
