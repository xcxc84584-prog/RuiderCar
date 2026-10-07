import streamlit as st
from backend.services.auth_service import login,register
from backend.services.account_service import close_account,update_account_info
from frontend.auth_session import establish_browser_session,logout_browser_session
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
    if st.button("建立帳號",use_container_width=True):
        ok,msg=register(n,e,ph,p);(st.success if ok else st.error)(msg)
        if ok:
            st.info("帳號已建立，可直接登入。")
    st.divider()

def render_settings():
    u=st.session_state.get("user")
    if not u:
        st.warning("請先登入");return
    st.title("帳號設定")
    st.subheader("修正帳戶訊息")
    st.caption("可修改登入 Email 與聯絡電話。修改後會立即套用。")
    email=st.text_input("Email",value=u.get("email",""),key="settings_email")
    phone=st.text_input("電話",value=u.get("phone",""),key="settings_phone")
    if st.button("儲存帳戶訊息",type="primary",use_container_width=True):
        ok,msg,new_user=update_account_info(u["id"],email,phone)
        (st.success if ok else st.error)(msg)
        if ok:
            st.session_state.user=new_user
            st.rerun()
    st.divider()
    st.subheader("註銷帳號")
    st.warning("註銷後帳號將停用、公開商品下架，且會登出所有裝置。歷史交易／訊息資料依平台規則保留。")
    password=st.text_input("目前密碼",type="password",key="close_account_password")
    confirm=st.checkbox("我確認要註銷此帳號",key="close_account_confirm")
    if st.button("註銷帳號",use_container_width=True,disabled=not confirm):
        ok,msg=close_account(u["id"],password)
        (st.success if ok else st.error)(msg)
        if ok:
            logout_browser_session()
            st.session_state.page="首頁"
            st.rerun()
