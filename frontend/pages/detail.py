import streamlit as st
from datetime import datetime,timedelta
from backend.services.listing_service import get_listing
from backend.services.appointment_service import create
from backend.services.message_service import send
from backend.database import PROJECT_ROOT

def render():
    lid=st.session_state.get("selected_listing")
    x=get_listing(lid) if lid else None
    if not x:st.warning("請先選擇商品。");return
    current=st.session_state.get("user")
    if x["status"]!="active" and (not current or current["id"]!=x["seller_id"]):
        st.warning("此商品目前未上架。");return
    imgs=x.get("images") or []
    st.title(x["title"])
    top_image,top_info=st.columns([1.05,1.35],gap="large")
    with top_image:
        if imgs:
            cover=PROJECT_ROOT/imgs[0]["file_path"]
            if cover.exists():st.image(str(cover),use_container_width=True)
            else:st.info("封面照片目前無法顯示。")
        else:st.info("賣家尚未上傳商品照片。")
    with top_info:
        st.markdown(f"## :blue[NT$ {x['price']:,}]")
        if x.get("summary"):st.write(x["summary"])
        a,b,c=st.columns(3)
        a.metric("年式",x["year"]);b.metric("里程",f'{x["mileage"]:,} km');c.metric("能源",x["fuel"])
        st.write(f'**廠牌／車型：** {x["brand"]} {x["model"]}')
        st.write(f'**車身／變速：** {x["body_type"]}／{x["transmission"]}')
        st.write(f'**所在地：** {x["location"]}')
        st.write(f'**預計交車時間：** {x["delivery_time"]}')
        st.write(f'**看車地址：** {x["meeting_address"]}')
        st.write(f'**付款方式：** {x["payment_method"]}')
        st.write(f'**接受貸款：** {"是" if x["accepts_loan"] else "否"}')
    st.subheader("商品說明")
    st.write(x["description"] or "賣家尚未填寫詳細說明。")
    u=st.session_state.get("user")
    if not u:
        st.info("登入後即可預約看車或聯絡賣家。")
    elif u["id"]==x["seller_id"]:
        st.info("這是你自己的商品。")
    else:
        st.subheader("預約看車")
        d=st.date_input("日期",min_value=datetime.now().date())
        t=st.time_input("時間",value=(datetime.now()+timedelta(hours=2)).time().replace(second=0,microsecond=0))
        note=st.text_input("備註")
        if st.button("提出預約",use_container_width=True):
            ok,msg=create(u["id"],x["id"],datetime.combine(d,t),note);st.success(msg) if ok else st.error(msg)
        st.subheader("和賣家聊天")
        subject=st.text_input("主旨",value=f'詢問：{x["title"]}')
        body=st.text_area("內容")
        if st.button("送出訊息",use_container_width=True):
            if body.strip():send(u["id"],x["seller_id"],subject,body,x["id"]);st.success("訊息已送出")
    if len(imgs)>1:
        st.divider()
        st.subheader("其他照片")
        gallery=imgs[1:]
        for start in range(0,len(gallery),3):
            cols=st.columns(3)
            for offset,img in enumerate(gallery[start:start+3]):
                path=PROJECT_ROOT/img["file_path"]
                if path.exists():
                    with cols[offset]:st.image(str(path),use_container_width=True,caption=f"照片 {start+offset+2}")
