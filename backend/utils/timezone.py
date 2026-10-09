from datetime import datetime,timezone
from zoneinfo import ZoneInfo
TAIPEI=ZoneInfo("Asia/Taipei")
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
def taipei_now():
    return datetime.now(TAIPEI).replace(tzinfo=None)
def to_taipei(value):
    if value is None:return None
    if value.tzinfo is None:value=value.replace(tzinfo=timezone.utc)
    return value.astimezone(TAIPEI).replace(tzinfo=None)
def taipei_text(value,fmt="%Y-%m-%d %H:%M:%S"):
    v=to_taipei(value)
    return v.strftime(fmt) if v else ""
