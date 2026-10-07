import time
from datetime import datetime,timedelta
import streamlit as st
from streamlit_cookies_controller import CookieController,RemoveEmptyElementContainer
from backend.services.session_service import create_login_session,restore_login_session,revoke_login_session
COOKIE_NAME="ruidercar_remember"
REMEMBER_DAYS=30
RemoveEmptyElementContainer()
def _controller():
    return CookieController()
def _cookie_token():
    token=st.session_state.get("remember_cookie_token")
    if token:return token
    try:
        token=_controller().get(COOKIE_NAME)
    except Exception:
        token=None
    if isinstance(token,dict):token=token.get("value")
    if token:st.session_state.remember_cookie_token=token
    return token
def restore_browser_session():
    try:
        if "_bd_session" in st.query_params:del st.query_params["_bd_session"]
    except Exception:pass
    if st.session_state.get("user"):return
    token=_cookie_token()
    if not token:return
    user=restore_login_session(token)
    if user:
        st.session_state.user=user
        st.session_state.auth_token=token
        st.session_state.remember_device=True
    else:
        try:_controller().remove(COOKIE_NAME)
        except Exception:pass
        st.session_state.pop("remember_cookie_token",None)
def establish_browser_session(user,remember=False):
    token=create_login_session(user["id"],remember=remember)
    st.session_state.user=user
    st.session_state.auth_token=token
    st.session_state.remember_device=remember
    if remember:
        expiry=datetime.now()+timedelta(days=REMEMBER_DAYS)
        _controller().set(COOKIE_NAME,{"value":token,"expiry_date":expiry.isoformat()})
        st.session_state.remember_cookie_token=token
        time.sleep(0.35)
def logout_browser_session():
    token=st.session_state.get("auth_token") or _cookie_token()
    if token:revoke_login_session(token)
    try:_controller().remove(COOKIE_NAME)
    except Exception:pass
    st.session_state.pop("remember_cookie_token",None)
    st.session_state.pop("remember_device",None)
    st.session_state.pop("auth_token",None)
    st.session_state.pop("user",None)
