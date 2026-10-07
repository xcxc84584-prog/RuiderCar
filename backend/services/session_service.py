import hashlib
import secrets
from datetime import datetime,timedelta
from sqlalchemy import select,delete
from backend.database import SessionLocal
from backend.models.entities import User
from backend.models.session import LoginSession
SESSION_DAYS=7
def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
def create_login_session(user_id):
    token=secrets.token_urlsafe(48)
    with SessionLocal() as db:
        db.add(LoginSession(user_id=user_id,token_hash=_hash(token),expires_at=datetime.utcnow()+timedelta(days=SESSION_DAYS)))
        db.commit()
    return token
def restore_login_session(token):
    if not token:return None
    now=datetime.utcnow()
    with SessionLocal() as db:
        s=db.scalar(select(LoginSession).where(LoginSession.token_hash==_hash(token)))
        if not s or s.expires_at<=now:
            if s:db.delete(s);db.commit()
            return None
        u=db.get(User,s.user_id)
        if not u or u.suspended:return None
        return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"traffic_balance":u.traffic_balance}
def revoke_login_session(token):
    if not token:return
    with SessionLocal() as db:
        db.execute(delete(LoginSession).where(LoginSession.token_hash==_hash(token)))
        db.commit()
