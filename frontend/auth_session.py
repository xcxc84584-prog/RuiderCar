import streamlit as st
from backend.services.session_service import create_login_session,restore_login_session,revoke_login_session
TOKEN_PARAM="_bd_session"
def _get_token():
    try:
        value=st.query_params.get(TOKEN_PARAM)
        if isinstance(value,list):return value[-1] if value else None
        return value
    except Exception:return None
def restore_browser_session():
    if st.session_state.get("user"):return
    token=_get_token()
    if not token:return
    user=restore_login_session(token)
    if user:
        st.session_state.user=user
        st.session_state.auth_token=token
    else:
        try:del st.query_params[TOKEN_PARAM]
        except Exception:pass
def establish_browser_session(user):
    token=create_login_session(user["id"])
    st.session_state.user=user
    st.session_state.auth_token=token
    st.query_params[TOKEN_PARAM]=token
def logout_browser_session():
    token=st.session_state.get("auth_token") or _get_token()
    if token:revoke_login_session(token)
    try:del st.query_params[TOKEN_PARAM]
    except Exception:pass
    st.session_state.pop("auth_token",None)
    st.session_state.pop("user",None)
