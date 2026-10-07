import streamlit as st
from backend.services.auth_service import login,register
from frontend.auth_session import establish_browser_session
def render_login():
    st.title("登入")
    e=st.text_input("Email");p=st.text_input("密碼",type="password")
    if st.button("登入",use_container_width=True):
        u=login(e,p)
        if u:
            establish_browser_session(u);st.session_state.page="首頁";st.rerun()
        st.error("帳號或密碼錯誤")
def render_register():
    st.title("註冊")
    n=st.text_input("名稱");e=st.text_input("Email");ph=st.text_input("手機號碼");p=st.text_input("密碼",type="password")
    if st.button("建立帳號",use_container_width=True):
        if len(p)<8:st.error("密碼至少 8 碼");return
        ok,msg=register(n,e,ph,p);st.success(msg) if ok else st.error(msg)

def render_settings():
    from backend.services.account_service import close_account
    from frontend.auth_session import logout_browser_session
    u=st.session_state.get("user")
    if not u:st.warning("請先登入。\n");return
    st.title("帳號設定")
    st.write(f'帳號：{u.get("name","")}｜{u.get("email","")}')
    st.divider()
    st.subheader("註銷帳號")
    if u.get("role")=="admin":
        st.info("管理員帳號不能從此頁面註銷。")
        return
    st.error("註銷後將無法登入；目前公開商品會立即下架。歷史預約、訊息與流量交易紀錄會保留，以維持資料完整性。此操作無法自行復原。")
    password=st.text_input("輸入目前密碼",type="password",key="close_account_password")
    confirm=st.checkbox("我了解註銷後將無法再使用此帳號登入",key="close_account_confirm")
    if st.button("永久註銷帳號",type="primary",use_container_width=True,disabled=not confirm):
        if not password:st.error("請輸入目前密碼");return
        ok,msg=close_account(u["id"],password)
        if not ok:st.error(msg);return
        logout_browser_session()
        st.session_state.page="首頁"
        st.success(msg)
        st.rerun()
