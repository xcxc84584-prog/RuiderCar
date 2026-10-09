from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import TrafficTransaction,TrafficPurchaseRequest,User

def transactions(uid,limit=None):
    with SessionLocal() as db:
        q=select(TrafficTransaction).where(TrafficTransaction.user_id==uid).order_by(TrafficTransaction.created_at.desc())
        if limit:q=q.limit(limit)
        xs=db.scalars(q).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def purchase_requests(uid):
    with SessionLocal() as db:
        xs=db.scalars(select(TrafficPurchaseRequest).where(TrafficPurchaseRequest.user_id==uid).order_by(TrafficPurchaseRequest.created_at.desc())).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def request_purchase(uid,amount,last5,note):
    if amount<500:return False,"最低購買 NT$500"
    last5=str(last5).strip()
    if len(last5)!=5 or not last5.isdigit():return False,"匯款帳號末五碼必須為 5 位數字"
    with SessionLocal() as db:
        db.add(TrafficPurchaseRequest(user_id=uid,amount=amount,last5=last5,note=note,status="等待審核"))
        db.commit()
        return True,"已送出審核"

def _is_admin(db,uid):
    u=db.get(User,uid);return bool(u and u.role=="admin" and not u.suspended and not u.blacklisted and (u.account_status or "active")=="active")

def pending(admin_uid):
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return []
        xs=db.scalars(select(TrafficPurchaseRequest).where(TrafficPurchaseRequest.status=="等待審核").order_by(TrafficPurchaseRequest.created_at.asc())).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def approve(admin_uid,rid):
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return False,"沒有管理員權限"
        try:
            r=db.get(TrafficPurchaseRequest,rid)
            if not r:return False,"申請不存在"
            if r.status!="等待審核":return False,f"此申請已處理：{r.status}"
            u=db.get(User,r.user_id)
            if not u:return False,"會員不存在"
            before=u.traffic_balance
            u.traffic_balance+=r.amount
            r.status="已批准"
            db.add(TrafficTransaction(user_id=u.id,kind="購買流量",delta=r.amount,before_balance=before,after_balance=u.traffic_balance,reason=f"流量購買申請 #{r.id}",reference_id=r.id))
            db.commit()
            return True,f"已批准申請 #{r.id}，增加 {r.amount} 流量"
        except Exception:
            db.rollback()
            return False,"批准失敗"

def reject(admin_uid,rid):
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return False,"沒有管理員權限"
        try:
            r=db.get(TrafficPurchaseRequest,rid)
            if not r:return False,"申請不存在"
            if r.status!="等待審核":return False,f"此申請已處理：{r.status}"
            r.status="已拒絕"
            db.commit()
            return True,f"已拒絕申請 #{r.id}，未增加流量"
        except Exception:
            db.rollback()
            return False,"拒絕失敗"
