import streamlit as st
import pandas as pd
import requests
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 頁面風格：科技深色風 ---
st.set_page_config(page_title="物業管理終端", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    .hero-text { background: linear-gradient(90deg, #00F2FF, #7000FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; }
    div[data-testid="stMetric"] { background: rgba(28, 28, 30, 0.9); border: 1px solid #38383A; border-radius: 16px; padding: 20px; }
    .stButton>button { background: linear-gradient(45deg, #00F2FF, #7000FF); color: white; border-radius: 12px; font-weight: bold; width: 100%; border: none; height: 3em; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 資料讀取設定 ---
SHEET_ID = "1JjnIVHXruwhHSBvZGJE_aaLMK1da8uhKu_0fbRhnyDI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def load_data():
    response = requests.get(CSV_URL)
    response.encoding = 'utf-8'
    return pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])

df = load_data()

# --- 主畫面 ---
st.markdown('<p class="hero-text">PROPERTY MANAGEMENT TERMINAL</p>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("管理房源", f"{len(df)} 戶")
c2.metric("本月預計總收", f"${df['租金加電費'].sum():,.0f}")
c3.metric("系統連線", "DIRECT LINK ACTIVE")

st.divider()

t1, t2 = st.tabs(["📊 監控中心", "⚡ 智能結算"])

with t1:
    st.dataframe(df, use_container_width=True, hide_index=True)

with t2:
    st.subheader("⚡ 月底自動化結算")
    target = st.selectbox("選擇房號", df['房號'].astype(str))
    room = df[df['房號'].astype(str) == target].iloc[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"租客：{room['租客']} | 公司：{room['公司名稱']}")
        prev_v = float(room['上次電表'])
        curr_v = st.number_input("本次讀數", value=float(room['本次電表']) if not pd.isna(room['本次電表']) else prev_v)
    with col2:
        rate = 5.0 # 依照您的截圖設定
        usage = curr_v - prev_v
        total = room['租金'] + (usage * rate)
        
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0,242,255,0.1) 0%, rgba(112,0,255,0.1) 100%); 
                    padding: 30px; border-radius: 20px; border: 1px solid #00F2FF; text-align: center;">
            <p style="color:#888; margin:0;">房號 {target} 應收總額</p>
            <h1 style="color:#FFFFFF; margin:10px 0;">NT$ {total:,.0f}</h1>
            <p style="color:#00F2FF;">租金: ${room['租金']:,} + 電費: ${usage*rate:,.0f} ({usage}度)</p>
        </div>
    """, unsafe_allow_html=True)

    st.info("💡 提醒：若要啟用「自動寫回」功能，請參考下方步驟完成 GitHub 部署。")