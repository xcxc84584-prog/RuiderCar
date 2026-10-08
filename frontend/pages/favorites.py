import streamlit as st
from backend.services.favorite_service import favorites,toggle_favorite
from frontend.components.cards import vehicle_card
def render():
    u=st.session_state.get("user")
    if not u:st.warning("請先登入");return
    st.title("我的收藏")
    rows=favorites(u["id"])
    if not rows:st.info("目前沒有收藏商品。");return
    cols=st.columns(3)
    for i,x in enumerate(rows):
        with cols[i%3]:
            if vehicle_card(x,show_image=True):
                st.session_state.selected_listing=x["id"];st.session_state.page="商品詳細";st.rerun()
            if st.button("取消收藏",key=f'fav_remove_{x["id"]}',use_container_width=True):
                toggle_favorite(u["id"],x["id"]);st.rerun()
