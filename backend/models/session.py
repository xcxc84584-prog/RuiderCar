from datetime import datetime
from sqlalchemy import String,Integer,DateTime,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column
from backend.database import Base
class LoginSession(Base):
    __tablename__="login_sessions"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    expires_at:Mapped[datetime]=mapped_column(DateTime,index=True)
