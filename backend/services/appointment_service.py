from datetime import datetime
from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import Appointment,Listing

def create(buyer_id,listing_id,dt,note=""):
    if dt<=datetime.now(): return False,"不可預約過去時間"
    with SessionLocal() as db:
        listing=db.get(Listing,listing_id)
        if not listing or listing.status!="active":return False,"商品目前不可預約"
        a=Appointment(listing_id=listing_id,buyer_id=buyer_id,appointment_at=dt,note=note,status="等待確認")
        db.add(a); db.commit(); return True,"已送出，等待賣家確認"

def mine(uid):
    with SessionLocal() as db:
        xs=db.scalars(select(Appointment).where(Appointment.buyer_id==uid).order_by(Appointment.appointment_at.desc())).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def seller_pending(uid):
    with SessionLocal() as db:
        xs=db.scalars(select(Appointment).join(Listing,Appointment.listing_id==Listing.id).where(Listing.seller_id==uid).order_by(Appointment.appointment_at)).all()
        return [{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in xs]

def set_status(uid,aid,status):
    with SessionLocal() as db:
        a=db.get(Appointment,aid)
        if not a:return False
        l=db.get(Listing,a.listing_id)
        if l.seller_id!=uid:return False
        a.status=status; db.commit(); return True
