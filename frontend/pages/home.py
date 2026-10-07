import streamlit as st
import pandas as pd
import html
from backend.services.admin_service import settings
from backend.services.listing_service import list_public
from frontend.components.cards import vehicle_card

def render():
    cfg=settings()
    title=html.escape(cfg.get("home_hero_title","RuiderCar 商品交易平台"))
    subtitle=html.escape(cfg.get("home_hero_subtitle",""))
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
    c1,c2=st.columns(2)
    vehicles_only=c1.checkbox("僅顯示車輛商品",value=False)
    show_images=c2.checkbox("顯示圖片",value=True)
    cars=list_public(q,vehicles_only=vehicles_only)
    if not cars:st.info("目前沒有符合條件的商品。");return
    if show_images:
        cols=st.columns(3)
        for i,x in enumerate(cars):
            with cols[i%3]:
                if vehicle_card(x,show_image=True):
                    st.session_state.selected_listing=x["id"];st.session_state.page="商品詳細";st.rerun()
    else:
        rows=[]
        for x in cars:
            rows.append({"ID":x["id"],"商品":x["title"],"類型":"車輛" if x.get("product_type","vehicle")=="vehicle" else "常規","價格":f'NT$ {x["price"]:,}',"賣家":x.get("seller_name",""),"Email":x.get("seller_email",""),"電話":x.get("seller_phone",""),"所在地":x.get("location",""),"里程":f'{x["mileage"]:,} km' if x.get("product_type","vehicle")=="vehicle" else "—"})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.caption("選擇商品 ID 後可查看詳細資料。")
        ids=[x["id"] for x in cars]
        selected=st.selectbox("商品 ID",ids,format_func=lambda lid:next(f'#{x["id"]} {x["title"]}' for x in cars if x["id"]==lid))
        if st.button("查看選定商品",use_container_width=True):
            st.session_state.selected_listing=selected;st.session_state.page="商品詳細";st.rerun()
