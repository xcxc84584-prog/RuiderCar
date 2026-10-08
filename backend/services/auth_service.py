from sqlalchemy import select,func
from backend.database import SessionLocal
from backend.models.entities import User,SystemSetting,TrafficTransaction,RegistrationRisk
from backend.utils.password import hash_password,verify_password
def setting(db,key,default):
    x=db.get(SystemSetting,key)
    return x.value if x else str(default)
def register(name,email,phone,password):
    name=name.strip();email=email.strip().lower();phone=phone.strip()
    if not name or not email or not phone:return False,"名稱、Email、手機號碼不可空白"
    if "@" not in email or "." not in email.split("@")[-1]:return False,"Email 格式不正確"
    if len(password)<8:return False,"密碼至少 8 碼"
    with SessionLocal() as db:
        limit=max(1,int(setting(db,"account_limit",500)))
        active_count=db.scalar(select(func.count(User.id)).where(~User.email.like("deleted-%@deleted.invalid"))) or 0
        if active_count>=limit:return False,"目前帳號數量已達平台上限，暫時無法建立新帳號"
        if db.scalar(select(User).where(User.email==email)):return False,"此 Email 已註冊"
        if db.scalar(select(User).where(User.phone==phone)):
            db.add(RegistrationRisk(email=email,phone=phone,reason="手機號碼已被其他帳號使用"));db.commit()
            return False,"此手機號碼已綁定其他帳號"
        initial=int(setting(db,"initial_traffic",1000))
        u=User(name=name,email=email,phone=phone,password_hash=hash_password(password),traffic_balance=initial,verified=True)
        db.add(u);db.flush()
        db.add(TrafficTransaction(user_id=u.id,kind="初始發放",delta=initial,before_balance=0,after_balance=initial,reason="新會員初始流量"))
        db.commit()
        return True,"帳號建立成功，現在可以登入"
def login(email,password):
    with SessionLocal() as db:
        u=db.scalar(select(User).where(User.email==email.strip().lower()))
        if not u or u.suspended or u.blacklisted:return None
        if not verify_password(password,u.password_hash):return None
        return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"traffic_balance":u.traffic_balance}
def fresh_user(uid):
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u or u.suspended or u.blacklisted:return None
        return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"traffic_balance":u.traffic_balance}
