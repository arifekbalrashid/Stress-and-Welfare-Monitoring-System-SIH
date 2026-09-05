import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.auth.security import get_password_hash
from app.models.user import User

engine = create_engine('sqlite:///saathi.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    admin.password_hash = get_password_hash('admin123')
    db.commit()
    print("Successfully reset admin password to 'admin123'")
else:
    print("Admin user not found")
