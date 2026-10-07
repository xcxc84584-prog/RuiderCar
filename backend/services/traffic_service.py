from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import TrafficTransaction,TrafficPurchaseRequest,User

def transactions(uid):
    with SessionLocal() as db:
        xs=db.scalars(select(TrafficTransaction).where(TrafficTransaction.user_id==uid).order_by(TrafficTransaction.created_at.desc())).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def request_purchase(uid,amount,last5,note):
    if amount<500:return False,"最低購買 NT$500"
    with SessionLocal() as db:
        db.add(TrafficPurchaseRequest(user_id=uid,amount=amount,last5=last5,note=note)); db.commit()
        return True,"已送出審核"

def pending():
    with SessionLocal() as db:
        xs=db.scalars(select(TrafficPurchaseRequest).where(TrafficPurchaseRequest.status=="等待審核")).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def approve(rid):
    with SessionLocal() as db:
        r=db.get(TrafficPurchaseRequest,rid)
        if not r or r.status!="等待審核":return False
        u=db.get(User,r.user_id); before=u.traffic_balance; u.traffic_balance+=r.amount; r.status="已批准"
        db.add(TrafficTransaction(user_id=u.id,kind="購買流量",delta=r.amount,before_balance=before,after_balance=u.traffic_balance,reason=f"流量購買申請 #{r.id}",reference_id=r.id))
        db.commit(); return True
