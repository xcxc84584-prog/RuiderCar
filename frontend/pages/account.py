import streamlit as st
from backend.services.auth_service import login,register
from frontend.auth_session import establish_browser_session
def render_login():
    st.title("登入")
    e=st.text_input("Email");p=st.text_input("密碼",type="password")
    remember=st.checkbox("在此裝置保持登入 30 天",value=False,help="僅建議在自己的裝置使用。登出或帳號註銷後會失效。")
    if st.button("登入",use_container_width=True):
        u=login(e,p)
        if u:
            establish_browser_session(u,remember=remember);st.session_state.page="首頁";st.rerun()
        st.error("帳號或密碼錯誤")
def render_register():
    st.title("註冊")
    n=st.text_input("名稱");e=st.text_input("Email");ph=st.text_input("手機號碼");p=st.text_input("密碼",type="password")
    if st.button("建立帳號並寄送驗證碼",use_container_width=True):
        ok,msg=register(n,e,ph,p);(st.success if ok else st.error)(msg)
        if ok:st.session_state.verify_email=e.strip().lower()
    st.divider()
