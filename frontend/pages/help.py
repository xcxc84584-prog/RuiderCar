import streamlit as st
from backend.services.admin_service import settings

def render():
    st.title("輔助與說明")
    s=settings()
    st.subheader("更新日誌")
    st.markdown(s.get("help_changelog","目前尚未提供更新日誌。"))
    st.divider();st.subheader("操作說明")
    st.markdown(s.get("help_guide","目前尚未提供操作說明。"))
