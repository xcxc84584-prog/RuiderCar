import csv,io,ipaddress
from datetime import timedelta
from sqlalchemy import select,func,delete,text
from backend.database import SessionLocal
from backend.models.entities import IpAddressRecord,IpActivityLog,User
from backend.models.session import LoginSession
from backend.services.admin_service import settings
from backend.utils.timezone import utc_now,taipei_now,to_taipei,taipei_text

def normalize_ip(value):
    raw=str(value or "").strip()
    if not raw:return "unknown"
    try:
        addr=ipaddress.ip_address(raw)
        if isinstance(addr,ipaddress.IPv6Address) and addr.ipv4_mapped:return str(addr.ipv4_mapped)
        return str(addr)
    except ValueError:return "unknown"

def client_ip_from_streamlit(st):
    try:
        direct=getattr(st.context,"ip_address",None)
        if direct and normalize_ip(direct)!="unknown":return normalize_ip(direct)
    except Exception:pass
    try:
        h=st.context.headers
        for key in ("X-Forwarded-For","X-Real-Ip"):
            raw=h.get(key) if hasattr(h,"get") else None
            if raw:
                candidate=str(raw).split(",")[0].strip()
                if normalize_ip(candidate)!="unknown":return normalize_ip(candidate)
    except Exception:pass
    return "unknown"

def _ints():
    s=settings()
    def val(k,d,lo=1,hi=1000000):
        try:return max(lo,min(hi,int(s.get(k,d))))
        except:return d
    return val("ip_request_limit_per_minute",180),val("active_ip_limit",50),val("ip_log_retention_days",7)

def cleanup_old_logs():
    _,_,days=_ints();cut=utc_now()-timedelta(days=days)
    with SessionLocal() as db:
        db.execute(delete(IpActivityLog).where(IpActivityLog.created_at<cut));db.commit()

def _revoke_ip_sessions(db,ip):db.execute(delete(LoginSession).where(LoginSession.ip_address==ip))

def _visit_log_due(db,ip,now):
    last=db.scalar(select(func.max(IpActivityLog.created_at)).where(IpActivityLog.ip_address==ip,IpActivityLog.event=="VISIT"))
    return last is None or (now-last)>=timedelta(seconds=30)

def touch_ip(ip,user_id=None):
    ip=normalize_ip(ip);now=utc_now();rate_limit,active_limit,_=_ints()
    if ip=="unknown":return {"allowed":True,"status":"unknown","queue_position":0,"rate":0}
    with SessionLocal() as db:
        if db.bind.dialect.name=="postgresql":db.execute(text("SELECT pg_advisory_xact_lock(728201)"))
        rec=db.get(IpAddressRecord,ip)
        if not rec:
            rec=IpAddressRecord(ip_address=ip,status="normal",first_seen=now,last_seen=now,rate_window_started=now,rate_window_count=0);db.add(rec);db.flush()
        if rec.status=="greylist" and rec.greylisted_until and rec.greylisted_until<=now:
            rec.status="normal";rec.greylisted_until=None;rec.status_reason="";rec.queued_at=None
            db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="GREYLIST_EXPIRED",created_at=now))
        if rec.status=="blacklist":
            rec.last_seen=now;db.commit();return {"allowed":False,"status":"blacklist","queue_position":0,"rate":0}
        if rec.status=="greylist" and rec.greylisted_until and rec.greylisted_until>now:
            rec.last_seen=now;db.commit();return {"allowed":False,"status":"greylist","until":rec.greylisted_until,"reason":rec.status_reason,"queue_position":0,"rate":0}
        if not rec.rate_window_started or now-rec.rate_window_started>=timedelta(minutes=1):rec.rate_window_started=now;rec.rate_window_count=0
        rec.rate_window_count=(rec.rate_window_count or 0)+1;rate=rec.rate_window_count
        rec.request_count=(rec.request_count or 0)+1;rec.peak_requests_per_minute=max(rec.peak_requests_per_minute or 0,rate);rec.last_seen=now
        if rate>rate_limit:
            rec.status="greylist";rec.greylisted_until=now+timedelta(minutes=30);rec.status_reason=f"超過 {rate_limit} requests/min";rec.queued_at=None
            _revoke_ip_sessions(db,ip);db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="GREYLIST",detail=rec.status_reason,created_at=now));db.commit()
            return {"allowed":False,"status":"greylist","until":rec.greylisted_until,"reason":rec.status_reason,"queue_position":0,"rate":rate}
        if rec.status!="whitelist":
            active_cut=now-timedelta(minutes=5)
            active=db.scalar(select(func.count(IpAddressRecord.ip_address)).where(IpAddressRecord.ip_address!=ip,IpAddressRecord.status.in_(["normal"]),IpAddressRecord.last_seen>=active_cut,IpAddressRecord.queued_at.is_(None))) or 0
            if rec.queued_at is not None or active>=active_limit:
                if rec.queued_at is None:rec.queued_at=now;db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="QUEUE_ENTER",created_at=now));db.flush()
                ahead=db.scalar(select(func.count(IpAddressRecord.ip_address)).where(IpAddressRecord.queued_at.is_not(None),IpAddressRecord.queued_at<rec.queued_at)) or 0
                if active<active_limit and ahead==0:rec.queued_at=None;db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="QUEUE_ADMIT",created_at=now))
                else:db.commit();return {"allowed":False,"status":"queue","queue_position":int(ahead)+1,"rate":rate}
        if _visit_log_due(db,ip,now):db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="VISIT",created_at=now))
        db.commit();return {"allowed":True,"status":rec.status,"queue_position":0,"rate":rate}

def admin_ip_rows(admin_uid,keyword="",status="all",limit=300):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return []
        xs=db.scalars(select(IpAddressRecord).order_by(IpAddressRecord.last_seen.desc()).limit(max(1,min(limit,1000)))).all();now=utc_now();out=[]
        for x in xs:
            if keyword and keyword not in x.ip_address:continue
            shown=x.status
            if shown=="greylist" and x.greylisted_until and x.greylisted_until<=now:shown="normal"
            if status!="all" and shown!=status:continue
            rate=x.rate_window_count or 0
            if not x.rate_window_started or now-x.rate_window_started>=timedelta(minutes=1):rate=0
            out.append({"ip":x.ip_address,"status":shown,"first_seen":to_taipei(x.first_seen),"last_seen":to_taipei(x.last_seen),"requests/min":rate,"peak":x.peak_requests_per_minute or 0,"request_count":x.request_count or 0,"reason":x.status_reason or "","greylisted_until":to_taipei(x.greylisted_until),"queued_at":to_taipei(x.queued_at)})
        return out

def admin_set_ip_status(admin_uid,ip,status):
    if status not in ("normal","whitelist","blacklist"):return False,"不支援的狀態"
    ip=normalize_ip(ip)
    with SessionLocal() as db:
        admin=db.get(User,admin_uid);rec=db.get(IpAddressRecord,ip)
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        if not rec:return False,"IP 不存在"
        rec.status=status;rec.greylisted_until=None;rec.queued_at=None;rec.status_reason="管理員設定" if status!="normal" else ""
        if status=="blacklist":_revoke_ip_sessions(db,ip)
        db.add(IpActivityLog(ip_address=ip,user_id=admin_uid,event=f"ADMIN_{status.upper()}",created_at=utc_now()));db.commit();return True,f"{ip} 已設定為 {status}"

def ip_history(admin_uid,ip,limit=100):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return []
        xs=db.scalars(select(IpActivityLog).where(IpActivityLog.ip_address==normalize_ip(ip)).order_by(IpActivityLog.created_at.desc()).limit(limit)).all()
        return [{"時間":taipei_text(x.created_at),"事件":x.event,"User ID":x.user_id,"說明":x.detail} for x in xs]

def export_ip_log_csv(admin_uid):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return "RuiderCar_IP_Log.csv",b""
        xs=db.scalars(select(IpActivityLog).order_by(IpActivityLog.created_at.desc())).all();out=io.StringIO();w=csv.writer(out);w.writerow(["Timestamp (Asia/Taipei)","IP","UserID","Event","Detail"])
        for x in xs:w.writerow([taipei_text(x.created_at),x.ip_address,x.user_id or "",x.event,x.detail])
        return f'RuiderCar_IP_Log_{taipei_now().strftime("%Y%m%d_%H%M%S")}.csv',out.getvalue().encode("utf-8-sig")
