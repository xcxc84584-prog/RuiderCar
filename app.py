import streamlit as st
from backend.seed import seed
from frontend.styles.theme import apply_theme
from frontend.router import route
from frontend.auth_session import restore_browser_session,logout_browser_session,browser_theme_preference,save_browser_theme_preference
from backend.services.auth_service import fresh_user
from backend.services.account_service import update_theme_preference
from backend.services.ip_service import client_ip_from_streamlit,touch_ip,cleanup_old_logs
import time
from datetime import datetime
from backend.utils.timezone import utc_now
st.set_page_config(page_title="RuiderCar 車輛交易平台",page_icon="🚙",layout="wide",initial_sidebar_state="expanded")
@st.cache_resource(show_spinner=False)
def _bootstrap():
    seed()
    return True
_bootstrap()
client_ip=client_ip_from_streamlit(st)
if "ip_cleanup_at" not in st.session_state or time.time()-st.session_state.ip_cleanup_at>600:
    cleanup_old_logs();st.session_state.ip_cleanup_at=time.time()
ip_gate=touch_ip(client_ip,st.session_state.get("user",{}).get("id") if st.session_state.get("user") else None)
if not ip_gate.get("allowed",True):
    status=ip_gate.get("status")
    if status=="queue":
        st.title("網站目前使用人數已達上限")
        st.info(f'排隊中：當前隊列第 {ip_gate.get("queue_position",1)} 位')
        st.caption("系統會依序釋放最近 5 分鐘沒有活動的 IP 名額。請稍後重新整理。")
        if st.button("重新檢查排隊狀態",width="stretch"):st.rerun()
    elif status=="greylist":
        until=ip_gate.get("until")
        remain=max(0,int((until-utc_now()).total_seconds())) if until else 0
        st.title("暫時限制存取")
        st.error(f'此 IP 因短時間大量請求暫停存取。剩餘約 {remain//60} 分 {remain%60} 秒。')
    else:
        st.title("存取遭拒")
        st.error("此 IP 已被系統管理員封鎖。")
    st.stop()
_lp=None
if st.session_state.pop("show_loading",False):
    _lp=st.progress(35,text="正在載入頁面…")
if "page" not in st.session_state:st.session_state.page="首頁"
restore_browser_session()
if st.session_state.get("user"):
    if not st.session_state.get("impersonator_admin"):
        latest=fresh_user(st.session_state.user["id"])
        if latest:st.session_state.user=latest
        else:logout_browser_session()
u=st.session_state.get("user")
current_identity=u.get("id") if u else "guest"
if st.session_state.get("theme_identity")!=current_identity:
    preferred=(u.get("theme_preference") if u else browser_theme_preference()) or "dark"
    st.session_state.theme_mode=preferred if preferred in ("dark","light") else "dark"
    st.session_state.theme_identity=current_identity
    st.session_state.theme_selector="🌙 黑夜" if st.session_state.theme_mode=="dark" else "☀️ 白天"
elif "theme_mode" not in st.session_state:
    st.session_state.theme_mode=(browser_theme_preference() or "dark")
apply_theme(st.session_state.theme_mode)
with st.sidebar:
    st.markdown("## 🚙 RuiderCar")
    theme_label=st.radio("顯示模式",["🌙 黑夜","☀️ 白天"],index=0 if st.session_state.theme_mode=="dark" else 1,horizontal=True,key="theme_selector")
    selected_theme="dark" if theme_label.startswith("🌙") else "light"
    if selected_theme!=st.session_state.theme_mode:
        st.session_state.theme_mode=selected_theme
        save_browser_theme_preference(selected_theme)
        if st.session_state.get("user"):
            update_theme_preference(st.session_state.user["id"],selected_theme)
            st.session_state.user["theme_preference"]=selected_theme
        st.rerun()
    u=st.session_state.get("user")
    if u:
        if st.session_state.get("impersonator_admin"):
            admin_origin=st.session_state.impersonator_admin
            st.warning(f'管理員代理登入：#{u["id"]} {u["name"]}')
            if st.button("返回管理員帳號",width="stretch",key="return_admin"):
                from backend.services.admin_service import log_impersonation_end
                log_impersonation_end(admin_origin["id"],u["id"])
                st.session_state.user=admin_origin
                st.session_state.pop("impersonator_admin",None)
                st.session_state.page="管理員後台"
                st.rerun()
        st.success(f'登入：{u["name"]}')
        st.caption(f'流量：{u["traffic_balance"]}')
        pages=["首頁","我的收藏","我的預約","信件區","送信給管理員","流量中心","賣出／商品管理","輔助與說明","帳號設定"]
        if u.get("role")=="admin":pages.append("管理員後台")
        for p in pages:
            if st.button(p,width="stretch",key=f"nav_{p}"):st.session_state.page=p;st.session_state.show_loading=True;st.rerun()
        if st.button("登出",width="stretch"):
            st.session_state.pop("impersonator_admin",None)
            logout_browser_session();st.session_state.page="首頁";st.session_state.show_loading=True;st.rerun()
    else:
        if st.button("首頁",width="stretch"):st.session_state.page="首頁";st.session_state.show_loading=True;st.rerun()
        if st.button("我的收藏",width="stretch"):st.session_state.page="我的收藏";st.rerun()
        if st.button("登入",width="stretch"):st.session_state.page="登入";st.session_state.show_loading=True;st.rerun()
        if st.button("註冊",width="stretch"):st.session_state.page="註冊";st.session_state.show_loading=True;st.rerun()
        if st.button("輔助與說明",width="stretch"):st.session_state.page="輔助與說明";st.session_state.show_loading=True;st.rerun()
if _lp:_lp.progress(80,text="正在載入內容…")
route()
if _lp:_lp.progress(100,text="載入完成")
