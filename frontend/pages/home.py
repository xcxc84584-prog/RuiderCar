import streamlit as st
import html,math
from backend.services.admin_service import settings
from backend.services.listing_service import list_public
from frontend.components.cards import vehicle_card
PAGE_SIZE=9
def _open(lid):
    st.session_state.selected_listing=lid;st.session_state.page="商品詳細";st.rerun()
def render():
    cfg=settings()
    title=html.escape(cfg.get("home_hero_title","RuiderCar 商品交易平台"));subtitle=html.escape(cfg.get("home_hero_subtitle",""))
    try:width=max(40,min(100,int(cfg.get("home_hero_width","100"))))
    except:width=100
    try:height=max(80,min(400,int(cfg.get("home_hero_height","140"))))
    except:height=140
    try:title_size=max(16,min(64,int(cfg.get("home_hero_title_size","26"))))
    except:title_size=26
    try:subtitle_size=max(10,min(32,int(cfg.get("home_hero_subtitle_size","16"))))
    except:subtitle_size=16
    st.markdown(f"""<div class="hero admin-hero" style="width:{width}%;min-height:{height}px;height:{height}px;padding:16px 28px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;overflow:hidden;"><h1 style="font-size:{title_size}px;margin:0 0 8px 0;">{title}</h1><p style="font-size:{subtitle_size}px;margin:0;">{subtitle}</p></div>""",unsafe_allow_html=True)
    q=st.text_input("搜尋商品",placeholder="輸入商品名稱")
    show_images=st.checkbox("顯示圖片",value=True)
    cars=list_public(q)
    if not cars:st.info("目前沒有符合條件的商品。");return
    pages=max(1,math.ceil(len(cars)/PAGE_SIZE))
    page=max(1,min(int(st.session_state.get("home_page",1)),pages))
    st.session_state.home_page=page
    start=(page-1)*PAGE_SIZE;visible=cars[start:start+PAGE_SIZE]
    if show_images:
        cols=st.columns(3)
        for i,x in enumerate(visible):
            with cols[i%3]:
                if vehicle_card(x,show_image=True):_open(x["id"])
    else:
        for x in visible:
            with st.container(border=True):
                c1,c2=st.columns([5,1])
                with c1:
                    st.markdown(f'### {x["title"]}　NT$ {x["price"]:,}')
                    typ="車輛" if x.get("product_type","vehicle")=="vehicle" else "常規"
                    st.caption(f'{typ}商品｜賣家：{x.get("seller_name","")}｜所在地：{x.get("location","")}')
                    if x.get("seller_default_meeting_address"):st.caption(f'常用交易／看貨地址：{x["seller_default_meeting_address"]}')
                    if x.get("summary"):st.write(x["summary"])
                with c2:
                    if st.button("查看",key=f'home_text_view_{x["id"]}',use_container_width=True):_open(x["id"])

    st.divider()
    st.caption(f"第 {page}/{pages} 頁｜每頁最多 {PAGE_SIZE} 件商品。僅載入目前頁面的商品封面。")
    prev_col,page_col,next_col=st.columns([1,2,1])
    with prev_col:
        if st.button("← 上一頁",disabled=page<=1,use_container_width=True,key="home_prev_page"):
            st.session_state.home_page=page-1;st.rerun()
    with page_col:
        selected_page=st.selectbox("切換頁面",list(range(1,pages+1)),index=page-1,key="home_bottom_page",label_visibility="collapsed")
        if selected_page!=page:
            st.session_state.home_page=selected_page;st.rerun()
    with next_col:
        if st.button("下一頁 →",disabled=page>=pages,use_container_width=True,key="home_next_page"):
            st.session_state.home_page=page+1;st.rerun()
