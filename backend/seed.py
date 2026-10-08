from sqlalchemy import select
from backend.database import SessionLocal,init_db,PROJECT_ROOT
from backend.models.entities import User,ListingImage
from backend.services.admin_service import seed_settings,ensure_blacklist_schema
from backend.utils.password import hash_password
from backend.cloud_config import secret

def seed():
    init_db()
    seed_settings()
    # One-time best-effort migration for legacy local image files into durable DB storage.
    with SessionLocal() as db:
        legacy=db.query(ListingImage).filter(ListingImage.image_data.is_(None)).all()
        changed=False
        for img in legacy:
            if not img.file_path:continue
            path=PROJECT_ROOT/img.file_path
            if path.exists() and path.is_file():
                try:
                    img.image_data=path.read_bytes()
                    suffix=path.suffix.lower()
                    img.mime_type={"png":"image/png","webp":"image/webp","jpg":"image/jpeg","jpeg":"image/jpeg"}.get(suffix.lstrip("."),"image/jpeg")
                    changed=True
                except OSError:pass
        if changed:db.commit()
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
