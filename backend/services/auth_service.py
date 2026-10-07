from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import User,SystemSetting,TrafficTransaction,RegistrationRisk
from backend.utils.password import hash_password,verify_password

def setting(db,key,default):
    x=db.get(SystemSetting,key)
    return x.value if x else str(default)

def register(name,email,phone,password):
    email=email.strip().lower()
    phone=phone.strip()
    if not name.strip() or not email or not phone:
        return False,"名稱、Email、手機號碼不可空白"
    if len(password)<8:
        return False,"密碼至少 8 碼"
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)):
            return False,"此 Email 已註冊"
        if db.scalar(select(User).where(User.phone==phone)):
            db.add(RegistrationRisk(email=email,phone=phone,reason="手機號碼已被其他帳號使用"))
            db.commit()
            return False,"此手機號碼已綁定其他帳號"
        initial=int(setting(db,"initial_traffic",1000))
        u=User(
            name=name.strip(),email=email,phone=phone,
            password_hash=hash_password(password),traffic_balance=initial
        )
        db.add(u)
        db.flush()
        db.add(TrafficTransaction(
            user_id=u.id,kind="初始發放",delta=initial,
            before_balance=0,after_balance=initial,
            reason="新會員初始流量"
        ))
        db.commit()
        return True,"註冊成功"

def login(email,password):
    with SessionLocal() as db:
        u=db.scalar(select(User).where(User.email==email.strip().lower()))
        if not u or u.suspended:
            return None
        if not verify_password(password,u.password_hash):
            return None
        return {
            "id":u.id,"name":u.name,"email":u.email,
            "role":u.role,"traffic_balance":u.traffic_balance
        }
