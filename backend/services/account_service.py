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

def update_account_info(uid,email,phone,default_meeting_address='',unread_mail_notifications=True):
    email=email.strip().lower();phone=phone.strip()
    if not email or not phone:return False,"Email、電話不可空白",None
    if "@" not in email or "." not in email.split("@")[-1]:return False,"Email 格式不正確",None
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u:return False,"帳號不存在",None
        email_owner=db.scalar(select(User).where(User.email==email,User.id!=uid))
        if email_owner:return False,"此 Email 已被其他帳號使用",None
        phone_owner=db.scalar(select(User).where(User.phone==phone,User.id!=uid))
        if phone_owner:return False,"此電話已被其他帳號使用",None
        u.email=email;u.phone=phone;u.default_meeting_address=str(default_meeting_address or '').strip();u.unread_mail_notifications=bool(unread_mail_notifications)
        db.commit()
        return True,"帳戶訊息已更新",{"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role,"traffic_balance":u.traffic_balance,"default_meeting_address":u.default_meeting_address or "","registration_type":u.registration_type or "normal","account_status":u.account_status or "active","unread_mail_notifications":bool(u.unread_mail_notifications)}
