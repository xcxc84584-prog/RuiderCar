from pathlib import Path
from uuid import uuid4
from sqlalchemy import select,delete
from backend.database import SessionLocal,PROJECT_ROOT
from backend.models.entities import Listing,ListingImage
UPLOAD_ROOT=PROJECT_ROOT/"storage"/"uploads"/"listings"
UPLOAD_ROOT.mkdir(parents=True,exist_ok=True)
ALLOWED_EXT={".jpg",".jpeg",".png",".webp"}
MAX_IMAGES=10
def _ext(name):
    x=Path(name or "").suffix.lower()
    return x if x in ALLOWED_EXT else None
def list_images(listing_id):
    with SessionLocal() as db:
        xs=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order,ListingImage.id)).all()
        return [{"id":x.id,"listing_id":x.listing_id,"file_path":x.file_path,"sort_order":x.sort_order} for x in xs]
def add_uploaded_images(uid,listing_id,uploads):
    uploads=list(uploads or [])
    if not uploads:return True,"沒有新增照片"
    with SessionLocal() as db:
        listing=db.get(Listing,listing_id)
        if not listing or listing.seller_id!=uid:return False,"商品不存在或沒有權限"
        old=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order)).all()
        if len(old)+len(uploads)>MAX_IMAGES:return False,f"每個商品最多 {MAX_IMAGES} 張照片"
        folder=UPLOAD_ROOT/str(listing_id);folder.mkdir(parents=True,exist_ok=True)
        order=len(old)+1
        for up in uploads:
            ext=_ext(getattr(up,"name",""))
            if not ext:return False,"只允許 JPG、JPEG、PNG、WEBP"
            filename=f"{uuid4().hex}{ext}"
            path=folder/filename
            path.write_bytes(up.getvalue())
            rel=path.relative_to(PROJECT_ROOT).as_posix()
            db.add(ListingImage(listing_id=listing_id,file_path=rel,sort_order=order))
            order+=1
        db.commit()
        return True,f"已新增 {len(uploads)} 張照片"
def delete_image(uid,image_id):
    with SessionLocal() as db:
        img=db.get(ListingImage,image_id)
        if not img:return False,"照片不存在"
        listing=db.get(Listing,img.listing_id)
        if not listing or listing.seller_id!=uid:return False,"沒有權限"
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
def cover_path(listing_id):
    xs=list_images(listing_id)
    return str(PROJECT_ROOT/xs[0]["file_path"]) if xs else None
