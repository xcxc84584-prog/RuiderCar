import streamlit as st
def apply_theme(mode="dark"):
    light=mode=="light"
    bg="linear-gradient(180deg,#f8fbff,#eef5ff)" if light else "radial-gradient(circle at 15% 0%,#10294a 0,#07111f 34%,#050b14 100%)"
    fg="#172033" if light else "#f3f7ff"
    side="#ffffff" if light else "#081525"
    border="#b9cee8" if light else "#1e3a5f"
    card="#ffffff" if light else "#0b1d35"
    st.markdown(f"""<style>
    .stApp{{background:{bg};color:{fg}}}
    [data-testid="stSidebar"]{{background:{side};border-right:1px solid {border}}}
    .hero{{border:1px solid #3b82f6;border-radius:16px;background:{card};margin-bottom:16px}}
    .hero h1,.hero p{{color:{fg}!important}}
    div.stButton>button{{border-radius:10px;border:1px solid #2563eb}}
    [data-testid="stMetric"]{{background:{card};border:1px solid {border};padding:12px;border-radius:14px}}
    [data-testid="stSidebarCollapsedControl"] button{{width:auto!important;min-width:128px!important;padding:6px 10px!important}}
    [data-testid="stSidebarCollapsedControl"] button svg{{display:none!important}}
    [data-testid="stSidebarCollapsedControl"] button:before{{content:"使用者選擇 >>";font-weight:700;white-space:nowrap}}
    </style>""",unsafe_allow_html=True)
