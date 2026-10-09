import streamlit as st
from backend.services.favorite_service import favorites,toggle_favorite
from backend.services.listing_service import get_listing
from frontend.components.cards import vehicle_card
from frontend.auth_session import guest_favorite_ids,toggle_guest_favorite
def render():
    u=st.session_state.get("user")
    st.title("我的收藏")
    if u:
        rows=favorites(u["id"])
    else:
        rows=[]
        for lid in guest_favorite_ids():
            x=get_listing(lid)
            if x and x.get("status")=="active":rows.append(x)
        st.caption("遊客收藏儲存在目前瀏覽器的本機 Cookie；清除網站資料或更換瀏覽器／裝置後不會同步。登入後會自動合併至會員收藏。")
    if not rows:st.info("目前沒有收藏商品。");return
    cols=st.columns(3)
    for i,x in enumerate(rows):
        with cols[i%3]:
            if vehicle_card(x,show_image=True):
                st.session_state.selected_listing=x["id"];st.session_state.page="商品詳細";st.rerun()
            if st.button("取消收藏",key=f'fav_remove_{x["id"]}',width="stretch"):
                if u:toggle_favorite(u["id"],x["id"])
                else:toggle_guest_favorite(x["id"])
                st.rerun()
