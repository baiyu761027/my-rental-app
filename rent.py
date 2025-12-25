import streamlit as st
import pandas as pd
import requests
import io

# --- 1. 極致冷調科技 UI 設定 ---
st.set_page_config(page_title="物業管理終端", layout="wide")

st.markdown("""
    <style>
    /* 全域設定：純黑底 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* 標題：俐落漸層 */
    .hero-text {
        background: linear-gradient(90deg, #00F2FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 32px; font-weight: 800;
        padding: 15px 0;
    }
    
    /* 數據卡片：移除發光，改用實線邊框 */
    div[data-testid="stMetric"] {
        background: #151517 !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    /* 監控中心表格：無光暈、俐落邊框設計 */
    .stDataFrame {
        background: #000000 !important;
        border: 1px solid #444444 !important;
        border-radius: 5px !important;
    }

    /* 調整按鈕 */
    .stButton>button {
        background: linear-gradient(45deg, #00F2FF, #7000FF) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }

    /* 結算區塊文字 */
    .bill-amount { color: #FFFFFF; font-size: 48px; font-weight: 800; margin: 10px 0; }
    .bill-detail-rent { color: #00F2FF; } /* 租金青色 */
    .bill-detail-elec { color: #BF40FF; } /* 電費紫色 */

    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 資料讀取 ---
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

# --- 3. 儀表板主畫面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v2.0</p>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("管理房源", f"{len(df)} 戶")
with m2:
    total_revenue = df['租金加電費'].sum() if '租金加電費' in df.columns else 0
    st.metric("預計總營收", f"${total_revenue:,.0f}")
with m3:
    st.metric("連線狀態", "DIRECT LINK", delta="ONLINE")

st.divider()

t1, t2 = st.tabs(["📊 監控中心", "⚡ 智能結算"])

with t1:
    st.markdown("<h3 style='color:#AAAAAA; font-size: 18px;'>全房源數據庫 (無光暈冷調版)</h3>", unsafe_allow_html=True)
    # 使用表格原本的俐落質感
    st.dataframe(df, use_container_width=True, hide_index=True)

with t2:
    st.subheader("⚡ 自動化抄表結算")
    if not df.empty:
        target = st.selectbox("請選擇房號", df['房號'].astype(str))
        room = df[df['房號'].astype(str) == target].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"👤 **租客：** <span style='color:#00F2FF;'>{room['租客']}</span>", unsafe_allow_html=True)
            st.markdown(f"🏢 **公司：** <span style='color:#7000FF;'>{room['公司名稱']}</span>", unsafe_allow_html=True)
            prev_v = float(room['上次電表'])
            curr_v = st.number_input("本次讀數", value=float(room['本次電表']) if not pd.isna(room['本次電表']) else prev_v)
        
        with col2:
            rate = 5.0 
            usage = curr_v - prev_v
            elec_fee = usage * rate
            total_bill = room['租金'] + elec_fee
            
        # 結算框：保持層次感但減少過度發光
        st.markdown(f"""
            <div style="background: #111111; padding: 25px; border-radius: 15px; border: 1px solid #333; text-align: center; margin: 15px 0;">
                <p style="color:#666; margin:0; font-size: 14px;">房號 {target} 應收金額</p>
                <h1 class="bill-amount">NT$ {total_bill:,.0f}</h1>
                <p style="font-size: 16px;">
                    <span class="bill-detail-rent">租金 ${room['租金']:,}</span> 
                    <span style="color:#444;"> | </span> 
                    <span class="bill-detail-elec">電費 ${elec_fee:,.0f}</span>
                </p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 確認結算"):
            st.balloons()
