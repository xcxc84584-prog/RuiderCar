from datetime import datetime
from sqlalchemy import String,Integer,Float,DateTime,Text,ForeignKey,Boolean,LargeBinary,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from backend.database import Base

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(80))
    email:Mapped[str]=mapped_column(String(180),unique=True,index=True)
    phone:Mapped[str]=mapped_column(String(30),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String(255))
    role:Mapped[str]=mapped_column(String(20),default="member")
    traffic_balance:Mapped[int]=mapped_column(Integer,default=0)
    verified:Mapped[bool]=mapped_column(Boolean,default=True)
    verification_code_hash:Mapped[str]=mapped_column(String(64),default="")
    verification_expires_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    verification_sent_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    suspended:Mapped[bool]=mapped_column(Boolean,default=False)
    blacklisted:Mapped[bool]=mapped_column(Boolean,default=False)
    blacklist_reason:Mapped[str]=mapped_column(Text,default="")
    blacklisted_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    default_meeting_address:Mapped[str]=mapped_column(String(250),default="")
    registration_type:Mapped[str]=mapped_column(String(20),default="normal",index=True)
    account_status:Mapped[str]=mapped_column(String(30),default="active",index=True)
    failed_login_attempts:Mapped[int]=mapped_column(Integer,default=0)
    login_locked_until:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    unread_mail_notifications:Mapped[bool]=mapped_column(Boolean,default=True)
    theme_preference:Mapped[str]=mapped_column(String(10),default="dark")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)


class Listing(Base):
    __tablename__="listings"
    id:Mapped[int]=mapped_column(primary_key=True)
    seller_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    product_type:Mapped[str]=mapped_column(String(20),default="vehicle",index=True)
    title:Mapped[str]=mapped_column(String(150))
    price:Mapped[int]=mapped_column(Integer)
    summary:Mapped[str]=mapped_column(String(300),default="")
    description:Mapped[str]=mapped_column(Text,default="")
    brand:Mapped[str]=mapped_column(String(80),default="")
    model:Mapped[str]=mapped_column(String(80),default="")
    year:Mapped[int]=mapped_column(Integer,default=2026)
    mileage:Mapped[int]=mapped_column(Integer,default=0)
    fuel:Mapped[str]=mapped_column(String(40),default="汽油")
    transmission:Mapped[str]=mapped_column(String(40),default="自排")
    location:Mapped[str]=mapped_column(String(100),default="")
    color:Mapped[str]=mapped_column(String(40),default="")
    body_type:Mapped[str]=mapped_column(String(40),default="轎車")
    delivery_time:Mapped[str]=mapped_column(String(100),default="")
    meeting_address:Mapped[str]=mapped_column(String(200),default="")
    payment_method:Mapped[str]=mapped_column(String(100),default="現金")
    accepts_loan:Mapped[bool]=mapped_column(Boolean,default=False)
    image_path:Mapped[str]=mapped_column(String(300),default="")
    status:Mapped[str]=mapped_column(String(30),default="draft")
    months:Mapped[int]=mapped_column(Integer,default=1)
    traffic_cost:Mapped[int]=mapped_column(Integer,default=0)
    published_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    expires_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    listing_time_fee:Mapped[int]=mapped_column(Integer,default=0)
    refunded_time_fee:Mapped[int]=mapped_column(Integer,default=0)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class ListingImage(Base):
    __tablename__="listing_images"
    id:Mapped[int]=mapped_column(primary_key=True)
    listing_id:Mapped[int]=mapped_column(ForeignKey("listings.id"),index=True)
    file_path:Mapped[str]=mapped_column(String(500),default="")
    image_data:Mapped[bytes|None]=mapped_column(LargeBinary,nullable=True)
    mime_type:Mapped[str]=mapped_column(String(60),default="image/jpeg")
    sort_order:Mapped[int]=mapped_column(Integer,default=1,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)


class Favorite(Base):
    __tablename__="favorites"
    __table_args__=(UniqueConstraint("user_id","listing_id",name="uq_favorite_user_listing"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    listing_id:Mapped[int]=mapped_column(ForeignKey("listings.id"),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Appointment(Base):
    __tablename__="appointments"
    id:Mapped[int]=mapped_column(primary_key=True)
    listing_id:Mapped[int]=mapped_column(ForeignKey("listings.id"))
    buyer_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    appointment_at:Mapped[datetime]=mapped_column(DateTime)
    status:Mapped[str]=mapped_column(String(30),default="等待確認")
    note:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Message(Base):
    __tablename__="messages"
    id:Mapped[int]=mapped_column(primary_key=True)
    sender_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    receiver_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    listing_id:Mapped[int|None]=mapped_column(ForeignKey("listings.id"),nullable=True)
    subject:Mapped[str]=mapped_column(String(150))
    body:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(30),default="未讀")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class AdminMessage(Base):
    __tablename__="admin_messages"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    category:Mapped[str]=mapped_column(String(40))
    subject:Mapped[str]=mapped_column(String(150))
    body:Mapped[str]=mapped_column(Text)
    reply:Mapped[str]=mapped_column(Text,default="")
    status:Mapped[str]=mapped_column(String(30),default="未讀")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class TrafficTransaction(Base):
    __tablename__="traffic_transactions"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    kind:Mapped[str]=mapped_column(String(50))
    delta:Mapped[int]=mapped_column(Integer)
    before_balance:Mapped[int]=mapped_column(Integer)
    after_balance:Mapped[int]=mapped_column(Integer)
    reason:Mapped[str]=mapped_column(String(250),default="")
    reference_id:Mapped[int|None]=mapped_column(Integer,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class TrafficPurchaseRequest(Base):
    __tablename__="traffic_purchase_requests"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    amount:Mapped[int]=mapped_column(Integer)
    last5:Mapped[str]=mapped_column(String(5))
    note:Mapped[str]=mapped_column(Text,default="")
    status:Mapped[str]=mapped_column(String(30),default="等待審核")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class SystemSetting(Base):
    __tablename__="system_settings"
    key:Mapped[str]=mapped_column(String(100),primary_key=True)
    value:Mapped[str]=mapped_column(Text)

class RegistrationRisk(Base):
    __tablename__="registration_risks"
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(180))
    phone:Mapped[str]=mapped_column(String(30))
    reason:Mapped[str]=mapped_column(String(250))
    status:Mapped[str]=mapped_column(String(30),default="待審核")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class AdminAuditLog(Base):
    __tablename__="admin_audit_logs"
    id:Mapped[int]=mapped_column(primary_key=True)
    admin_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    action:Mapped[str]=mapped_column(String(80),index=True)
    target_type:Mapped[str]=mapped_column(String(40),default="")
    target_id:Mapped[int|None]=mapped_column(Integer,nullable=True)
    detail:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
