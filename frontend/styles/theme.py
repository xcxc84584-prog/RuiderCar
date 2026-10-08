import streamlit as st
def apply_theme():
    st.markdown('''
    <style>
    .stApp{background:radial-gradient(circle at 15% 0%,#10294a 0,#07111f 34%,#050b14 100%);color:#f3f7ff}
    [data-testid="stSidebar"]{background:#081525;border-right:1px solid #1e3a5f}
    .hero{padding:28px;border:1px solid #1d4ed8;border-radius:22px;background:linear-gradient(135deg,#0c1d35,#102b52);margin-bottom:20px}
    .hero h1{font-size:2.25rem;margin:0;color:#eff6ff}.hero p{color:#9fc5ff;font-size:1.05rem}
    .vehicle-card{height:100%;padding:18px;border-radius:18px;background:linear-gradient(145deg,#10294a,#0b1d35);border:1px solid #245a9e;box-shadow:0 12px 30px rgba(0,70,170,.20);margin-bottom:10px}
    .vehicle-card:hover{border-color:#60a5fa;box-shadow:0 14px 34px rgba(37,99,235,.30)}
    .vehicle-card h3{color:#dbeafe;margin:.2rem 0}.price{font-size:1.45rem;font-weight:800;color:#60a5fa}
    .muted{color:#91a9c6}.pill{display:inline-block;padding:4px 9px;border-radius:999px;background:#153c69;color:#bfdbfe;margin:2px;font-size:.82rem}
    div.stButton>button{border-radius:10px;border:1px solid #2563eb;background:#123b70;color:white}
    div.stButton>button:hover{border-color:#60a5fa;background:#1d4ed8;color:white}
    [data-testid="stMetric"]{background:#0b1d35;border:1px solid #1f4f83;padding:12px;border-radius:14px}
    [data-testid="stSidebarCollapsedControl"] button{width:auto!important;min-width:128px!important;padding:6px 10px!important}
    [data-testid="stSidebarCollapsedControl"] button svg{display:none!important}
    [data-testid="stSidebarCollapsedControl"] button:before{content:"使用者選擇 >>";font-weight:700;white-space:nowrap;color:#dbeafe}
    [class*="st-key-cal_"] button,[class*="st-key-cal_"] button p{color:#ff4b4b!important;font-weight:800!important}
    </style>''',unsafe_allow_html=True)
