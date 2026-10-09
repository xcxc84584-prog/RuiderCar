from datetime import datetime,timedelta
from sqlalchemy import select,func
from backend.database import SessionLocal
from backend.models.entities import User,SystemSetting,TrafficTransaction,RegistrationRisk
from backend.utils.password import hash_password,verify_password
MAX_LOGIN_FAILURES=5
LOCK_MINUTES=15
def setting(db,key,default):
    x=db.get(SystemSetting,key)
    return x.value if x else str(default)
def _public_user(u):
    return {"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role,"traffic_balance":u.traffic_balance,"default_meeting_address":u.default_meeting_address or "","registration_type":u.registration_type or "normal","account_status":u.account_status or "active"}
def register(name,email,phone,password,registration_type="normal"):
    name=name.strip();email=email.strip().lower();phone=phone.strip();registration_type=str(registration_type or "normal").strip().lower()
    if registration_type not in ("normal","authorized"):return False,"註冊類型不正確"
    if not name or not email or not phone:return False,"名稱、Email、手機號碼不可空白"
    if "@" not in email or "." not in email.split("@")[-1]:return False,"Email 格式不正確"
    if len(password)<8:return False,"密碼至少 8 碼"
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)):return False,"此 Email 已註冊"
        if db.scalar(select(User).where(User.phone==phone)):
            db.add(RegistrationRisk(email=email,phone=phone,reason="手機號碼已被其他帳號使用"));db.commit()
            return False,"此手機號碼已綁定其他帳號"
        if registration_type=="normal":
            limit=max(1,int(setting(db,"account_limit",500)))
            active_count=db.scalar(select(func.count(User.id)).where(User.registration_type=="normal",~User.email.like("deleted-%@deleted.invalid"))) or 0
            if active_count>=limit:return False,"一般註冊帳號數量已達平台上限，可改用授權註冊等待管理員審核"
        initial=int(setting(db,"initial_traffic",1000))
        status="active" if registration_type=="normal" else "pending_approval"
        u=User(name=name,email=email,phone=phone,password_hash=hash_password(password),traffic_balance=initial,verified=True,registration_type=registration_type,account_status=status)
        db.add(u);db.flush()
        db.add(TrafficTransaction(user_id=u.id,kind="初始發放",delta=initial,before_balance=0,after_balance=initial,reason="新會員初始流量"))
        db.commit()
        return (True,"帳號建立成功，現在可以登入") if status=="active" else (True,"授權註冊已送出，請等待管理員批准後再登入")
def login(email,password):
    now=datetime.utcnow();email=email.strip().lower()
    with SessionLocal() as db:
        u=db.scalar(select(User).where(User.email==email))
        if not u or u.suspended or u.blacklisted:return None,"帳號或密碼錯誤"
        if (u.account_status or "active")!="active":
            status=u.account_status or "active"
            msg={"pending_approval":"此帳號正在等待管理員批准","rejected":"此授權註冊已被拒絕"}.get(status,"此帳號目前不可登入")
            return None,msg
        if u.login_locked_until and u.login_locked_until>now:
            mins=max(1,int((u.login_locked_until-now).total_seconds()//60)+1)
            return None,f"登入失敗次數過多，請約 {mins} 分鐘後再試"
        if not verify_password(password,u.password_hash):
            u.failed_login_attempts=(u.failed_login_attempts or 0)+1
            if u.failed_login_attempts>=MAX_LOGIN_FAILURES:
                u.login_locked_until=now+timedelta(minutes=LOCK_MINUTES);u.failed_login_attempts=0
            db.commit();return None,"帳號或密碼錯誤"
        u.failed_login_attempts=0;u.login_locked_until=None;db.commit()
        return _public_user(u),"登入成功"
def fresh_user(uid):
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u or u.suspended or u.blacklisted or (u.account_status or "active")!="active":return None
        return _public_user(u)
