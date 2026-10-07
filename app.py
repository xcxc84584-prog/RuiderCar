import streamlit as st
from backend.seed import seed
from frontend.styles.theme import apply_theme
from frontend.router import route
from frontend.auth_session import restore_browser_session,logout_browser_session
from backend.services.auth_service import fresh_user
st.set_page_config(page_title="RuiderCar 車輛交易平台",page_icon="🚙",layout="wide",initial_sidebar_state="expanded")
@st.cache_resource(show_spinner=False)
def _bootstrap():
    seed()
    return True
_bootstrap();apply_theme()
if "page" not in st.session_state:st.session_state.page="首頁"
restore_browser_session()
if st.session_state.get("user"):
    latest=fresh_user(st.session_state.user["id"])
    if latest:st.session_state.user=latest
    else:logout_browser_session()
with st.sidebar:
    st.markdown("## 🚙 RuiderCar")
    u=st.session_state.get("user")
    if u:
        st.success(f'登入：{u["name"]}')
        st.caption(f'流量：{u["traffic_balance"]}')
        pages=["首頁","我的預約","信件區","送信給管理員","流量中心","賣出／商品管理","帳號設定"]
        if u.get("role")=="admin":pages.append("管理員後台")
        for p in pages:
            if st.button(p,use_container_width=True,key=f"nav_{p}"):st.session_state.page=p;st.rerun()
        if st.button("登出",use_container_width=True):
            logout_browser_session();st.session_state.page="首頁";st.rerun()
    else:
        if st.button("首頁",use_container_width=True):st.session_state.page="首頁";st.rerun()
        if st.button("登入",use_container_width=True):st.session_state.page="登入";st.rerun()
        if st.button("註冊",use_container_width=True):st.session_state.page="註冊";st.rerun()
route()
