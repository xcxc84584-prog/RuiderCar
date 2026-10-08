import streamlit as st
from frontend.pages import home,detail,account,member,seller,admin,help
def route():
    p=st.session_state.get("page","首頁")
    if p=="首頁":home.render()
    elif p=="商品詳細":detail.render()
    elif p=="登入":account.render_login()
    elif p=="註冊":account.render_register()
    elif p=="帳號設定":account.render_settings()
    elif p=="我的預約":member.reservations()
    elif p=="信件區":member.mailbox()
    elif p=="送信給管理員":member.admin_contact()
    elif p=="流量中心":member.traffic()
    elif p=="輔助與說明":help.render()
    elif p=="賣出／商品管理":seller.render()
    elif p=="管理員後台":admin.render()
