import hashlib
import secrets
from datetime import datetime,timedelta
from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import User,SystemSetting,TrafficTransaction,RegistrationRisk
from backend.utils.password import hash_password,verify_password
from backend.services.email_service import send_verification_email

def setting(db,key,default):
    x=db.get(SystemSetting,key)
    return x.value if x else str(default)
def _code_hash(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
def _issue_code(u):
    code=f"{secrets.randbelow(1000000):06d}"
    now=datetime.utcnow()
    u.verification_code_hash=_code_hash(code)
    u.verification_expires_at=now+timedelta(minutes=10)
    u.verification_sent_at=now
    return code
def register(name,email,phone,password):
    email=email.strip().lower();phone=phone.strip()
    if not name.strip() or not email or not phone:return False,"名稱、Email、手機號碼不可空白"
    if "@" not in email or "." not in email.split("@")[-1]:return False,"Email 格式不正確"
    if len(password)<8:return False,"密碼至少 8 碼"
    with SessionLocal() as db:
        existing=db.scalar(select(User).where(User.email==email))
        if existing:
            if not existing.verified:return False,"此 Email 已建立待驗證帳號，請使用下方重新寄送驗證碼"
            return False,"此 Email 已註冊"
        if db.scalar(select(User).where(User.phone==phone)):
            db.add(RegistrationRisk(email=email,phone=phone,reason="手機號碼已被其他帳號使用"));db.commit()
            return False,"此手機號碼已綁定其他帳號"
        initial=int(setting(db,"initial_traffic",1000))
        u=User(name=name.strip(),email=email,phone=phone,password_hash=hash_password(password),traffic_balance=initial,verified=False)
        db.add(u);db.flush()
        db.add(TrafficTransaction(user_id=u.id,kind="初始發放",delta=initial,before_balance=0,after_balance=initial,reason="新會員初始流量"))
        code=_issue_code(u);db.commit()
    ok,msg=send_verification_email(email,code)
    if not ok:return True,"帳號已建立，但驗證信暫時寄送失敗。請使用「重新寄送驗證碼」。"
    return True,"帳號已建立，驗證碼已寄到您的 Email，請完成驗證後登入"
def resend_verification(email):
    email=email.strip().lower()
    with SessionLocal() as db:
        u=db.scalar(select(User).where(User.email==email))
        if not u:return False,"找不到此待驗證帳號"
        if u.verified:return False,"此 Email 已完成驗證"
        now=datetime.utcnow()
        if u.verification_sent_at and (now-u.verification_sent_at).total_seconds()<60:return False,"請等待 60 秒後再重新寄送"
        code=_issue_code(u);db.commit()
    return send_verification_email(email,code)
def verify_email(email,code):
    email=email.strip().lower();code=str(code).strip()
    with SessionLocal() as db:
        u=db.scalar(select(User).where(User.email==email))
        if not u:return False,"帳號不存在"
        if u.verified:return True,"Email 已完成驗證"
        if not u.verification_code_hash or not u.verification_expires_at:return False,"請先重新寄送驗證碼"
        if u.verification_expires_at<datetime.utcnow():return False,"驗證碼已過期，請重新寄送"
        if _code_hash(code)!=u.verification_code_hash:return False,"驗證碼錯誤"
        u.verified=True;u.verification_code_hash="";u.verification_expires_at=None;db.commit()
        return True,"Email 驗證成功，現在可以登入"
def login(email,password):
    with SessionLocal() as db:
        u=db.scalar(select(User).where(User.email==email.strip().lower()))
        if not u or u.suspended or u.blacklisted or not u.verified:return None
        if not verify_password(password,u.password_hash):return None
        return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"traffic_balance":u.traffic_balance}
def fresh_user(uid):
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u or u.suspended or u.blacklisted:return None
        return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"traffic_balance":u.traffic_balance}
