import streamlit as st
from backend.database import PROJECT_ROOT
from backend.services.listing_service import admin_force_remove
def vehicle_card(x):
    imgs=x.get("images") or []
    if imgs:
        path=PROJECT_ROOT/imgs[0]["file_path"]
        if path.exists():st.image(str(path),use_container_width=True)
    else:
        st.markdown('<div style="height:180px;border-radius:14px;background:#0d47a1;display:flex;align-items:center;justify-content:center;font-size:44px">🚙</div>',unsafe_allow_html=True)
    st.markdown(f'### {x["title"]}')
    st.markdown(f'**NT$ {x["price"]:,}**')
    st.caption(f'{x["year"]}｜{x["mileage"]:,} km｜{x["location"]}')
    st.caption(f'賣家：{x.get("seller_name","")}｜{x.get("seller_email","")}｜{x.get("seller_phone","")}')
    current=st.session_state.get("user")
    if current and current.get("role")=="admin":
        if st.button("管理員強制移除",key=f'admin_remove_{x["id"]}',use_container_width=True):
            ok,msg=admin_force_remove(current["id"],x["id"])
            (st.success if ok else st.error)(msg)
            if ok:st.rerun()
    return st.button("查看商品",key=f'detail_{x["id"]}',use_container_width=True)
