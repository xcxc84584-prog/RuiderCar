import streamlit as st
from datetime import datetime,timedelta
from backend.services.listing_service import get_listing
from backend.services.appointment_service import create
from backend.services.message_service import send
def render():
    lid=st.session_state.get("selected_listing")
    x=get_listing(lid) if lid else None
    if not x:st.warning("請先選擇商品。");return
    current=st.session_state.get("user")
    if x["status"]!="active" and (not current or current["id"]!=x["seller_id"]):
        st.warning("此商品目前未上架。");return
    st.title(x["title"]);st.markdown(f"## :blue[NT$ {x['price']:,}]")
    imgs=x.get("images") or []
    if imgs:
        from backend.database import PROJECT_ROOT
        cover=PROJECT_ROOT/imgs[0]["file_path"]
        if cover.exists():st.image(str(cover),use_container_width=True)
        if len(imgs)>1:
            st.caption(f"商品照片 1/{len(imgs)}｜下方為其他照片")
            cols=st.columns(min(4,len(imgs)-1))
            for i,img in enumerate(imgs[1:]):
                path=PROJECT_ROOT/img["file_path"]
                if path.exists():
                    with cols[i%len(cols)]:st.image(str(path),use_container_width=True,caption=f"照片 {i+2}")
    else:
        st.info("賣家尚未上傳商品照片。")
    a,b,c=st.columns(3);a.metric("年式",x["year"]);b.metric("里程",f'{x["mileage"]:,} km');c.metric("能源",x["fuel"])
    st.write(x["description"]);st.caption(f'{x["brand"]} {x["model"]}｜{x["body_type"]}｜{x["transmission"]}｜{x["location"]}')
    st.write("**預計交車時間：**",x["delivery_time"]);st.write("**看車地址：**",x["meeting_address"])
    u=st.session_state.get("user")
    if not u:st.info("登入後即可預約看車或聯絡賣家。");return
    if u["id"]==x["seller_id"]:st.info("這是你自己的商品。");return
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
