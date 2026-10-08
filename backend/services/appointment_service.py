from datetime import datetime,timedelta
from sqlalchemy import select,or_
from backend.database import SessionLocal
from backend.models.entities import Appointment,Listing,User

def create(buyer_id,listing_id,dt,note=""):
    if dt<=datetime.now(): return False,"不可預約過去時間"
    with SessionLocal() as db:
        listing=db.get(Listing,listing_id)
        if not listing or listing.status!="active":return False,"商品目前不可預約"
        a=Appointment(listing_id=listing_id,buyer_id=buyer_id,appointment_at=dt,note=note,status="等待確認")
        db.add(a);db.commit();return True,"已送出，等待賣家確認"

def _row(db,a,uid):
    listing=db.get(Listing,a.listing_id)
    buyer=db.get(User,a.buyer_id)
    seller=db.get(User,listing.seller_id) if listing else None
    other=seller if a.buyer_id==uid else buyer
    return {**{c.name:getattr(a,c.name) for c in a.__table__.columns},"listing_title":listing.title if listing else "商品已移除","buyer_name":buyer.name if buyer else "","seller_name":seller.name if seller else "","other_user_id":other.id if other else None,"other_name":other.name if other else "","other_email":other.email if other else "","other_phone":other.phone if other else ""}

def mine(uid,keyword=""):
    with SessionLocal() as db:
        xs=db.scalars(select(Appointment).outerjoin(Listing,Appointment.listing_id==Listing.id).where(or_(Appointment.buyer_id==uid,Listing.seller_id==uid)).order_by(Appointment.appointment_at.desc())).all()
        rows=[_row(db,x,uid) for x in xs]
        k=str(keyword or "").strip().lower()
        if k:rows=[r for r in rows if k in str(r.get("other_user_id","")).lower() or k in r.get("other_email","").lower() or k in r.get("other_phone","").lower()]
        return rows

def week_confirmed(uid,target_date):
    start=target_date-timedelta(days=target_date.weekday())
    start_dt=datetime.combine(start,datetime.min.time());end_dt=start_dt+timedelta(days=7)
    with SessionLocal() as db:
        xs=db.scalars(select(Appointment).join(Listing,Appointment.listing_id==Listing.id).where(or_(Appointment.buyer_id==uid,Listing.seller_id==uid),Appointment.status=="已確認",Appointment.appointment_at>=start_dt,Appointment.appointment_at<end_dt).order_by(Appointment.appointment_at)).all()
        return start,[_row(db,x,uid) for x in xs]

def seller_pending(uid):
    with SessionLocal() as db:
        xs=db.scalars(select(Appointment).join(Listing,Appointment.listing_id==Listing.id).where(Listing.seller_id==uid).order_by(Appointment.appointment_at)).all()
        return [_row(db,x,uid) for x in xs]

def set_status(uid,aid,status):
    with SessionLocal() as db:
        a=db.get(Appointment,aid)
        if not a:return False
        l=db.get(Listing,a.listing_id)
        if not l or l.seller_id!=uid:return False
        a.status=status;db.commit();return True

def delete_appointment(uid,aid):
    with SessionLocal() as db:
        a=db.get(Appointment,aid)
        if not a:return False,"預約不存在"
        l=db.get(Listing,a.listing_id)
        if a.buyer_id!=uid and (not l or l.seller_id!=uid):return False,"沒有權限刪除此預約"
        db.delete(a);db.commit();return True,"預約紀錄已刪除"

def delete_appointments(uid,aids):
    ids=[int(x) for x in aids if str(x).isdigit()]
    if not ids:return False,"請先選擇要刪除的預約"
    deleted=0
    with SessionLocal() as db:
        for aid in ids:
            a=db.get(Appointment,aid)
            if not a:continue
            l=db.get(Listing,a.listing_id)
            if a.buyer_id==uid or (l and l.seller_id==uid):
                db.delete(a);deleted+=1
        db.commit()
    return True,f"已刪除 {deleted} 筆預約紀錄"
