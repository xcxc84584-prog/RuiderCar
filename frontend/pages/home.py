import streamlit as st
import streamlit.components.v1 as components
import html,math
from backend.services.admin_service import settings
from backend.services.listing_service import public_catalog_bounds,list_public_page
from frontend.components.cards import vehicle_card
from backend.services.message_service import unread_count
PAGE_SIZE=9
def _open(lid):
    st.session_state.home_return_listing=int(lid);st.session_state.detail_origin="首頁";st.session_state.selected_listing=lid;st.session_state.page="商品詳細";st.session_state.show_loading=True;st.rerun()
def render():
    cfg=settings();title=html.escape(cfg.get("home_hero_title","RuiderCar 商品交易平台"));subtitle=html.escape(cfg.get("home_hero_subtitle",""))
    try:width=max(40,min(100,int(cfg.get("home_hero_width","100"))))
    except:width=100
    try:height=max(80,min(400,int(cfg.get("home_hero_height","140"))))
    except:height=140
    try:title_size=max(16,min(64,int(cfg.get("home_hero_title_size","26"))))
    except:title_size=26
    try:subtitle_size=max(10,min(32,int(cfg.get("home_hero_subtitle_size","16"))))
    except:subtitle_size=16
    st.markdown(f'''<div class="hero admin-hero" style="width:{width}%;min-height:{height}px;height:{height}px;padding:16px 28px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;overflow:hidden;"><h1 style="font-size:{title_size}px;margin:0 0 8px 0;">{title}</h1><p style="font-size:{subtitle_size}px;margin:0;">{subtitle}</p></div>''',unsafe_allow_html=True)
    with st.form("home_search_form"):
        q=st.text_input("搜尋商品",value=st.session_state.get("home_search_applied",""),placeholder="輸入商品名稱")
        show_images=st.checkbox("顯示圖片",value=st.session_state.get("home_show_images",True))
        search_submit=st.form_submit_button("套用搜尋",width="stretch")
    if search_submit:
        st.session_state.home_search_applied=q.strip();st.session_state.home_show_images=show_images;st.session_state.home_page=1;st.session_state.pop("home_applied_price_range",None);st.rerun()
    q=st.session_state.get("home_search_applied","");show_images=st.session_state.get("home_show_images",True)
    count,price_min,price_max=public_catalog_bounds(q)
    if not count:st.info("目前沒有符合條件的商品。");return
    u=st.session_state.get("user")
    if u and bool(u.get("unread_mail_notifications",True)):
        unread=unread_count(u["id"])
        if unread>0:
            cmsg,cbtn=st.columns([5,1]);cmsg.warning(f"📩 你有 {unread} 封未讀信件。")
            if cbtn.button("查看信件",key="home_open_unread_mail",width="stretch"):st.session_state.page="信件區";st.rerun()
    st.subheader("價格區間")
    with st.form("home_price_form"):
        cmin,cmax,cquery=st.columns([2,2,1])
        applied=st.session_state.get("home_applied_price_range",(price_min,price_max))
        selected_min=cmin.number_input("最低價格",min_value=0,value=max(0,int(applied[0])),step=1000)
        selected_max=cmax.number_input("最高價格",min_value=0,value=max(0,int(applied[1])),step=1000)
        query_price=cquery.form_submit_button("查詢",width="stretch")
    if selected_min>selected_max:st.error("最低價格不可高於最高價格。");return
    if query_price:
        st.session_state.home_applied_price_range=(int(selected_min),int(selected_max));st.session_state.home_page=1;st.rerun()
    applied_min,applied_max=st.session_state.get("home_applied_price_range",(price_min,price_max))
    page=max(1,int(st.session_state.get("home_page",1)))
    visible,total=list_public_page(q,applied_min,applied_max,page,PAGE_SIZE)
    pages=max(1,math.ceil(total/PAGE_SIZE));page=min(page,pages)
    if page!=st.session_state.get("home_page",1):st.session_state.home_page=page;visible,total=list_public_page(q,applied_min,applied_max,page,PAGE_SIZE)
    st.caption(f"價格查詢：NT$ {applied_min:,} ～ NT$ {applied_max:,}｜符合 {total} 件商品")
    if not visible:st.info("目前價格區間內沒有符合條件的商品。");return
    return_lid=st.session_state.get("home_restore_listing")
    if show_images:
        cols=st.columns(3)
        for i,x in enumerate(visible):
            with cols[i%3]:
                st.markdown(f'<div id="listing-{x["id"]}"></div>',unsafe_allow_html=True)
                if vehicle_card(x,show_image=True):_open(x["id"])
    else:
        for x in visible:
            st.markdown(f'<div id="listing-{x["id"]}"></div>',unsafe_allow_html=True)
            with st.container(border=True):
                c1,c2=st.columns([5,1])
                with c1:
                    st.markdown(f'### {x["title"]}');st.markdown(f'**NT$ {x["price"]:,}**');typ="車輛" if x.get("product_type","vehicle")=="vehicle" else "常規"
                    st.caption(f'{typ}商品｜賣家：{x.get("seller_name","")}｜所在地：{x.get("location","")}')
                    if x.get("seller_default_meeting_address"):st.caption(f'常用交易／看貨地址：{x["seller_default_meeting_address"]}')
                    if x.get("summary"):st.write(x["summary"])
                with c2:
                    if st.button("查看",key=f'home_text_view_{x["id"]}',width="stretch"):_open(x["id"])
    if return_lid:
        components.html(f'''<script>const id='listing-{int(return_lid)}';setTimeout(()=>{{const el=window.parent.document.getElementById(id);if(el) el.scrollIntoView({{behavior:'instant',block:'center'}});}},80);</script>''',height=0);st.session_state.pop("home_restore_listing",None)
    st.divider();st.caption(f"第 {page}/{pages} 頁｜每頁最多 {PAGE_SIZE} 件商品。資料庫只查詢目前頁面，封面按目前頁面載入。")
    prev_col,page_col,next_col=st.columns([1,2,1])
    with prev_col:
        if st.button("← 上一頁",disabled=page<=1,width="stretch",key="home_prev_page"):st.session_state.home_page=page-1;st.session_state.show_loading=True;st.rerun()
    with page_col:
        selected_page=st.selectbox("切換頁面",list(range(1,pages+1)),index=page-1,key="home_bottom_page",label_visibility="collapsed")
        if selected_page!=page:st.session_state.home_page=selected_page;st.session_state.show_loading=True;st.rerun()
    with next_col:
        if st.button("下一頁 →",disabled=page>=pages,width="stretch",key="home_next_page"):st.session_state.home_page=page+1;st.session_state.show_loading=True;st.rerun()
