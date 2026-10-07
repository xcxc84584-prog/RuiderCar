import os
def secret(name,default=None):
    if os.getenv(name):return os.getenv(name)
    try:
        import streamlit as st
        return st.secrets.get(name,default)
    except Exception:
        return default
