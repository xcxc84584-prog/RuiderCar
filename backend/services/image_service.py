from pathlib import Path
from uuid import uuid4
from sqlalchemy import select
from backend.database import SessionLocal,PROJECT_ROOT
from backend.models.entities import Listing,ListingImage
UPLOAD_ROOT=PROJECT_ROOT/"storage"/"uploads"/"listings"
UPLOAD_ROOT.mkdir(parents=True,exist_ok=True)
ALLOWED_EXT={".jpg",".jpeg",".png",".webp"}
MIME={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}
MAX_IMAGES=10
MAX_IMAGE_BYTES=5*1024*1024
def _ext(name):
    x=Path(name or "").suffix.lower()
    return x if x in ALLOWED_EXT else None
def list_images(listing_id):
    with SessionLocal() as db:
        xs=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order,ListingImage.id)).all()
        return [{"id":x.id,"listing_id":x.listing_id,"file_path":x.file_path,"image_data":x.image_data,"mime_type":x.mime_type,"sort_order":x.sort_order} for x in xs]
def add_uploaded_images(uid,listing_id,uploads):
    uploads=list(uploads or [])
    if not uploads:return True,"沒有新增照片"
    with SessionLocal() as db:
        listing=db.get(Listing,listing_id)
        if not listing or listing.seller_id!=uid:return False,"商品不存在或沒有權限"
        old=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order)).all()
        if len(old)+len(uploads)>MAX_IMAGES:return False,f"每個商品最多 {MAX_IMAGES} 張照片"
        order=len(old)+1
        for up in uploads:
            ext=_ext(getattr(up,"name",""))
            if not ext:return False,"只允許 JPG、JPEG、PNG、WEBP"
            data=up.getvalue()
            if len(data)>MAX_IMAGE_BYTES:return False,"單張照片不可超過 5 MB"
            # PostgreSQL/Supabase is the durable source. file_path remains only for legacy compatibility.
            db.add(ListingImage(listing_id=listing_id,file_path="",image_data=data,mime_type=MIME[ext],sort_order=order))
            order+=1
        db.commit()
        return True,f"已新增 {len(uploads)} 張照片；照片已保存至持久化資料庫"
def delete_image(uid,image_id):
    with SessionLocal() as db:
        img=db.get(ListingImage,image_id)
        if not img:return False,"照片不存在"
        listing=db.get(Listing,img.listing_id)
        if not listing or listing.seller_id!=uid:return False,"沒有權限"
        if img.file_path:
            path=PROJECT_ROOT/img.file_path
            try:
                if path.exists():path.unlink()
            except OSError:pass
        lid=img.listing_id;db.delete(img);db.flush()
        xs=db.scalars(select(ListingImage).where(ListingImage.listing_id==lid).order_by(ListingImage.sort_order,ListingImage.id)).all()
        for i,x in enumerate(xs,1):x.sort_order=i
        db.commit();return True,"照片已刪除"
def move_image(uid,image_id,direction):
    with SessionLocal() as db:
        img=db.get(ListingImage,image_id)
        if not img:return False,"照片不存在"
        listing=db.get(Listing,img.listing_id)
        if not listing or listing.seller_id!=uid:return False,"沒有權限"
        xs=db.scalars(select(ListingImage).where(ListingImage.listing_id==img.listing_id).order_by(ListingImage.sort_order,ListingImage.id)).all()
        ids=[x.id for x in xs];i=ids.index(image_id);j=i+direction
        if j<0 or j>=len(xs):return False,"已在最前或最後"
        xs[i].sort_order,xs[j].sort_order=xs[j].sort_order,xs[i].sort_order
        db.commit();return True,"照片順序已更新"
def image_source(img):
    data=img.get("image_data")
    if data:return data
    image_id=img.get("id")
    if image_id:
        with SessionLocal() as db:
            row=db.get(ListingImage,image_id)
            if row and row.image_data:return row.image_data
            fp=(row.file_path if row else "") or img.get("file_path") or ""
    else:fp=img.get("file_path") or ""
    if fp:
        path=PROJECT_ROOT/fp
        if path.exists():return str(path)
    return None
