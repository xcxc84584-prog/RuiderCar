from datetime import datetime
import secrets
from sqlalchemy import delete,select
from backend.database import SessionLocal
from backend.models.entities import User,Listing
from backend.models.session import LoginSession
from backend.utils.password import verify_password,hash_password

def close_account(uid,password):
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u:return False,"帳號不存在"
        if u.role=="admin":return False,"管理員帳號不能從會員頁面註銷"
        if u.suspended:return False,"帳號已停用"
        if not verify_password(password,u.password_hash):return False,"目前密碼錯誤"
        for x in db.scalars(select(Listing).where(Listing.seller_id==uid)).all():
            if x.status=="active":x.status="closed"
        stamp=datetime.utcnow().strftime("%Y%m%d%H%M%S")
        nonce=secrets.token_hex(8)
        u.name="已註銷會員"
        u.email=f"deleted-{uid}-{stamp}-{nonce}@deleted.invalid"
        u.phone=f"deleted-{uid}-{nonce}"
        u.password_hash=hash_password(secrets.token_urlsafe(48))
        u.suspended=True
        db.execute(delete(LoginSession).where(LoginSession.user_id==uid))
        db.commit()
        return True,"帳號已註銷"
