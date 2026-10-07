import streamlit as st
from backend.database import PROJECT_ROOT
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
    return st.button("查看商品",key=f'detail_{x["id"]}',use_container_width=True)
