import hashlib
import secrets
from datetime import datetime,timedelta
from sqlalchemy import select,delete
from backend.database import SessionLocal
from backend.models.entities import User
from backend.models.session import LoginSession
SESSION_HOURS=12
REMEMBER_DAYS=30
def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
def create_login_session(user_id,remember=False,ip_address=""):
    token=secrets.token_urlsafe(48)
    lifetime=timedelta(days=REMEMBER_DAYS) if remember else timedelta(hours=SESSION_HOURS)
    with SessionLocal() as db:
        db.add(LoginSession(user_id=user_id,token_hash=_hash(token),ip_address=str(ip_address or "")[:128],expires_at=datetime.utcnow()+lifetime))
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
        if not u or u.suspended or u.blacklisted or (u.account_status or "active")!="active":return None
        return {"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role,"traffic_balance":u.traffic_balance,"default_meeting_address":u.default_meeting_address or "","registration_type":u.registration_type or "normal","account_status":u.account_status or "active","unread_mail_notifications":bool(u.unread_mail_notifications),"theme_preference":u.theme_preference if u.theme_preference in ("dark","light") else "dark"}
def revoke_login_session(token):
    if not token:return
    with SessionLocal() as db:
        db.execute(delete(LoginSession).where(LoginSession.token_hash==_hash(token)))
        db.commit()
