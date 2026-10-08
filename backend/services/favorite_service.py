from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.entities import Favorite,Listing
from backend.services.listing_service import row_to_dict
def is_favorite(uid,lid):
    with SessionLocal() as db:return db.scalar(select(Favorite.id).where(Favorite.user_id==uid,Favorite.listing_id==lid)) is not None
def toggle_favorite(uid,lid):
    with SessionLocal() as db:
        listing=db.get(Listing,lid)
        if not listing or listing.status!="active":return False,"商品目前無法收藏",False
        x=db.scalar(select(Favorite).where(Favorite.user_id==uid,Favorite.listing_id==lid))
        if x:
            db.delete(x);db.commit();return True,"已取消收藏",False
        db.add(Favorite(user_id=uid,listing_id=lid));db.commit();return True,"已加入收藏",True
def favorites(uid):
    with SessionLocal() as db:
        xs=db.execute(select(Favorite,Listing).join(Listing,Listing.id==Favorite.listing_id).where(Favorite.user_id==uid,Listing.status=="active").order_by(Favorite.created_at.desc())).all()
        return [row_to_dict(l) for _,l in xs]
