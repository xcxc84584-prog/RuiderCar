from pathlib import Path
from uuid import uuid4
from functools import lru_cache
from io import BytesIO
from PIL import Image,ImageOps
from sqlalchemy import select
from backend.database import SessionLocal,PROJECT_ROOT
from backend.models.entities import Listing,ListingImage
from backend.services.storage_service import storage_precheck,delete_oldest_images_to_fit
UPLOAD_ROOT=PROJECT_ROOT/"storage"/"uploads"/"listings"
UPLOAD_ROOT.mkdir(parents=True,exist_ok=True)
ALLOWED_EXT={".jpg",".jpeg",".png",".webp"}
MIME={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}
MAX_IMAGES=10
MAX_IMAGE_BYTES=5*1024*1024
MAX_IMAGE_PIXELS=24_000_000
DETAIL_MAX_EDGE=1600
DETAIL_WEBP_QUALITY=82

def _compress_upload(data):
    try:
        with Image.open(BytesIO(data)) as im:
            im.verify()
        with Image.open(BytesIO(data)) as im:
            im=ImageOps.exif_transpose(im)
            if im.width*im.height>MAX_IMAGE_PIXELS:
                return None,"圖片解析度過高"
            if im.mode not in ("RGB","RGBA"):
                im=im.convert("RGBA" if "A" in im.getbands() else "RGB")
            im.thumbnail((DETAIL_MAX_EDGE,DETAIL_MAX_EDGE),Image.Resampling.LANCZOS)
            if im.mode=="RGBA":
                bg=Image.new("RGB",im.size,(255,255,255));bg.paste(im,mask=im.getchannel("A"));im=bg
            out=BytesIO();im.save(out,format="WEBP",quality=DETAIL_WEBP_QUALITY,method=4,optimize=True)
            return out.getvalue(),None
    except Exception:
        return None,"圖片內容無法解析或格式不正確"

def _ext(name):
    x=Path(name or "").suffix.lower()
    return x if x in ALLOWED_EXT else None
def list_images(listing_id):
    with SessionLocal() as db:
        xs=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order,ListingImage.id)).all()
        return [{"id":x.id,"listing_id":x.listing_id,"file_path":x.file_path,"image_data":x.image_data,"mime_type":x.mime_type,"sort_order":x.sort_order} for x in xs]
def add_uploaded_images(uid,listing_id,uploads,overwrite_oldest=False):
    uploads=list(uploads or [])
    if not uploads:return True,"沒有新增照片"
    with SessionLocal() as db:
        listing=db.get(Listing,listing_id)
        if not listing or listing.seller_id!=uid:return False,"商品不存在或沒有權限"
        old=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order)).all()
        if len(old)+len(uploads)>MAX_IMAGES:return False,f"每個商品最多 {MAX_IMAGES} 張照片"
        prepared=[]
        for up in uploads:
            ext=_ext(getattr(up,"name",""))
            if not ext:return False,"只允許 JPG、JPEG、PNG、WEBP"
            data=up.getvalue()
            if len(data)>MAX_IMAGE_BYTES:return False,"單張照片不可超過 5 MB"
            compressed,error=_compress_upload(data)
            if error:return False,error
            prepared.append((".webp",compressed))
        incoming=sum(len(data) for _,data in prepared)
        fits,quota=storage_precheck(uid,incoming)
        if not fits:
            if not overwrite_oldest:
                return False,f'STORAGE_LIMIT|目前 {quota["used_mb"]:.2f} MB / {quota["limit_mb"]} MB；本次新增 {incoming/(1024*1024):.2f} MB'
            ok,removed=delete_oldest_images_to_fit(uid,incoming)
            if not ok:return False,"沒有足夠的可刪除舊圖片來騰出空間"
            old=db.scalars(select(ListingImage).where(ListingImage.listing_id==listing_id).order_by(ListingImage.sort_order)).all()
        order=len(old)+1
        for ext,data in prepared:
            # PostgreSQL/Supabase is the durable source. file_path remains only for legacy compatibility.
            db.add(ListingImage(listing_id=listing_id,file_path="",image_data=data,mime_type=MIME[ext],sort_order=order))
            order+=1
        db.commit()
        return True,f"已新增 {len(uploads)} 張照片；圖片已壓縮為 WEBP 並保存至持久化資料庫"
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
@lru_cache(maxsize=256)
def _cached_image_data(image_id):
    with SessionLocal() as db:
        row=db.get(ListingImage,image_id)
        if row and row.image_data:return row.image_data
        return None

@lru_cache(maxsize=256)
def _cached_cover_data(image_id):
    data=_cached_image_data(int(image_id))
    if not data:return None
    try:
        with Image.open(BytesIO(data)) as im:
            im=ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((640,640),Image.Resampling.LANCZOS)
            out=BytesIO();im.save(out,format="WEBP",quality=72,method=3,optimize=True)
            return out.getvalue()
    except Exception:return data
def cover_source(img):
    image_id=img.get("id")
    if image_id:
        data=_cached_cover_data(int(image_id))
        if data:return data
    return image_source(img)

def image_source(img):
    data=img.get("image_data")
    if data:return data
    image_id=img.get("id")
    if image_id:
        data=_cached_image_data(int(image_id))
        if data:return data
        with SessionLocal() as db:
            row=db.get(ListingImage,image_id)
            fp=(row.file_path if row else "") or img.get("file_path") or ""
    else:fp=img.get("file_path") or ""
    if fp:
        path=PROJECT_ROOT/fp
        if path.exists():return str(path)
    return None
