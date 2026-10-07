import streamlit as st
import pandas as pd
from backend.services.listing_service import list_public
from frontend.components.cards import vehicle_card

def render():
    st.markdown('<div class="hero"><h1>RuiderCar 商品交易平台</h1><p>瀏覽車輛與常規商品、預約或聯絡賣家。平台不代替買賣雙方完成線下交易。</p></div>',unsafe_allow_html=True)
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
