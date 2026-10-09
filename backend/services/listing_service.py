from datetime import datetime,timedelta
import time
import math
from sqlalchemy import select,func
from backend.database import SessionLocal
from backend.models.entities import Listing,ListingImage,Favorite,Appointment,Message,User,SystemSetting,TrafficTransaction
_PREFETCH_TTL=20
_prefetch_details={}
_prefetch_pages={}
def _setting(db,key,default):
    x=db.get(SystemSetting,key);return float(x.value) if x else default
def list_public(search="",vehicles_only=False):
    with SessionLocal() as db:
        q=select(Listing).where(Listing.status=="active").order_by(Listing.created_at.desc())
        if vehicles_only:q=q.where(Listing.product_type=="vehicle")
        if search:q=q.where(Listing.title.contains(search))
        return [row_to_dict(x) for x in db.scalars(q).all()]

def public_catalog_bounds(search=""):
    with SessionLocal() as db:
        q=select(func.count(Listing.id),func.min(Listing.price),func.max(Listing.price)).where(Listing.status=="active")
        if search:q=q.where(Listing.title.ilike(f"%{search}%"))
        count,min_price,max_price=db.execute(q).one()
        return int(count or 0),int(min_price or 0),int(max_price or 0)
def list_public_page(search="",min_price=None,max_price=None,page=1,page_size=9):
    page=max(1,int(page));page_size=max(1,min(int(page_size),60))
    cache_key=(str(search or ""),min_price,max_price,page,page_size)
    cached=_prefetch_pages.get(cache_key)
    if cached and time.monotonic()-cached[0]<_PREFETCH_TTL:
        return cached[1],cached[2]
    with SessionLocal() as db:
        filters=[Listing.status=="active"]
        if search:filters.append(Listing.title.ilike(f"%{search}%"))
        if min_price is not None:filters.append(Listing.price>=int(min_price))
        if max_price is not None:filters.append(Listing.price<=int(max_price))
        total=int(db.scalar(select(func.count(Listing.id)).where(*filters)) or 0)
        q=(select(Listing,User.name,User.email,User.phone,User.default_meeting_address)
           .join(User,User.id==Listing.seller_id)
           .where(*filters).order_by(Listing.created_at.desc())
           .offset((page-1)*page_size).limit(page_size))
        rows=db.execute(q).all();out=[]
        listing_ids=[x[0].id for x in rows]
        covers={}
        if listing_ids:
            imgs=db.scalars(select(ListingImage).where(ListingImage.listing_id.in_(listing_ids)).order_by(ListingImage.listing_id,ListingImage.sort_order,ListingImage.id)).all()
            for i in imgs:
                if i.listing_id not in covers:covers[i.listing_id]={"id":i.id,"file_path":i.file_path,"mime_type":i.mime_type,"sort_order":i.sort_order}
        for x,name,email,phone,address in rows:
            d={c.name:getattr(x,c.name) for c in x.__table__.columns}
            d["images"]=[covers[x.id]] if x.id in covers else []
            d["seller_name"]=name or "未知賣家";d["seller_email"]=email or "";d["seller_phone"]=phone or "";d["seller_default_meeting_address"]=address or ""
            out.append(d)
        _prefetch_pages[cache_key]=(time.monotonic(),out,total)
        return out,total
def prefetch_public_navigation(search,min_price,max_price,current_page,page_size,current_rows=None,total_pages=None):
    rows=current_rows or []
    for row in rows:
        lid=int(row.get("id",0) or 0)
        if lid and lid not in _prefetch_details:
            try:
                detail=_get_listing_uncached(lid)
                if detail:_prefetch_details[lid]=(time.monotonic(),detail)
            except Exception:pass
    for p in (int(current_page)-1,int(current_page)+1):
        if p>=1 and (total_pages is None or p<=int(total_pages)):
            try:list_public_page(search,min_price,max_price,p,page_size)
            except Exception:pass
def user_listings(uid):
    with SessionLocal() as db:
        return [row_to_dict(x) for x in db.scalars(select(Listing).where(Listing.seller_id==uid).order_by(Listing.created_at.desc())).all()]
def _get_listing_uncached(lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid);return row_to_dict(x) if x else None
def get_listing(lid):
    try:lid=int(lid)
    except:return None
    cached=_prefetch_details.get(lid)
    if cached and time.monotonic()-cached[0]<_PREFETCH_TTL:return cached[1]
    x=_get_listing_uncached(lid)
    if x:_prefetch_details[lid]=(time.monotonic(),x)
    return x
def _validate(data):
    if not str(data.get("title","")).strip():return False,"商品名稱不可空白"
    if int(data.get("price",0))<=0:return False,"價格必須大於 0"
    product_type=data.get("product_type","vehicle")
    if product_type not in ("vehicle","general"):return False,"商品類型錯誤"
    if product_type=="vehicle":
        if not str(data.get("brand","")).strip():return False,"車輛商品的廠牌不可空白"
        if not str(data.get("model","")).strip():return False,"車輛商品的車型不可空白"
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
        allowed={"product_type","title","price","summary","description","brand","model","year","mileage","fuel","transmission","location","body_type","color","meeting_address","delivery_time","payment_method","accepts_loan","months"}
        for k,v in data.items():
            if k in allowed:setattr(x,k,v)
        db.commit();return True,"草稿已更新"
def _traffic_cost(db,x):
    traffic_max=max(1,int(_setting(db,"traffic_max",100)))
    traffic_min=max(1,int(_setting(db,"traffic_min",20)))
    traffic_per=max(1,int(_setting(db,"traffic_per_100k_month",5)))
    if traffic_min>traffic_max:traffic_min=traffic_max
    price_units=max(1,math.ceil(int(x.price)/100000))
    raw=price_units*max(1,int(x.months))*traffic_per
    return min(traffic_max,max(traffic_min,raw))
def publication_cost(lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid)
        if not x:return None
        return _traffic_cost(db,x)
def publish(uid,lid):
    with SessionLocal() as db:
        x=db.get(Listing,lid);u=db.get(User,uid)
        if not x or x.seller_id!=uid:return False,"商品不存在"
        if x.status=="active":return False,"商品已經上架，沒有重複扣除流量"
        if x.status!="draft":return False,f"目前狀態 {x.status} 無法上架"
        cost=_traffic_cost(db,x)
        if u.traffic_balance<cost:return False,f"流量不足：目前 {u.traffic_balance}，上架需要 {cost}，尚缺 {cost-u.traffic_balance}"
        before=u.traffic_balance;u.traffic_balance-=cost
        now=datetime.utcnow()
        x.traffic_cost=cost;x.status="active"
        x.published_at=now
        x.expires_at=now+timedelta(days=30*x.months)
        x.listing_time_fee=max(0,cost-20)
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
            db.add(TrafficTransaction(user_id=uid,kind="下架退款",delta=refund,before_balance=before,after_balance=u.traffic_balance,reason=f"商品提前下架，按剩餘期間退還可退款流量（最低流量不退款）：{x.title}",reference_id=x.id))
        x.status="draft"
        x.published_at=None
        x.expires_at=None
        x.traffic_cost=0
        x.listing_time_fee=0
        db.commit()
        return True,f"商品已下架，退還 {refund} 流量；商品已回到草稿",refund

def delete_draft(uid,lid):
    import shutil
    import logging
    from backend.database import PROJECT_ROOT
    logger=logging.getLogger(__name__)
    paths=[]
    with SessionLocal() as db:
        try:
            x=db.get(Listing,lid)
            if not x or x.seller_id!=uid:return False,"草稿不存在或沒有權限"
            if x.status!="draft":return False,"只有草稿可以永久刪除"
            imgs=db.scalars(select(ListingImage).where(ListingImage.listing_id==lid)).all()
            paths=[PROJECT_ROOT/i.file_path for i in imgs]
            db.query(ListingImage).filter(ListingImage.listing_id==lid).delete(synchronize_session=False)
            db.query(Favorite).filter(Favorite.listing_id==lid).delete(synchronize_session=False)
            db.query(Appointment).filter(Appointment.listing_id==lid).delete(synchronize_session=False)
            db.query(Message).filter(Message.listing_id==lid).update({Message.listing_id:None},synchronize_session=False)
            db.flush()
            db.delete(x)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("[delete_draft] listing_id=%s failed",lid)
            return False,"草稿永久刪除失敗，請查看系統日誌"
    for path in paths:
        try:
            if path.exists():path.unlink()
        except OSError:
            logger.warning("[delete_draft] unable to remove file: %s",path,exc_info=True)
    folder=PROJECT_ROOT/"storage"/"uploads"/"listings"/str(lid)
    try:
        if folder.exists():shutil.rmtree(folder)
    except OSError:
        logger.warning("[delete_draft] unable to remove folder: %s",folder,exc_info=True)
    return True,"草稿已永久刪除"
def admin_force_remove(admin_uid,lid,reason):
    import shutil
    import logging
    from backend.database import PROJECT_ROOT
    logger=logging.getLogger(__name__)
    reason=str(reason or "").strip()
    if not reason:return False,"請填寫強制移除原因"
    paths=[]
    with SessionLocal() as db:
        try:
            admin=db.get(User,admin_uid);x=db.get(Listing,lid)
            if not admin or admin.role!="admin":return False,"沒有管理員權限"
            if not x:return False,"商品不存在"
            seller_id=x.seller_id;title=x.title
            imgs=db.scalars(select(ListingImage).where(ListingImage.listing_id==lid)).all()
            paths=[PROJECT_ROOT/i.file_path for i in imgs]
            db.add(Message(sender_id=admin_uid,receiver_id=seller_id,listing_id=None,subject="系統通知：商品已由管理員強制移除",body=f"您的商品 #{lid}「{title}」已由管理員強制移除。原因：{reason}。該商品已下架並永久刪除，不退還上架流量。",status="未讀"))
            db.query(ListingImage).filter(ListingImage.listing_id==lid).delete(synchronize_session=False)
            db.query(Favorite).filter(Favorite.listing_id==lid).delete(synchronize_session=False)
            db.query(Appointment).filter(Appointment.listing_id==lid).delete(synchronize_session=False)
            db.query(Message).filter(Message.listing_id==lid).update({Message.listing_id:None},synchronize_session=False)
            db.flush();db.delete(x);db.commit()
        except Exception:
            db.rollback();logger.exception("[admin_force_remove] listing_id=%s failed",lid)
            return False,"強制移除失敗，請查看系統日誌"
    for path in paths:
        try:
            if path.exists():path.unlink()
        except OSError:logger.warning("[admin_force_remove] unable to remove file: %s",path,exc_info=True)
    folder=PROJECT_ROOT/"storage"/"uploads"/"listings"/str(lid)
    try:
        if folder.exists():shutil.rmtree(folder)
    except OSError:logger.warning("[admin_force_remove] unable to remove folder: %s",folder,exc_info=True)
    return True,"商品已強制下架並永久刪除，系統通知已寄到賣家站內信箱"
def row_to_dict(x):
    d={c.name:getattr(x,c.name) for c in x.__table__.columns}
    with SessionLocal() as db:
        imgs=db.scalars(select(ListingImage).where(ListingImage.listing_id==x.id).order_by(ListingImage.sort_order,ListingImage.id)).all()
        d["images"]=[{"id":i.id,"file_path":i.file_path,"mime_type":i.mime_type,"sort_order":i.sort_order} for i in imgs]
        seller=db.get(User,x.seller_id)
        d["seller_name"]=seller.name if seller else "未知賣家"
        d["seller_email"]=seller.email if seller else ""
        d["seller_phone"]=seller.phone if seller else ""
        d["seller_default_meeting_address"]=seller.default_meeting_address if seller else ""
    return d
