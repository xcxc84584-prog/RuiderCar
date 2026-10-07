from sqlalchemy import select
from backend.database import SessionLocal,init_db
from backend.models.entities import User
from backend.services.admin_service import seed_settings,ensure_blacklist_schema
from backend.utils.password import hash_password
from backend.cloud_config import secret

def seed():
    init_db()
    seed_settings()
    email=secret("ADMIN_EMAIL")
    password=secret("ADMIN_PASSWORD")
    name=secret("ADMIN_NAME","Administrator")
    phone=secret("ADMIN_PHONE","0900000000")
    if not email or not password:return
    with SessionLocal() as db:
        admin=db.scalar(select(User).where(User.email==email))
        if not admin:
            db.add(User(name=name,email=email,phone=phone,password_hash=hash_password(password),role="admin",traffic_balance=0,verified=True))
            db.commit()
