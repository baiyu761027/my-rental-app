import streamlit as st
import pandas as pd
import requests
import io

# --- 1. 極致霓虹科技 UI 設定 ---
st.set_page_config(page_title="物業管理終端", layout="wide")

st.markdown("""
    <style>
    /* 全域背景與文字 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* 霓虹漸層標題 */
    .hero-text {
        background: linear-gradient(90deg, #00F2FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 36px; font-weight: 800;
        padding: 20px 0;
    }
    
    /* 數據卡片美化 */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.9) !important;
        border: 1px solid #00F2FF !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.2) !important;
    }

    /* 監控中心表格風格化 */
    .stDataFrame {
        background: rgba(20, 20, 22, 0.95) !important;
        border: 1px solid #00F2FF !important;
        border-radius: 12px !important;
        padding: 10px !important;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.1) !important;
    }

    /* 按鈕霓虹漸層 */
    .stButton>button {
        background: linear-gradient(45deg, #00F2FF, #7000FF) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        box-shadow: 0 4px 15px rgba(112, 0, 255, 0.3) !important;
    }
    
    /* 標籤頁 (Tabs) 樣式自訂 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        color: #888 !important;
        font-size: 18px !important;
    }
    .stTabs [aria-selected="true"] {
        color: #00F2FF !important;
        border-bottom: 2px solid #00F2FF !important;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 資料讀取 (讀取您的試算表) ---
SHEET_ID = "1JjnIVHXruwhHSBvZGJE_aaLMK1da8uhKu_0fbRhnyDI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(CSV_URL)
        response.encoding = 'utf-8'
        # 對齊您的表格欄位
        return pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板主畫面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v2.0</p>', unsafe_allow_html=True)

# 頂部霓虹數據框
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("管理房源", f"{len(df)} 戶")
with m2:
    # 讀取「租金加電費」欄位總和
    total_revenue = df['租金加電費'].sum() if '租金加電費' in df.columns else 0
    st.metric("本月預計總收", f"${total_revenue:,.0f}")
with m3:
    st.metric("系統連線", "DIRECT LINK", delta="ACTIVE")

st.divider()

# 分頁標籤
t1, t2 = st.tabs(["📊 監控中心", "⚡ 智能結算"])

with t1:
    st.markdown("<h3 style='color:#00F2FF;'>全房源實時監控數據庫</h3>", unsafe_allow_html=True)
    # 這裡顯示您截圖中的完整欄位
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True
    )

with t2:
    st.subheader("⚡ 月底自動化結算系統")
    if not df.empty:
        # 選擇房號邏輯
        target = st.selectbox("請選擇要結算的房號", df['房號'].astype(str))
        room = df[df['房號'].astype(str) == target].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"👤 **租客：** {room['租客']}")
            st.markdown(f"🏢 **公司名稱：** {room['公司名稱']}")
            prev_v = float(room['上次電表'])
            curr_v = st.number_input("輸入本次電表讀數", value=float(room['本次電表']) if not pd.isna(room['本次電表']) else prev_v)
        
        with col2:
            rate = 5.0 # 您表格中設定的單價
            usage = curr_v - prev_v
            elec_fee = usage * rate
            total_bill = room['租金'] + elec_fee
            
        # 結算顯示框 (霓虹漸層風格)
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0,242,255,0.1) 0%, rgba(112,0,255,0.1) 100%); 
                        padding: 30px; border-radius: 20px; border: 1px solid #00F2FF; text-align: center; margin: 20px 0;
                        box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);">
                <p style="color:#888; margin:0; font-size: 14px;">房號 {target} 當期應收帳單</p>
                <h1 style="color:#FFFFFF; margin:10px 0; font-size: 48px;">NT$ {total_bill:,.0f}</h1>
                <p style="color:#00F2FF; font-size: 16px;">
                    租金 ${room['租金']:,} + 電費 ${elec_fee:,.0f} (本期用電 {usage} 度)
                </p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("💾 確認結算並同步至 Google Sheets"):
            st.balloons()
            st.success(f"房號 {target} 的數據已計算完成！(存回功能需配置寫入權限)")
    else:
        st.warning("目前讀取不到房源資料，請檢查試算表。")e(str))
        room = df[df['房號'].astype(str) == target].iloc[0]
