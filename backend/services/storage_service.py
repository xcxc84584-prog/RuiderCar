from sqlalchemy import select,func
from backend.database import SessionLocal
from backend.models.entities import User,Listing,ListingImage,AdminAuditLog,IpAddressRecord
from backend.services.admin_service import settings
from backend.utils.timezone import utc_now
MB=1024*1024

def default_storage_limit_mb():
    try:return max(1,int(settings().get("default_storage_limit_mb","100")))
    except:return 100

def storage_usage_bytes(user_id):
    with SessionLocal() as db:
        value=db.scalar(select(func.coalesce(func.sum(func.length(ListingImage.image_data)),0)).join(Listing,Listing.id==ListingImage.listing_id).where(Listing.seller_id==int(user_id),ListingImage.image_data.is_not(None)))
        return int(value or 0)

def _account_whitelisted(db,user_id):
    suffix=f"(account:{int(user_id)})"
    return db.scalar(select(func.count(IpAddressRecord.ip_address)).where(IpAddressRecord.status=="whitelist",IpAddressRecord.ip_address.like(f"%{suffix}")))>0

def storage_status(user_id):
    with SessionLocal() as db:
        user=db.get(User,int(user_id))
        if not user:return {"used_bytes":0,"used_mb":0.0,"limit_mb":default_storage_limit_mb(),"unlimited":False,"custom":False}
        used=storage_usage_bytes(user.id)
        unlimited=user.role=="admin" or _account_whitelisted(db,user.id)
        limit=None if unlimited else default_storage_limit_mb()
        return {"used_bytes":used,"used_mb":round(used/MB,2),"limit_mb":limit,"unlimited":unlimited,"custom":False}

def admin_set_account_storage_limit(admin_uid,user_id,limit_mb=None):
    with SessionLocal() as db:
        admin=db.get(User,int(admin_uid));user=db.get(User,int(user_id))
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        if not user:return False,"帳號不存在"
        if user.role=="admin":return False,"Administrator 為 Unlimited，不需要設定資料量限制"
        if limit_mb is not None:
            try:limit_mb=int(limit_mb)
            except:return False,"請輸入有效的 MB 數值"
            if limit_mb<1 or limit_mb>102400:return False,"資料量限制必須介於 1 到 102400 MB"
        user.custom_storage_limit_mb=limit_mb
        db.add(AdminAuditLog(admin_id=admin.id,action="ACCOUNT_STORAGE_LIMIT",target_type="user",target_id=user.id,detail=(f"custom_storage_limit_mb={limit_mb}" if limit_mb is not None else "default_storage_limit"),created_at=utc_now()))
        db.commit()
        return True,(f"Account #{user.id} 資料量限制已設為 {limit_mb} MB" if limit_mb is not None else f"Account #{user.id} 已恢復全站預設資料量限制")

def storage_precheck(user_id,incoming_bytes):
    st=storage_status(user_id)
    if st["unlimited"]:return True,st
    st["incoming_bytes"]=int(incoming_bytes);st["projected_bytes"]=st["used_bytes"]+int(incoming_bytes)
    return st["projected_bytes"]<=st["limit_mb"]*MB,st

def delete_oldest_images_to_fit(user_id,incoming_bytes):
    st=storage_status(user_id)
    if st["unlimited"]:return True,0
    target=max(0,st["used_bytes"]+int(incoming_bytes)-st["limit_mb"]*MB)
    if target<=0:return True,0
    removed=0
    with SessionLocal() as db:
        rows=db.execute(select(ListingImage,Listing).join(Listing,Listing.id==ListingImage.listing_id).where(Listing.seller_id==int(user_id)).order_by(ListingImage.created_at.asc(),ListingImage.id.asc())).all()
        for img,listing in rows:
            size=len(img.image_data or b"")
            db.delete(img);removed+=size
            if removed>=target:break
        if removed<target:db.rollback();return False,0
        db.commit()
    return True,removed
