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
_bootstrap()
if "theme_mode" not in st.session_state:st.session_state.theme_mode="dark"
apply_theme(st.session_state.theme_mode)
if "page" not in st.session_state:st.session_state.page="首頁"
restore_browser_session()
if st.session_state.get("user"):
    if not st.session_state.get("impersonator_admin"):
        latest=fresh_user(st.session_state.user["id"])
        if latest:st.session_state.user=latest
        else:logout_browser_session()
with st.sidebar:
    st.markdown("## 🚙 RuiderCar")
    theme_label=st.radio("顯示模式",["🌙 黑夜","☀️ 白天"],index=0 if st.session_state.theme_mode=="dark" else 1,horizontal=True,key="theme_selector")
    selected_theme="dark" if theme_label.startswith("🌙") else "light"
    if selected_theme!=st.session_state.theme_mode:
        st.session_state.theme_mode=selected_theme;st.rerun()
    u=st.session_state.get("user")
    if u:
        if st.session_state.get("impersonator_admin"):
            admin_origin=st.session_state.impersonator_admin
            st.warning(f'管理員代理登入：#{u["id"]} {u["name"]}')
            if st.button("返回管理員帳號",use_container_width=True,key="return_admin"):
                st.session_state.user=admin_origin
                st.session_state.pop("impersonator_admin",None)
                st.session_state.page="管理員後台"
                st.rerun()
        st.success(f'登入：{u["name"]}')
        st.caption(f'流量：{u["traffic_balance"]}')
        pages=["首頁","我的收藏","我的預約","信件區","送信給管理員","流量中心","賣出／商品管理","輔助與說明","帳號設定"]
        if u.get("role")=="admin":pages.append("管理員後台")
        for p in pages:
            if st.button(p,use_container_width=True,key=f"nav_{p}"):st.session_state.page=p;st.rerun()
        if st.button("登出",use_container_width=True):
            st.session_state.pop("impersonator_admin",None)
            logout_browser_session();st.session_state.page="首頁";st.rerun()
    else:
        if st.button("首頁",use_container_width=True):st.session_state.page="首頁";st.rerun()
        if st.button("登入",use_container_width=True):st.session_state.page="登入";st.rerun()
        if st.button("註冊",use_container_width=True):st.session_state.page="註冊";st.rerun()
        if st.button("輔助與說明",use_container_width=True):st.session_state.page="輔助與說明";st.rerun()
route()
