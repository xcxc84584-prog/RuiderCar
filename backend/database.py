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
    from backend.models.entities import User,Listing,ListingImage,Favorite,Appointment,Message,AdminMessage,TrafficTransaction,TrafficPurchaseRequest,SystemSetting,RegistrationRisk
    from backend.models.session import LoginSession
    from sqlalchemy import inspect,text
    Base.metadata.create_all(engine)
    dialect=engine.dialect.name
    with engine.begin() as conn:
        if dialect=="postgresql":
            statements=[
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS blacklisted BOOLEAN NOT NULL DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS blacklist_reason TEXT NOT NULL DEFAULT ''",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS blacklisted_at TIMESTAMP NULL",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_hash VARCHAR(64) NOT NULL DEFAULT ''",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_expires_at TIMESTAMP NULL",
                 "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_sent_at TIMESTAMP NULL",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS default_meeting_address VARCHAR(250) NOT NULL DEFAULT ''",
                "ALTER TABLE listings ADD COLUMN IF NOT EXISTS product_type VARCHAR(20) NOT NULL DEFAULT 'vehicle'",
                "ALTER TABLE listing_images ADD COLUMN IF NOT EXISTS image_data BYTEA NULL",
                "ALTER TABLE listing_images ADD COLUMN IF NOT EXISTS mime_type VARCHAR(60) NOT NULL DEFAULT 'image/jpeg'"
            ]
            for sql in statements:conn.execute(text(sql))
        elif dialect=="sqlite":
            tables={"users":{c["name"] for c in inspect(engine).get_columns("users")}, "listings":{c["name"] for c in inspect(engine).get_columns("listings")},"listing_images":{c["name"] for c in inspect(engine).get_columns("listing_images")}}
            additions={
                "users":{"blacklisted":"BOOLEAN NOT NULL DEFAULT 0","blacklist_reason":"TEXT NOT NULL DEFAULT ''","blacklisted_at":"DATETIME","verification_code_hash":"VARCHAR(64) NOT NULL DEFAULT ''","verification_expires_at":"DATETIME","verification_sent_at":"DATETIME","default_meeting_address":"VARCHAR(250) NOT NULL DEFAULT ''"},
                "listings":{"published_at":"DATETIME","expires_at":"DATETIME","listing_time_fee":"INTEGER NOT NULL DEFAULT 0","refunded_time_fee":"INTEGER NOT NULL DEFAULT 0","product_type":"VARCHAR(20) NOT NULL DEFAULT 'vehicle'"},
                "listing_images":{"image_data":"BLOB","mime_type":"VARCHAR(60) NOT NULL DEFAULT 'image/jpeg'"}
            }
            for table,cols in additions.items():
                for name,ddl in cols.items():
                    if name not in tables[table]:conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
