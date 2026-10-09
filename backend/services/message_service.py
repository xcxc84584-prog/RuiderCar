from sqlalchemy import select,func
from backend.database import SessionLocal
from backend.models.entities import Message,AdminMessage,User
def _is_admin(db,uid):
    u=db.get(User,uid);return bool(u and u.role=="admin" and not u.suspended and not u.blacklisted and (u.account_status or "active")=="active")
def send(authenticated_uid,receiver,subject,body,listing_id=None):
    with SessionLocal() as db:
        sender=db.get(User,authenticated_uid);target=db.get(User,receiver)
        if not sender or sender.suspended or sender.blacklisted or (sender.account_status or "active")!="active":return False,"寄件者身分無效"
        if not target:return False,"收件者不存在"
        db.add(Message(sender_id=authenticated_uid,receiver_id=receiver,subject=subject,body=body,listing_id=listing_id));db.commit();return True,"訊息已送出"
def inbox(uid,keyword=""):
    with SessionLocal() as db:
        rows=db.execute(select(Message,User).join(User,User.id==Message.sender_id).where(Message.receiver_id==uid,Message.status!="無送達紀錄").order_by(Message.created_at.desc())).all();out=[];k=str(keyword or "").strip().lower()
        for m,u in rows:
            if k and k not in str(u.id).lower() and k not in u.email.lower() and k not in u.phone.lower():continue
            d={c.name:getattr(m,c.name) for c in m.__table__.columns};d.update({"sender_user_id":u.id,"sender_name":u.name,"sender_email":u.email,"sender_phone":u.phone});out.append(d)
        return out
def unread_count(uid):
    with SessionLocal() as db:
        return int(db.scalar(select(func.count(Message.id)).where(Message.receiver_id==uid,Message.status=="未讀")) or 0)

def set_message_status(uid,mid,status):
    if status not in ("未讀","已讀"):return False
    with SessionLocal() as db:
        x=db.get(Message,mid)
        if not x or x.receiver_id!=uid:return False
        x.status=status;db.commit();return True
def delete_message(uid,mid):
    with SessionLocal() as db:
        x=db.get(Message,mid)
        if not x or x.receiver_id!=uid:return False,"信件不存在或沒有權限"
        x.status="無送達紀錄";db.commit();return True,"信件已從你的信件區移除，狀態已改為「無送達紀錄」"
def quick_reply(uid,mid,body):
    body=(body or "").strip()
    if not body:return False,"回覆內容不可為空"
    with SessionLocal() as db:
        x=db.get(Message,mid)
        if not x or x.receiver_id!=uid:return False,"信件不存在或沒有權限"
        subject=x.subject if x.subject.startswith("Re:") else f"Re: {x.subject}"
        db.add(Message(sender_id=uid,receiver_id=x.sender_id,subject=subject,body=body,listing_id=x.listing_id,status="未讀"));x.status="已讀";db.commit();return True,"回覆已送出"
def send_admin(uid,category,subject,body):
    with SessionLocal() as db:db.add(AdminMessage(user_id=uid,category=category,subject=subject,body=body));db.commit()
def admin_messages(admin_uid):
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return []
        rows=db.execute(select(AdminMessage,User).join(User,User.id==AdminMessage.user_id).order_by(AdminMessage.created_at.desc())).all();out=[]
        for m,u in rows:
            d={c.name:getattr(m,c.name) for c in m.__table__.columns};d.update({"user_name":u.name,"user_email":u.email,"user_phone":u.phone});out.append(d)
        return out
def set_admin_message_status(admin_uid,mid,status):
    if status not in ("未讀","已讀","處理中","已回覆","已關閉"):return False
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return False
        x=db.get(AdminMessage,mid)
        if not x:return False
        x.status=status;db.commit();return True
def reply_admin(admin_uid,mid,text):
    text=(text or "").strip()
    if not text:return False
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return False
        x=db.get(AdminMessage,mid)
        if not x:return False
        x.reply=text;x.status="已回覆";db.commit();return True
def delete_messages(uid,mids):
    ids=[int(x) for x in mids if str(x).isdigit()]
    if not ids:return False,"請先選擇要刪除的信件"
    changed=0
    with SessionLocal() as db:
        for mid in ids:
            x=db.get(Message,mid)
            if x and x.receiver_id==uid:x.status="無送達紀錄";changed+=1
        db.commit()
    return True,f"已批量移除 {changed} 封信件；狀態已改為「無送達紀錄」"
def delete_admin_messages(admin_uid,mids):
    ids=[int(x) for x in mids if str(x).isdigit()]
    if not ids:return False,"請先選擇通知"
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return False,"沒有管理員權限"
        rows=db.scalars(select(AdminMessage).where(AdminMessage.id.in_(ids))).all()
        for x in rows:db.delete(x)
        db.commit();return True,f"已刪除 {len(rows)} 筆管理員通知"
def bulk_admin_message_status(admin_uid,mids,status):
    if status not in ("未讀","已讀","處理中","已回覆","已關閉"):return False,"狀態不正確"
    ids=[int(x) for x in mids if str(x).isdigit()]
    if not ids:return False,"請先選擇通知"
    with SessionLocal() as db:
        if not _is_admin(db,admin_uid):return False,"沒有管理員權限"
        rows=db.scalars(select(AdminMessage).where(AdminMessage.id.in_(ids))).all()
        for x in rows:x.status=status
        db.commit();return True,f"已更新 {len(rows)} 筆通知"
