import streamlit as st
from datetime import datetime,timedelta
from backend.services.listing_service import get_listing,admin_force_remove
from backend.services.appointment_service import create
from backend.services.message_service import send
from backend.services.image_service import image_source
from backend.services.favorite_service import is_favorite,toggle_favorite

def render():
    lid=st.session_state.get("selected_listing")
    x=get_listing(lid) if lid else None
    if not x:st.warning("請先選擇商品。");return
    current=st.session_state.get("user")
    if x["status"]!="active" and (not current or current["id"]!=x["seller_id"]):
        st.warning("此商品目前未上架。");return
    imgs=x.get("images") or []
    st.title(x["title"])
    if current:
        fav=is_favorite(current["id"],x["id"])
        if st.button("★ 已收藏｜取消收藏" if fav else "☆ 收藏商品",key=f'favorite_detail_{x["id"]}'):
            ok,msg,_=toggle_favorite(current["id"],x["id"]);(st.success if ok else st.error)(msg)
            if ok:st.rerun()
    top_image,top_info=st.columns([1.05,1.35],gap="large")
    with top_image:
        if imgs:
            source=image_source(imgs[0])
            if source is not None:st.image(source,use_container_width=True)
            else:st.info("封面照片目前無法顯示。")
        else:st.info("賣家尚未上傳商品照片。")
    with top_info:
        st.markdown(f"## :blue[NT$ {x['price']:,}]")
        if x.get("summary"):st.write(x["summary"])
        if x.get("product_type","vehicle")=="vehicle":
            a,b,c=st.columns(3)
            a.metric("年式",x["year"]);b.metric("里程",f'{x["mileage"]:,} km');c.metric("能源",x["fuel"])
            st.write(f'**廠牌／車型：** {x["brand"]} {x["model"]}')
            st.write(f'**車身／變速：** {x["body_type"]}／{x["transmission"]}')
            st.write(f'**接受貸款：** {"是" if x["accepts_loan"] else "否"}')
        else:
            st.write("**商品類型：** 常規商品")
        st.write(f'**所在地：** {x["location"]}')
        st.write(f'**預計交付時間：** {x["delivery_time"]}')
        st.write(f'**交易／看貨地址：** {x["meeting_address"]}')
        st.write(f'**付款方式：** {x["payment_method"]}')
        st.write(f'**賣家：** {x.get("seller_name","")}')
        st.write(f'**賣家 Email：** {x.get("seller_email","")}')
        st.write(f'**賣家電話：** {x.get("seller_phone","")}')
    st.subheader("商品說明")
    st.write(x["description"] or "賣家尚未填寫詳細說明。")
    if current and current.get("role")=="admin" and x["status"]=="active":
        st.warning("管理員強制移除不退還賣家流量；系統會通知賣家，商品與草稿資料將永久刪除。")
        reason=st.text_input("強制移除原因",key=f'admin_force_reason_detail_{x["id"]}',placeholder="必填；原因會出現在系統通知中")
        if st.button("管理員強制移除商品",key=f'admin_force_remove_detail_{x["id"]}',use_container_width=True):
            ok,msg=admin_force_remove(current["id"],x["id"],reason)
            (st.success if ok else st.error)(msg)
            if ok:st.session_state.page="首頁";st.rerun()
    u=st.session_state.get("user")
    if not u:
        st.info("登入後即可預約查看商品或聯絡賣家。")
    elif u["id"]==x["seller_id"]:
        st.info("這是你自己的商品。")
    else:
        st.subheader("預約查看商品")
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
        load_gallery=st.toggle(f"展開／載入其他照片（{len(imgs)-1} 張）",value=False,key=f'load_gallery_{x["id"]}')
        if load_gallery:
            st.caption("詳細照片已按需載入。")
            gallery=imgs[1:]
            for start in range(0,len(gallery),3):
                cols=st.columns(3)
                for offset,img in enumerate(gallery[start:start+3]):
                    source=image_source(img)
                    if source is not None:
                        with cols[offset]:st.image(source,use_container_width=True,caption=f"照片 {start+offset+2}")
