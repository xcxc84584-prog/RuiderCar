from sqlalchemy import select,text
import streamlit as st
from backend.database import SessionLocal
from backend.models.entities import SystemSetting,User,Listing,ListingImage,Appointment,Message,AdminMessage,TrafficTransaction,TrafficPurchaseRequest,RegistrationRisk
from backend.models.session import LoginSession
from datetime import datetime

DEFAULTS={
    "initial_traffic":"1000",
    "traffic_max":"100",
    "traffic_min":"20",
    "traffic_per_100k_month":"5",
    "admin_email":"xcxc84584@gmail.com",
    "bank_name":"",
    "bank_holder":"",
    "transfer_account":"",
    "transfer_note":"轉帳後請於流量中心提交金額與匯款帳號末五碼，待管理員審核。",
    "home_hero_title":"RuiderCar 商品交易平台",
    "home_hero_subtitle":"瀏覽車輛與常規商品、預約或聯絡賣家。平台不代替買賣雙方完成線下交易。",
    "home_hero_width":"100",
    "home_hero_height":"140",
    "home_hero_title_size":"26",
    "home_hero_subtitle_size":"16"
}
def seed_settings():
    with SessionLocal() as db:
        existing={x.key for x in db.scalars(select(SystemSetting)).all()}
        for k,v in DEFAULTS.items():
            if k not in existing:db.add(SystemSetting(key=k,value=v))
        db.commit()
@st.cache_data(ttl=60,show_spinner=False)
def settings():
    with SessionLocal() as db:
        xs=db.scalars(select(SystemSetting)).all()
        out=DEFAULTS.copy();out.update({x.key:x.value for x in xs});return out
def save_setting(key,value):
    with SessionLocal() as db:
        x=db.get(SystemSetting,key)
        if x:x.value=str(value)
        else:db.add(SystemSetting(key=key,value=str(value)))
        db.commit()
    settings.clear()

def ensure_blacklist_schema():
    with SessionLocal() as db:
        dialect=db.bind.dialect.name
        if dialect=="postgresql":
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blacklisted BOOLEAN NOT NULL DEFAULT FALSE"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blacklist_reason TEXT NOT NULL DEFAULT ''"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blacklisted_at TIMESTAMP NULL"))
        elif dialect=="sqlite":
            cols={r[1] for r in db.execute(text("PRAGMA table_info(users)")).all()}
            if "blacklisted" not in cols:db.execute(text("ALTER TABLE users ADD COLUMN blacklisted BOOLEAN NOT NULL DEFAULT 0"))
            if "blacklist_reason" not in cols:db.execute(text("ALTER TABLE users ADD COLUMN blacklist_reason TEXT NOT NULL DEFAULT ''"))
            if "blacklisted_at" not in cols:db.execute(text("ALTER TABLE users ADD COLUMN blacklisted_at DATETIME NULL"))
        db.commit()
def users_for_admin():
    with SessionLocal() as db:
        xs=db.scalars(select(User).order_by(User.created_at.desc())).all()
        out=[]
        for u in xs:
            deleted=(u.name=="已註銷會員" and u.email.startswith("deleted-") and u.email.endswith("@deleted.invalid"))
            out.append({"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role,"traffic_balance":u.traffic_balance,"blacklisted":bool(u.blacklisted),"blacklist_reason":u.blacklist_reason or "","blacklisted_at":u.blacklisted_at,"deleted":deleted,"created_at":u.created_at})
        return out
def blacklist_user(uid,reason):
    reason=str(reason or "").strip()
    if not reason:return False,"請填寫加入黑名單原因"
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u:return False,"會員不存在"
        if u.role=="admin":return False,"管理員帳號不可加入黑名單"
        if u.name=="已註銷會員" and u.email.startswith("deleted-") and u.email.endswith("@deleted.invalid"):return False,"已註銷帳戶不可加入黑名單"
        if u.blacklisted:return False,"此會員已在黑名單"
        u.blacklisted=True
        u.blacklist_reason=reason
        u.blacklisted_at=datetime.utcnow()
        u.suspended=True
        db.query(LoginSession).filter(LoginSession.user_id==uid).delete(synchronize_session=False)
        db.query(Listing).filter(Listing.seller_id==uid,Listing.status=="active").update({Listing.status:"draft",Listing.published_at:None,Listing.expires_at:None},synchronize_session=False)
        db.commit()
        return True,"已加入黑名單；登入工作階段已撤銷，公開商品已下架"
def unblacklist_user(uid):
    with SessionLocal() as db:
        u=db.get(User,uid)
        if not u:return False,"會員不存在"
        if u.role=="admin":return False,"管理員帳號不使用黑名單功能"
        if not u.blacklisted:return False,"此會員不在黑名單"
        u.blacklisted=False
        u.blacklist_reason=""
        u.blacklisted_at=None
        u.suspended=False
        db.commit()
        return True,"已解除黑名單，會員可重新登入"

def permanently_delete_user(admin_uid,target_uid):
    import shutil
    import logging
    from backend.database import PROJECT_ROOT
    logger=logging.getLogger(__name__)
    if admin_uid==target_uid:return False,"管理員不可徹底刪除自己的帳號"
    folders=[]
    with SessionLocal() as db:
        try:
            admin=db.get(User,admin_uid);u=db.get(User,target_uid)
            if not admin or admin.role!="admin":return False,"沒有管理員權限"
            if not u:return False,"會員不存在"
            if u.role=="admin":return False,"管理員帳號不可使用徹底刪除功能"
            listings=db.scalars(select(Listing).where(Listing.seller_id==target_uid)).all()
            listing_ids=[x.id for x in listings]
            if listing_ids:
                db.query(ListingImage).filter(ListingImage.listing_id.in_(listing_ids)).delete(synchronize_session=False)
                db.query(Appointment).filter(Appointment.listing_id.in_(listing_ids)).delete(synchronize_session=False)
                db.query(Message).filter(Message.listing_id.in_(listing_ids)).update({Message.listing_id:None},synchronize_session=False)
                for lid in listing_ids:folders.append(PROJECT_ROOT/"storage"/"uploads"/"listings"/str(lid))
                db.query(Listing).filter(Listing.id.in_(listing_ids)).delete(synchronize_session=False)
            db.query(Appointment).filter(Appointment.buyer_id==target_uid).delete(synchronize_session=False)
            db.query(Message).filter((Message.sender_id==target_uid)|(Message.receiver_id==target_uid)).delete(synchronize_session=False)
            db.query(AdminMessage).filter(AdminMessage.user_id==target_uid).delete(synchronize_session=False)
            db.query(TrafficTransaction).filter(TrafficTransaction.user_id==target_uid).delete(synchronize_session=False)
            db.query(TrafficPurchaseRequest).filter(TrafficPurchaseRequest.user_id==target_uid).delete(synchronize_session=False)
            db.query(LoginSession).filter(LoginSession.user_id==target_uid).delete(synchronize_session=False)
            db.query(RegistrationRisk).filter((RegistrationRisk.email==u.email)|(RegistrationRisk.phone==u.phone)).delete(synchronize_session=False)
            db.delete(u);db.commit()
        except Exception:
            db.rollback();logger.exception("[permanently_delete_user] user_id=%s failed",target_uid)
            return False,"徹底刪除失敗，請查看系統日誌"
    for folder in folders:
        try:
            if folder.exists():shutil.rmtree(folder)
        except OSError:logger.warning("[permanently_delete_user] unable to remove folder: %s",folder,exc_info=True)
    return True,"帳號及其平台關聯資料已徹底刪除"
