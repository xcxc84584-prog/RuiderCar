from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import SystemSetting

DEFAULTS={
    "initial_traffic":"1000",
    "category_coefficient":"0.001",
    "category_minimum":"300",
    "admin_email":"xcxc84584@gmail.com",
    "bank_name":"",
    "bank_holder":"",
    "transfer_account":"",
    "transfer_note":"轉帳後請於流量中心提交金額與匯款帳號末五碼，待管理員審核。"
}
def seed_settings():
    with SessionLocal() as db:
        for k,v in DEFAULTS.items():
            if not db.get(SystemSetting,k):db.add(SystemSetting(key=k,value=v))
        db.commit()
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
