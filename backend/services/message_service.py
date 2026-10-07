from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import Message,AdminMessage,User

def send(sender,receiver,subject,body,listing_id=None):
    with SessionLocal() as db:
        db.add(Message(sender_id=sender,receiver_id=receiver,subject=subject,body=body,listing_id=listing_id))
        db.commit()

def inbox(uid):
    with SessionLocal() as db:
        rows=db.execute(
            select(Message,User)
            .join(User,User.id==Message.sender_id)
            .where(Message.receiver_id==uid)
            .order_by(Message.created_at.desc())
        ).all()
        out=[]
        for m,u in rows:
            d={c.name:getattr(m,c.name) for c in m.__table__.columns}
            d.update({"sender_name":u.name,"sender_email":u.email,"sender_phone":u.phone})
            out.append(d)
        return out

def set_message_status(uid,mid,status):
    if status not in ("未讀","已讀"):return False
    with SessionLocal() as db:
        x=db.get(Message,mid)
        if not x or x.receiver_id!=uid:return False
        x.status=status;db.commit();return True

def quick_reply(uid,mid,body):
    body=(body or "").strip()
    if not body:return False,"回覆內容不可為空"
    with SessionLocal() as db:
        x=db.get(Message,mid)
        if not x or x.receiver_id!=uid:return False,"信件不存在或沒有權限"
        subject=x.subject if x.subject.startswith("Re:") else f"Re: {x.subject}"
        db.add(Message(sender_id=uid,receiver_id=x.sender_id,subject=subject,body=body,listing_id=x.listing_id,status="未讀"))
        x.status="已讀"
        db.commit()
        return True,"回覆已送出"

def send_admin(uid,category,subject,body):
    with SessionLocal() as db:
        db.add(AdminMessage(user_id=uid,category=category,subject=subject,body=body));db.commit()

def admin_messages():
    with SessionLocal() as db:
        rows=db.execute(
            select(AdminMessage,User)
            .join(User,User.id==AdminMessage.user_id)
            .order_by(AdminMessage.created_at.desc())
        ).all()
        out=[]
        for m,u in rows:
            d={c.name:getattr(m,c.name) for c in m.__table__.columns}
            d.update({"user_name":u.name,"user_email":u.email,"user_phone":u.phone})
            out.append(d)
        return out

def set_admin_message_status(mid,status):
    if status not in ("未讀","已讀","處理中","已回覆","已關閉"):return False
    with SessionLocal() as db:
        x=db.get(AdminMessage,mid)
        if not x:return False
        x.status=status;db.commit();return True

def reply_admin(mid,text):
    text=(text or "").strip()
    if not text:return False
    with SessionLocal() as db:
        x=db.get(AdminMessage,mid)
        if not x:return False
        x.reply=text;x.status="已回覆";db.commit();return True
