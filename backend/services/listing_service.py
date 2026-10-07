from datetime import datetime,timedelta
import math
from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import Listing,ListingImage,User,SystemSetting,TrafficTransaction
def _setting(db,key,default):
    x=db.get(SystemSetting,key);return float(x.value) if x else default
def list_public(search=""):
    with SessionLocal() as db:
        q=select(Listing).where(Listing.status=="active").order_by(Listing.created_at.desc())
        if search:q=q.where(Listing.title.contains(search))
        return [row_to_dict(x) for x in db.scalars(q).all()]
def user_listings(uid):
    with SessionLocal() as db:
        return [row_to_dict(x) for x in db.scalars(select(Listing).where(Listing.seller_id==uid).order_by(Listing.created_at.desc())).all()]
def get_listing(lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid);return row_to_dict(x) if x else None
def _validate(data):
    if not str(data.get("title","")).strip():return False,"商品名稱不可空白"
    if int(data.get("price",0))<=0:return False,"價格必須大於 0"
    if not str(data.get("brand","")).strip():return False,"廠牌不可空白"
    if not str(data.get("model","")).strip():return False,"車型不可空白"
    return True,""
def create_draft(uid,data):
    ok,msg=_validate(data)
    if not ok:return None,msg
    with SessionLocal() as db:
        x=Listing(seller_id=uid,**data,status="draft");db.add(x);db.commit();return x.id,"草稿已建立"
def update_draft(uid,lid,data):
    ok,msg=_validate(data)
    if not ok:return False,msg
    with SessionLocal() as db:
        x=db.get(Listing,lid)
        if not x or x.seller_id!=uid:return False,"商品不存在"
        if x.status!="draft":return False,"只有草稿可以修改"
        allowed={"title","price","summary","description","brand","model","year","mileage","fuel","transmission","location","body_type","color","meeting_address","delivery_time","payment_method","accepts_loan","months"}
        for k,v in data.items():
            if k in allowed:setattr(x,k,v)
        db.commit();return True,"草稿已更新"
def publication_cost(lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid)
        if not x:return None
        coef=_setting(db,"category_coefficient",0.001)
        minimum=int(_setting(db,"category_minimum",300))
        return math.ceil(x.price*coef)+200*x.months+minimum
def publish(uid,lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid);u=db.get(User,uid)
        if not x or x.seller_id!=uid:return False,"商品不存在"
        if x.status=="active":return False,"商品已經上架，沒有重複扣除流量"
        if x.status!="draft":return False,f"目前狀態 {x.status} 無法上架"
        coef=_setting(db,"category_coefficient",0.001)
        minimum=int(_setting(db,"category_minimum",300))
        cost=math.ceil(x.price*coef)+200*x.months+minimum
        if u.traffic_balance<cost:return False,f"流量不足：目前 {u.traffic_balance}，上架需要 {cost}，尚缺 {cost-u.traffic_balance}"
        before=u.traffic_balance;u.traffic_balance-=cost
        now=datetime.utcnow()
        x.traffic_cost=cost;x.status="active"
        x.published_at=now
        x.expires_at=now+timedelta(days=30*x.months)
        x.listing_time_fee=200*x.months
        x.refunded_time_fee=0
        db.add(TrafficTransaction(user_id=uid,kind="上架扣除",delta=-cost,before_balance=before,after_balance=u.traffic_balance,reason=f"上架商品：{x.title}",reference_id=x.id))
        db.commit();return True,f"上架成功，扣除 {cost} 流量"
def unlist_refund_preview(uid,lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid)
        if not x or x.seller_id!=uid or x.status!="active":return None
        if not x.published_at or not x.expires_at:return 0
        total=max((x.expires_at-x.published_at).total_seconds(),1)
        remaining=max((x.expires_at-datetime.utcnow()).total_seconds(),0)
        refundable=max(int(x.listing_time_fee or 0)-int(x.refunded_time_fee or 0),0)
        return min(refundable,int((x.listing_time_fee or 0)*remaining/total))
def unlist(uid,lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid);u=db.get(User,uid)
        if not x or x.seller_id!=uid:return False,"商品不存在或沒有權限",0
        if x.status!="active":return False,"只有已上架商品可以下架",0
        if not x.published_at or not x.expires_at:
            refund=0
        else:
            total=max((x.expires_at-x.published_at).total_seconds(),1)
            remaining=max((x.expires_at-datetime.utcnow()).total_seconds(),0)
            refundable=max(int(x.listing_time_fee or 0)-int(x.refunded_time_fee or 0),0)
            refund=min(refundable,int((x.listing_time_fee or 0)*remaining/total))
        before=u.traffic_balance
        if refund>0:
            u.traffic_balance+=refund
            x.refunded_time_fee=int(x.refunded_time_fee or 0)+refund
            db.add(TrafficTransaction(user_id=uid,kind="下架退款",delta=refund,before_balance=before,after_balance=u.traffic_balance,reason=f"商品提前下架，退還未使用刊登時間流量：{x.title}",reference_id=x.id))
        x.status="draft"
        x.published_at=None
        x.expires_at=None
        x.traffic_cost=0
        x.listing_time_fee=0
        db.commit()
        return True,f"商品已下架，退還 {refund} 流量；商品已回到草稿",refund

def delete_draft(uid,lid):
    import shutil
    from pathlib import Path
    from backend.database import PROJECT_ROOT
    with SessionLocal() as db:
        x=db.get(Listing,lid)
        if not x or x.seller_id!=uid:return False,"草稿不存在或沒有權限"
        if x.status!="draft":return False,"只有草稿可以永久刪除"
        imgs=db.scalars(select(ListingImage).where(ListingImage.listing_id==lid)).all()
        paths=[PROJECT_ROOT/i.file_path for i in imgs]
        for i in imgs:db.delete(i)
        db.delete(x)
        db.commit()
    for path in paths:
        try:
            if path.exists():path.unlink()
        except OSError:pass
    folder=PROJECT_ROOT/"storage"/"uploads"/"listings"/str(lid)
    try:
        if folder.exists():shutil.rmtree(folder)
    except OSError:pass
    return True,"草稿已永久刪除"

def row_to_dict(x):
    d={c.name:getattr(x,c.name) for c in x.__table__.columns}
    with SessionLocal() as db:
        imgs=db.scalars(select(ListingImage).where(ListingImage.listing_id==x.id).order_by(ListingImage.sort_order,ListingImage.id)).all()
        d["images"]=[{"id":i.id,"file_path":i.file_path,"sort_order":i.sort_order} for i in imgs]
    return d
