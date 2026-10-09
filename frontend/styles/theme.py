import streamlit as st
def apply_theme(mode="dark"):
    light=mode=="light"
    if light:
        css="""
        .stApp{background:linear-gradient(180deg,#f8fafc 0%,#eef4fb 100%);color:#111827}
        .stApp p,.stApp span,.stApp label,.stApp li,.stApp div{color:#1f2937}
        .stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{color:#0f172a}
        [data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #cbd5e1}
        [data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#111827!important}
        .hero{border:1px solid #93c5fd;border-radius:16px;background:linear-gradient(135deg,#ffffff,#eff6ff);box-shadow:0 8px 24px rgba(15,23,42,.08);margin-bottom:16px}
        .hero h1{color:#0f172a!important}.hero p{color:#334155!important}
        [data-testid="stVerticalBlockBorderWrapper"]{background:#ffffff;border-color:#cbd5e1!important;box-shadow:0 4px 14px rgba(15,23,42,.05)}
        [data-testid="stExpander"]{background:#ffffff;border-color:#cbd5e1!important}
        [data-testid="stMetric"]{background:#ffffff;border:1px solid #cbd5e1;padding:12px;border-radius:14px}
        [data-testid="stMetricLabel"] p{color:#475569!important}
        [data-testid="stMetricValue"]{color:#0f172a!important}
        div.stButton>button{border-radius:10px;border:1px solid #2563eb;background:#ffffff;color:#1d4ed8;font-weight:650}
        div.stButton>button p{color:#1d4ed8!important}
        div.stButton>button:hover{background:#eff6ff;border-color:#1d4ed8}
        div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,textarea{background:#ffffff!important;color:#111827!important;border-color:#94a3b8!important}
        input,textarea{color:#111827!important;-webkit-text-fill-color:#111827!important}
        input::placeholder,textarea::placeholder{color:#64748b!important;-webkit-text-fill-color:#64748b!important}
        [data-baseweb="select"] span{color:#111827!important}
        [data-testid="stCaptionContainer"] p,.stCaption p{color:#475569!important}
        [data-testid="stAlert"] p,[data-testid="stAlert"] span{color:inherit!important}
        """
    else:
        css="""
        .stApp{background:radial-gradient(circle at 15% 0%,#10294a 0,#07111f 34%,#050b14 100%);color:#f3f7ff}
        [data-testid="stSidebar"]{background:#081525;border-right:1px solid #1e3a5f}
        .hero{border:1px solid #1d4ed8;border-radius:16px;background:linear-gradient(135deg,#0c1d35,#102b52);margin-bottom:16px}
        .hero h1{color:#eff6ff!important}.hero p{color:#9fc5ff!important}
        [data-testid="stMetric"]{background:#0b1d35;border:1px solid #1f4f83;padding:12px;border-radius:14px}
        div.stButton>button{border-radius:10px;border:1px solid #2563eb;background:#123b70;color:white}
        div.stButton>button:hover{border-color:#60a5fa;background:#1d4ed8;color:white}
        """
    common="""
    [data-testid="stSidebarCollapsedControl"] button{width:auto!important;min-width:128px!important;padding:6px 10px!important}
    [data-testid="stSidebarCollapsedControl"] button svg{display:none!important}
    [data-testid="stSidebarCollapsedControl"] button:before{content:"使用者選擇 >>";font-weight:700;white-space:nowrap}
    [class*="st-key-cal_"] button,[class*="st-key-cal_"] button p{color:#dc2626!important;font-weight:800!important}
    """
    st.markdown(f"<style>{css}{common}</style>",unsafe_allow_html=True)
