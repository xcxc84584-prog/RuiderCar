import streamlit as st
from backend.services.listing_service import list_public
from frontend.components.cards import vehicle_card
def render():
    st.markdown('<div class="hero"><h1>RuiderCar 車輛預約交易平台</h1><p>搜尋車輛、預約看車、直接與賣家聯絡。平台不代替買賣雙方完成線下交易。</p></div>',unsafe_allow_html=True)
    q=st.text_input("搜尋車輛",placeholder="輸入廠牌、車型或商品名稱")
    cars=list_public(q)
    if not cars:st.info("目前沒有符合條件的車輛。");return
    cols=st.columns(3)
    for i,x in enumerate(cars):
        with cols[i%3]:
            if vehicle_card(x):
                st.session_state.selected_listing=x["id"];st.session_state.page="商品詳細";st.rerun()
