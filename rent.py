import streamlit as st
import pandas as pd
import requests
import io

# --- 1. 全域極致科技風設定 ---
st.set_page_config(page_title="物業管理系統", layout="wide")

st.markdown("""
    <style>
    /* 整體背景與字體 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* 漸層標題 */
    .hero-text {
        background: linear-gradient(90deg, #00F2FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 36px; font-weight: 800;
        padding: 20px 0;
    }
    
    /* 數據卡片美化 */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.9);
        border: 1px solid #00F2FF;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
    }
    
    /* 表格美化 */
    .stDataFrame {
        border: 1px solid #38383A;
        border-radius: 12px;
    }
    
    /* 按鈕漸層 */
    .stButton>button {
        background: linear-gradient(45deg, #00F2FF, #7000FF) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.6) !important;
        transform: scale(1.02);
    }
    
    /* 標籤頁 (Tabs) 風格 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1C1C1E;
        border-radius: 10px 10px 0 0;
        color: #888;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(0deg, #00F2FF, transparent) !important;
        color: #00F2FF !important;
        border-bottom: 2px solid #00F2FF !important;
    }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心連線 (固定連結您的試算表) ---
SHEET_ID = "1JjnIVHXruwhHSBvZGJE_aaLMK1da8uhKu_0fbRhnyDI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(CSV_URL)
        response.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板內容 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v2.0</p>', unsafe_allow_html=True)

# 頂部霓虹數據框
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("管理房源", f"{len(df)} 戶")
with m2:
    st.metric("預計總營收", f"${df['租金加電費'].sum():,.0f}")
with m3:
    st.metric("系統連線", "SECURE LINK", delta="ONLINE")

st.divider()

# 分頁標籤
t1, t2 = st.tabs(["📊 房源監控中心", "⚡ 智能抄表結算"])

with t1:
    st.markdown("<h3 style='color:#00F2FF;'>全房源即時數據</h3>", unsafe_allow_html=True)
    # 使用最新的資料編輯器，風格與結算統一
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
    )

with t2:
    st.subheader("⚡ 月底自動化結算")
    if not df.empty:
        target = st.selectbox("選擇要結算的房號", df['房號'].astype(str))
        room = df[df['房號'].astype(str) == target].iloc[0]
