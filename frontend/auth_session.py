import time
from datetime import datetime,timedelta
import streamlit as st
from streamlit_cookies_controller import CookieController,RemoveEmptyElementContainer
from backend.services.session_service import create_login_session,restore_login_session,revoke_login_session
COOKIE_NAME="ruidercar_remember"
REGISTER_DEVICE_COOKIE="ruidercar_registered_device"
REMEMBER_DAYS=30
RemoveEmptyElementContainer()
def _controller():
    return CookieController()
def _cookie_token():
    token=st.session_state.get("remember_cookie_token")
    if token:return token
    token=None
    controller=_controller()
    for attempt in range(3):
        try:token=controller.get(COOKIE_NAME)
        except Exception:token=None
        if isinstance(token,dict):token=token.get("value")
        if token:break
        if attempt<2:time.sleep(0.15)
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
        _controller().set(COOKIE_NAME,token,path="/",expires=expiry,max_age=REMEMBER_DAYS*24*60*60,secure=True,same_site="lax")
        st.session_state.remember_cookie_token=token
        time.sleep(0.5)
def logout_browser_session():
    token=st.session_state.get("auth_token") or _cookie_token()
    if token:revoke_login_session(token)
    try:_controller().remove(COOKIE_NAME)
    except Exception:pass
    st.session_state.pop("remember_cookie_token",None)
    st.session_state.pop("remember_device",None)
    st.session_state.pop("auth_token",None)
    st.session_state.pop("user",None)

def device_already_registered():
    try:
        v=_controller().get(REGISTER_DEVICE_COOKIE)
        if isinstance(v,dict):v=v.get("value")
        return bool(v)
    except Exception:
        return False

def mark_device_registered():
    try:
        expiry=datetime.now()+timedelta(days=365)
        _controller().set(REGISTER_DEVICE_COOKIE,"1",path="/",expires=expiry,max_age=365*24*60*60,secure=True,same_site="lax")
        time.sleep(0.3)
    except Exception:
        pass

GUEST_FAVORITES_COOKIE="ruidercar_guest_favorites"
def guest_favorite_ids():
    try:
        raw=_controller().get(GUEST_FAVORITES_COOKIE)
        if isinstance(raw,dict):raw=raw.get("value")
        if not raw:return []
        return sorted({int(x) for x in str(raw).split(",") if str(x).isdigit()})[:200]
    except Exception:return []
def set_guest_favorite_ids(ids):
    clean=sorted({int(x) for x in ids if str(x).isdigit()})[:200]
    try:
        expiry=datetime.now()+timedelta(days=365)
        _controller().set(GUEST_FAVORITES_COOKIE,",".join(map(str,clean)),path="/",expires=expiry,max_age=365*24*60*60,secure=True,same_site="lax")
        time.sleep(0.2)
    except Exception:pass
    return clean
def toggle_guest_favorite(lid):
    ids=guest_favorite_ids();lid=int(lid)
    if lid in ids:ids.remove(lid);set_guest_favorite_ids(ids);return False
    ids.append(lid);set_guest_favorite_ids(ids);return True
def merge_guest_favorites(uid):
    from backend.services.favorite_service import add_favorites
    ids=guest_favorite_ids()
    if ids:add_favorites(uid,ids);set_guest_favorite_ids([])
    return len(ids)


THEME_COOKIE="ruidercar_theme"
def browser_theme_preference():
    try:
        value=_controller().get(THEME_COOKIE)
        if isinstance(value,dict):value=value.get("value")
        return value if value in ("dark","light") else None
    except Exception:return None
def save_browser_theme_preference(mode):
    mode=str(mode or "dark").lower()
    if mode not in ("dark","light"):return False
    try:
        expiry=datetime.now()+timedelta(days=365)
        _controller().set(THEME_COOKIE,mode,path="/",expires=expiry,max_age=365*24*60*60,secure=True,same_site="lax")
        return True
    except Exception:return False
