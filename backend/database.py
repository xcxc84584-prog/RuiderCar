import os
from backend.cloud_config import secret
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
PROJECT_ROOT=Path(__file__).resolve().parent.parent
DATA_DIR=PROJECT_ROOT/"data"
DATA_DIR.mkdir(parents=True,exist_ok=True)
DATABASE_URL=secret("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_PATH=DATA_DIR/"vehicle_market.db"
    DATABASE_URL=f"sqlite:///{DATABASE_PATH.as_posix()}"
connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {}
engine=create_engine(DATABASE_URL,connect_args=connect_args,pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase):
    pass
def init_db():
    from backend.models.entities import User,Listing,ListingImage,Appointment,Message,AdminMessage,TrafficTransaction,TrafficPurchaseRequest,SystemSetting,RegistrationRisk
    from backend.models.session import LoginSession
    Base.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import inspect,text
        cols={c["name"] for c in inspect(engine).get_columns("listings")}
        additions={
            "published_at":"DATETIME",
            "expires_at":"DATETIME",
            "listing_time_fee":"INTEGER NOT NULL DEFAULT 0",
            "refunded_time_fee":"INTEGER NOT NULL DEFAULT 0"
        }
        with engine.begin() as conn:
            for name,ddl in additions.items():
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE listings ADD COLUMN {name} {ddl}"))
