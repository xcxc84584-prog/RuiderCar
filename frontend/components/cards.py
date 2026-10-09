import streamlit as st
from backend.services.image_service import cover_source
from backend.services.listing_service import admin_force_remove

def vehicle_card(x,show_image=True):
    imgs=x.get("images") or []
    if show_image:
        if imgs:
            source=cover_source(imgs[0])
            if source is not None:st.image(source,width="stretch")
        else:
            icon="🚙" if x.get("product_type","vehicle")=="vehicle" else "📦"
            st.markdown(f'<div style="height:180px;border-radius:14px;background:#0d47a1;display:flex;align-items:center;justify-content:center;font-size:44px">{icon}</div>',unsafe_allow_html=True)
    st.markdown(f'### {x["title"]}')
    st.markdown(f'**NT$ {x["price"]:,}**')
    if x.get("product_type","vehicle")=="vehicle":
        st.write(f'年式：{x["year"]}　｜　里程：**{x["mileage"]:,} km**')
        st.caption(f'{x["brand"]} {x["model"]}｜{x["location"]}')
    else:
        st.caption(f'常規商品｜{x["location"]}')
    st.caption(f'賣家：{x.get("seller_name","")}｜{x.get("seller_email","")}｜{x.get("seller_phone","")}')
    if x.get("seller_default_meeting_address"):st.caption(f'常用交易／看貨地址：{x["seller_default_meeting_address"]}')
    current=st.session_state.get("user")
    if current and current.get("role")=="admin":
        reason=st.text_input("強制移除原因",key=f'admin_remove_reason_{x["id"]}',placeholder="必填；原因會通知賣家")
        if st.button("管理員強制移除",key=f'admin_remove_{x["id"]}',width="stretch"):
            ok,msg=admin_force_remove(current["id"],x["id"],reason)
            (st.success if ok else st.error)(msg)
            if ok:st.rerun()
    return st.button("查看商品",key=f'detail_{x["id"]}',width="stretch")
