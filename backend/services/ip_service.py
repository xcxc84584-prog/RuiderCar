import csv,io,ipaddress,secrets
from datetime import timedelta
from sqlalchemy import select,func,delete,text
from backend.database import SessionLocal
from backend.models.entities import IpAddressRecord,IpActivityLog,User,Listing,ListingImage
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

def client_identity(ip,user_id=None,guest_id=None):
    base=normalize_ip(ip)
    if user_id is not None:
        return f"{base}(account:{int(user_id)})"
    gid=str(guest_id or "guest")[:16]
    return f"{base}(guest:{gid})"

def identity_base_ip(value):
    raw=str(value or "")
    return normalize_ip(raw.split("(",1)[0])

def normalize_identity(value):
    raw=str(value or "").strip()
    if "(" in raw and raw.endswith(")"):
        base,suffix=raw.split("(",1)
        base=normalize_ip(base)
        return f"{base}({suffix}" if base!="unknown" else "unknown"
    return normalize_ip(raw)

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
        db.execute(delete(IpActivityLog).where(IpActivityLog.created_at<cut,IpActivityLog.event!="GREYLIST"));db.commit()

def _revoke_ip_sessions(db,ip):db.execute(delete(LoginSession).where(LoginSession.ip_address==ip))

def _visit_log_due(db,ip,now):
    last=db.scalar(select(func.max(IpActivityLog.created_at)).where(IpActivityLog.ip_address==ip,IpActivityLog.event=="VISIT"))
    return last is None or (now-last)>=timedelta(seconds=30)

def ip_security_capability(ip):
    identity=str(ip or "")
    base=identity_base_ip(identity)
    if base=="unknown":return {"usable":False,"reason":"無法取得 Client IP"}
    try:
        addr=ipaddress.ip_address(base)
        if addr.is_loopback:
            if "(account:" in identity or "(guest:" in identity:return {"usable":True,"reason":"Streamlit Cloud localhost fallback：以 IP + Account/Guest ID 區分用戶（非真實 Public IP）"}
            return {"usable":False,"reason":"目前只取得 Streamlit/Proxy localhost，缺少帳號/訪客識別"}
        if addr.is_unspecified:return {"usable":False,"reason":"取得 unspecified IP"}
        return {"usable":True,"reason":"以 IP + Account/Guest ID 作為應用層識別；不等同 CDN/WAF 級真實來源驗證"}
    except ValueError:return {"usable":False,"reason":"IP 格式無效"}

def touch_ip(ip,user_id=None):
    ip=normalize_identity(ip);now=utc_now();rate_limit,active_limit,_=_ints();cap=ip_security_capability(ip)
    if ip=="unknown":return {"allowed":True,"status":"unknown","queue_position":0,"rate":0,"security_usable":False,"security_reason":cap["reason"]}
    with SessionLocal() as db:
        if db.bind.dialect.name=="postgresql":db.execute(text("SELECT pg_advisory_xact_lock(728201)"))
        rec=db.get(IpAddressRecord,ip)
        if not rec:
            rec=IpAddressRecord(ip_address=ip,status="normal",first_seen=now,last_seen=now,rate_window_started=now,rate_window_count=0);db.add(rec);db.flush()
        if rec.status=="greylist" and rec.greylisted_until and rec.greylisted_until<=now:
            rec.status="normal";rec.greylisted_until=None;rec.status_reason="";rec.queued_at=None
            db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="GREYLIST_EXPIRED",created_at=now))
        if cap["usable"] and rec.status=="blacklist":
            rec.last_seen=now;db.commit();return {"allowed":False,"status":"blacklist","queue_position":0,"rate":0}
        current_user=db.get(User,user_id) if user_id is not None else None
        admin_exempt=bool(current_user and current_user.role=="admin" and not current_user.suspended and not current_user.blacklisted and (current_user.account_status or "active")=="active")
        if admin_exempt and rec.status=="greylist":
            rec.status="normal";rec.greylisted_until=None;rec.status_reason="";rec.queued_at=None
            db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="ADMIN_RATE_EXEMPT",detail="Administrator automatic rate-limit exemption",created_at=now))
        if cap["usable"] and rec.status=="greylist" and rec.greylisted_until and rec.greylisted_until>now:
            rec.last_seen=now;db.commit();return {"allowed":False,"status":"greylist","until":rec.greylisted_until,"reason":rec.status_reason,"queue_position":0,"rate":0}
        if not rec.rate_window_started or now-rec.rate_window_started>=timedelta(minutes=1):rec.rate_window_started=now;rec.rate_window_count=0
        rec.rate_window_count=(rec.rate_window_count or 0)+1;rate=rec.rate_window_count
        rec.request_count=(rec.request_count or 0)+1;rec.peak_requests_per_minute=max(rec.peak_requests_per_minute or 0,rate);rec.last_seen=now
        if not cap["usable"]:
            if _visit_log_due(db,ip,now):db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="VISIT",detail="IP security safe mode",created_at=now))
            db.commit();return {"allowed":True,"status":"diagnostic","queue_position":0,"rate":rate,"security_usable":False,"security_reason":cap["reason"]}
        effective_rate_limit=rate_limit
        rate_exempt=admin_exempt or rec.status=="whitelist"
        if (not rate_exempt) and rate>effective_rate_limit:
            rec.status="greylist";rec.greylisted_until=now+timedelta(minutes=30);rec.status_reason=f"超過 {effective_rate_limit} requests/min";rec.queued_at=None
            _revoke_ip_sessions(db,ip);db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="GREYLIST",detail=rec.status_reason,created_at=now));db.commit()
            return {"allowed":False,"status":"greylist","until":rec.greylisted_until,"reason":rec.status_reason,"queue_position":0,"rate":rate}
        if not rate_exempt:
            active_cut=now-timedelta(minutes=5)
            active=db.scalar(select(func.count(IpAddressRecord.ip_address)).where(IpAddressRecord.ip_address!=ip,IpAddressRecord.status.in_(["normal"]),IpAddressRecord.last_seen>=active_cut,IpAddressRecord.queued_at.is_(None))) or 0
            if rec.queued_at is not None or active>=active_limit:
                if rec.queued_at is None:rec.queued_at=now;db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="QUEUE_ENTER",created_at=now));db.flush()
                ahead=db.scalar(select(func.count(IpAddressRecord.ip_address)).where(IpAddressRecord.queued_at.is_not(None),IpAddressRecord.queued_at<rec.queued_at)) or 0
                if active<active_limit and ahead==0:rec.queued_at=None;db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="QUEUE_ADMIT",created_at=now))
                else:db.commit();return {"allowed":False,"status":"queue","queue_position":int(ahead)+1,"rate":rate}
        if _visit_log_due(db,ip,now):db.add(IpActivityLog(ip_address=ip,user_id=user_id,event="VISIT",created_at=now))
        db.commit();return {"allowed":True,"status":rec.status,"queue_position":0,"rate":rate,"effective_limit":None if rate_exempt else effective_rate_limit,"custom_limit":False,"resource_exempt":rate_exempt}

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
            account_id=None
            try:
                if "(account:" in x.ip_address:account_id=int(x.ip_address.split("(account:",1)[1].rstrip(")"))
            except (TypeError,ValueError):account_id=None
            linked=db.get(User,account_id) if account_id is not None else None
            admin_exempt=bool(linked and linked.role=="admin")
            storage_used=0
            storage_limit=None
            storage_custom=False
            if linked:
                storage_used=int(db.scalar(select(func.coalesce(func.sum(func.length(ListingImage.image_data)),0)).join(Listing,Listing.id==ListingImage.listing_id).where(Listing.seller_id==linked.id,ListingImage.image_data.is_not(None))) or 0)
                storage_custom=linked.custom_storage_limit_mb is not None
                if not admin_exempt:
                    try:storage_limit=int(linked.custom_storage_limit_mb or settings().get("default_storage_limit_mb","100"))
                    except:storage_limit=100
            resource_exempt=admin_exempt or shown=="whitelist"
            out.append({"ip":x.ip_address,"status":shown,"first_seen":to_taipei(x.first_seen),"last_seen":to_taipei(x.last_seen),"requests/min":rate,"peak":x.peak_requests_per_minute or 0,"request_count":x.request_count or 0,"reason":x.status_reason or "","greylisted_until":to_taipei(x.greylisted_until),"queued_at":to_taipei(x.queued_at),"custom_request_limit":None,"effective_request_limit":None if resource_exempt else _ints()[0],"admin_exempt":admin_exempt,"resource_exempt":resource_exempt,"account_id":account_id,"storage_used_mb":round(storage_used/(1024*1024),2),"storage_limit_mb":None if resource_exempt else int(settings().get("default_storage_limit_mb","100")),"storage_custom":False})
        return out

def admin_set_ip_status(admin_uid,ip,status):
    if status not in ("normal","whitelist","blacklist"):return False,"不支援的狀態"
    ip=normalize_identity(ip)
    with SessionLocal() as db:
        admin=db.get(User,admin_uid);rec=db.get(IpAddressRecord,ip)
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        if not rec:return False,"IP 不存在"
        rec.status=status;rec.greylisted_until=None;rec.queued_at=None;rec.status_reason="管理員設定" if status!="normal" else ""
        if status=="blacklist":_revoke_ip_sessions(db,ip)
        db.add(IpActivityLog(ip_address=ip,user_id=admin_uid,event=f"ADMIN_{status.upper()}",created_at=utc_now()));db.commit();return True,f"{ip} 已設定為 {status}"

def admin_set_ip_request_limit(admin_uid,ip,limit=None):
    ip=normalize_identity(ip)
    with SessionLocal() as db:
        admin=db.get(User,admin_uid);rec=db.get(IpAddressRecord,ip)
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        if not rec:return False,"IP 不存在"
        if limit is not None:
            try:limit=int(limit)
            except (TypeError,ValueError):return False,"請輸入有效的 requests/min"
            if limit<1 or limit>1000000:return False,"自訂上限必須介於 1 到 1,000,000 requests/min"
        rec.custom_request_limit=limit
        detail=f"custom_request_limit={limit}" if limit is not None else "custom_request_limit=global_default"
        db.add(IpActivityLog(ip_address=ip,user_id=admin_uid,event="ADMIN_RATE_LIMIT",detail=detail,created_at=utc_now()));db.commit()
        return True,(f"{ip} 自訂流量上限已設為 {limit} requests/min" if limit is not None else f"{ip} 已恢復全站預設流量上限")

def ip_history(admin_uid,ip,limit=100):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return []
        xs=db.scalars(select(IpActivityLog).where(IpActivityLog.ip_address==normalize_identity(ip)).order_by(IpActivityLog.created_at.desc()).limit(limit)).all()
        return [{"ID":x.id,"時間":taipei_text(x.created_at),"事件":x.event,"User ID":x.user_id,"說明":x.detail} for x in xs]

def export_ip_log_csv(admin_uid):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return "RuiderCar_IP_Log.csv",b""
        xs=db.scalars(select(IpActivityLog).order_by(IpActivityLog.created_at.desc())).all();out=io.StringIO();w=csv.writer(out);w.writerow(["Timestamp (Asia/Taipei)","IP","UserID","Event","Detail"])
        for x in xs:w.writerow([taipei_text(x.created_at),x.ip_address,x.user_id or "",x.event,x.detail])
        return f'RuiderCar_IP_Log_{taipei_now().strftime("%Y%m%d_%H%M%S")}.csv',out.getvalue().encode("utf-8-sig")


def delete_ip_log(admin_uid,log_id):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid);row=db.get(IpActivityLog,int(log_id))
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        if not row:return False,"LOG 不存在"
        if row.event=="GREYLIST":return False,"灰名單歷史請在灰名單歷史區刪除"
        db.delete(row);db.commit();return True,"LOG 已刪除"

def delete_ip_logs_for_ip(admin_uid,ip,include_greylist=False):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        q=delete(IpActivityLog).where(IpActivityLog.ip_address==normalize_identity(ip))
        if not include_greylist:q=q.where(IpActivityLog.event!="GREYLIST")
        result=db.execute(q);db.commit();return True,f"已刪除 {result.rowcount or 0} 筆 LOG"

def clear_ip_logs(admin_uid):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        result=db.execute(delete(IpActivityLog).where(IpActivityLog.event!="GREYLIST"));db.commit();return True,f"已清除 {result.rowcount or 0} 筆一般 IP LOG"

def greylist_history_ips(admin_uid):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return []
        ips=db.scalars(select(IpActivityLog.ip_address).where(IpActivityLog.event=="GREYLIST").group_by(IpActivityLog.ip_address).order_by(func.max(IpActivityLog.created_at).desc())).all()
        out=[]
        for ip in ips:
            rows=db.scalars(select(IpActivityLog).where(IpActivityLog.ip_address==ip,IpActivityLog.event=="GREYLIST").order_by(IpActivityLog.created_at.desc())).all()
            if rows:out.append({"ip":ip,"count":len(rows),"latest":{"id":rows[0].id,"time":taipei_text(rows[0].created_at),"detail":rows[0].detail},"history":[{"id":x.id,"time":taipei_text(x.created_at),"detail":x.detail} for x in rows]})
        return out

def delete_greylist_history(admin_uid,log_id=None,ip=None):
    with SessionLocal() as db:
        admin=db.get(User,admin_uid)
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        if log_id is not None:q=delete(IpActivityLog).where(IpActivityLog.id==int(log_id),IpActivityLog.event=="GREYLIST")
        elif ip:q=delete(IpActivityLog).where(IpActivityLog.ip_address==normalize_identity(ip),IpActivityLog.event=="GREYLIST")
        else:return False,"缺少刪除目標"
        result=db.execute(q);db.commit();return True,f"已刪除 {result.rowcount or 0} 筆灰名單歷史"

def ip_diagnostics(ip):
    cap=ip_security_capability(ip)
    return {"ip":normalize_identity(ip),"source":"st.context.ip_address / Streamlit context","security_usable":cap["usable"],"reason":cap["reason"]}


def admin_delete_ip_records(admin_uid,ips):
    normalized=[]
    for ip in ips or []:
        x=normalize_identity(ip)
        if x not in normalized:normalized.append(x)
    if not normalized:return False,"沒有選取 IP Identity",0
    with SessionLocal() as db:
        admin=db.get(User,int(admin_uid))
        if not admin or admin.role!="admin":return False,"沒有管理員權限",0
        deleted=0
        for ip in normalized:
            rec=db.get(IpAddressRecord,ip)
            if not rec:continue
            db.execute(delete(IpActivityLog).where(IpActivityLog.ip_address==ip,IpActivityLog.event!="GREYLIST"))
            db.delete(rec);deleted+=1
        db.commit()
        return True,f"已刪除 {deleted} 個 IP Identity；灰名單歷史依保留規則未刪除",deleted

def publish_global_resource_limits(admin_uid):
    with SessionLocal() as db:
        admin=db.get(User,int(admin_uid))
        if not admin or admin.role!="admin":return False,"沒有管理員權限"
        db.execute(text("UPDATE ip_address_records SET custom_request_limit = NULL"))
        db.execute(text("UPDATE users SET custom_storage_limit_mb = NULL WHERE role <> 'admin'"))
        db.commit()
        return True,"全站 IP／資料量限制已統一發佈；僅 Administrator 與 Whitelist 豁免"
