import hashlib
import secrets
from datetime import datetime,timedelta
from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import User,SystemSetting,TrafficTransaction,RegistrationRisk,PendingRegistration
from backend.utils.password import hash_password,verify_password
from backend.services.email_service import send_verification_email
def setting(db,key,default):
    x=db.get(SystemSetting,key)
    return x.value if x else str(default)
def _code_hash(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
def _new_code():
    code=f"{secrets.randbelow(1000000):06d}"
    now=datetime.utcnow()
    return code,_code_hash(code),now+timedelta(minutes=10),now
def register(name,email,phone,password):
    name=name.strip();email=email.strip().lower();phone=phone.strip()
    if not name or not email or not phone:return False,"名稱、Email、手機號碼不可空白"
    if "@" not in email or "." not in email.split("@")[-1]:return False,"Email 格式不正確"
    if len(password)<8:return False,"密碼至少 8 碼"
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)):return False,"此 Email 已註冊"
        if db.scalar(select(User).where(User.phone==phone)):
            db.add(RegistrationRisk(email=email,phone=phone,reason="手機號碼已被其他帳號使用"));db.commit()
            return False,"此手機號碼已綁定其他帳號"
        code,code_hash,expires,sent=_new_code()
        p=db.scalar(select(PendingRegistration).where(PendingRegistration.email==email))
        if p:
            p.name=name;p.phone=phone;p.password_hash=hash_password(password)
            p.verification_code_hash=code_hash;p.verification_expires_at=expires;p.verification_sent_at=sent
        else:
            db.add(PendingRegistration(name=name,email=email,phone=phone,password_hash=hash_password(password),verification_code_hash=code_hash,verification_expires_at=expires,verification_sent_at=sent))
        db.commit()
    ok,msg=send_verification_email(email,code)
    if not ok:return True,"註冊資料已暫存，但驗證信寄送失敗。請使用「重新寄送驗證碼」。正式帳號尚未建立。"
    return True,"驗證碼已寄出。完成 Email 驗證後才會正式建立帳號。"
def resend_verification(email):
    email=email.strip().lower()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)):return False,"此 Email 已經是正式帳號"
        p=db.scalar(select(PendingRegistration).where(PendingRegistration.email==email))
        if not p:return False,"找不到此待驗證註冊資料，請重新填寫註冊表單"
        now=datetime.utcnow()
        if p.verification_sent_at and (now-p.verification_sent_at).total_seconds()<60:return False,"請等待 60 秒後再重新寄送"
        code,code_hash,expires,sent=_new_code()
        p.verification_code_hash=code_hash;p.verification_expires_at=expires;p.verification_sent_at=sent
        db.commit()
    return send_verification_email(email,code)
def verify_email(email,code):
    email=email.strip().lower();code=str(code).strip()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)):return False,"此 Email 已建立正式帳號"
        p=db.scalar(select(PendingRegistration).where(PendingRegistration.email==email))
        if not p:return False,"找不到待驗證註冊資料"
        if p.verification_expires_at<datetime.utcnow():return False,"驗證碼已過期，請重新寄送"
        if _code_hash(code)!=p.verification_code_hash:return False,"驗證碼錯誤"
        if db.scalar(select(User).where(User.phone==p.phone)):return False,"此手機號碼已被其他帳號使用"
        initial=int(setting(db,"initial_traffic",1000))
        u=User(name=p.name,email=p.email,phone=p.phone,password_hash=p.password_hash,traffic_balance=initial,verified=True)
        db.add(u);db.flush()
        db.add(TrafficTransaction(user_id=u.id,kind="初始發放",delta=initial,before_balance=0,after_balance=initial,reason="新會員初始流量"))
        db.delete(p);db.commit()
        return True,"Email 驗證成功，正式帳號已建立，現在可以登入"
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
