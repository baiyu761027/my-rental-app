import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- 1. 極致冷調科技 UI 設定 ---
st.set_page_config(page_title="物業管理終端 v4.0", layout="wide")

st.markdown("""
    <style>
    /* 全域設定：純黑底與白色字 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* 漸層標題 */
    .hero-text {
        background: linear-gradient(90deg, #00F2FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 32px; font-weight: 800;
        padding: 15px 0;
    }
    
    /* 數據摘要框：無光暈、實線邊框 */
    div[data-testid="stMetric"] {
        background: #151517 !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    /* 監控中心表格：純黑背景、無光暈 */
    .stDataFrame {
        background: #000000 !important;
        border: 1px solid #444444 !important;
        border-radius: 5px !important;
    }

    /* 按鈕樣式 */
    .stButton>button {
        background: linear-gradient(45deg, #00F2FF, #7000FF) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3em !important;
        width: 100% !important;
    }

    /* 隱藏原生頁首頁尾 */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心資料讀取 (讀取您的試算表) ---
SHEET_ID = "1JjnIVHXruwhHSBvZGJE_aaLMK1da8uhKu_0fbRhnyDI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5) # 每 5 秒自動重新抓取最新數據
def load_data():
    try:
        response = requests.get(CSV_URL)
        response.encoding = 'utf-8'
        data = pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
        # 檢查並確保有「繳費狀態」欄位
        if '繳費狀態' not in data.columns:
            data['繳費狀態'] = '未交'
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板主介面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v4.0</p>', unsafe_allow_html=True)

# 計算收費統計
if not df.empty:
    paid_count = len(df[df['繳費狀態'] == '已交'])
    unpaid_count = len(df[df['繳費狀態'] == '未交'])
    total_revenue = df['租金加電費'].sum() if '租金加電費' in df.columns else 0

    # 頂部數據摘要卡片
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("收費進度", f"{paid_count} / {len(df)} 戶", delta=f"待收 {unpaid_count} 戶", delta_color="inverse")
    with m2:
        st.metric("預計總營收", f"${total_revenue:,.0f}")
    with m3:
        st.metric("系統狀態", "SECURE LINK", delta="ONLINE")

    st.divider()

    # 分頁導覽
    t1, t2 = st.tabs(["📊 監控中心", "⚡ 智能結算"])

    with t1:
        col_chart, col_table = st.columns([1, 2.5])
        
        with col_chart:
            # 繪製圓環圖 (收費進度)
            st.markdown("<p style='color:#888; font-size:14px; text-align:center;'>收費達成率</p>", unsafe_allow_html=True)
            fig = px.pie(
                names=['已交', '未交'], 
                values=[paid_count, unpaid_count],
                hole=0.75,
                color=['已交', '未交'],
                color_discrete_map={'已交':'#00F2FF', '未交':'#262626'} # 科技青對比深灰
            )
            fig.update_layout(
                showlegend=False, margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_traces(textinfo='percent', textfont_size=18, textfont_color="white")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_table:
            # 顯示全房源表格
            st.markdown("<p style='color:#00F2FF; font-size:16px;'>全房源實時數據庫</p>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("⚡ 自動化抄表結算")
        # 選擇房號邏輯
        target = st.selectbox("請選擇要結算的房號", df['房號'].astype(str))
        room = df[df['房號'].astype(str) == target].iloc[0]
        
        # 顯示繳費狀態提醒
        status_color = "#00F2FF" if room['繳費狀態'] == '已交' else "#FF4B4B"
        st.markdown(f"本月狀態：<span style='color:{status_color}; font-weight:bold;'>{room['繳費狀態']}</span>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"👤 **租客：** {room['租客']}")
            prev_v = float(room['上次電表'])
            curr_v = st.number_input("輸入本次電表讀數", value=float(room['本次電表']) if not pd.isna(room['本次電表']) else prev_v)
        
        with col_b:
            rate = 5.0 # 每度 5 元
            usage = curr_v - prev_v
            elec_fee = usage * rate
            total_bill = room['租金'] + elec_fee
            
            # 帳單預覽框
            st.markdown(f"""
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333; text-align:center;">
                    <p style="color:#888; margin:0; font-size:14px;">應收總額</p>
                    <h2 style="color:#FFFFFF; margin:10px 0;">NT$ {total_bill:,.0f}</h2>
                    <p style="color:#00F2FF; font-size:14px;">租金 ${room['租金']:,} + 電費 ${elec_fee:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)

        if st.button("🚀 確認結算 (請手動填回 Excel)"):
            st.balloons()
            st.success(f"房號 {target} 結算成功！請記得將 {total_bill:,.0f} 元記錄至試算表。")
else:
    st.error("無法讀取資料，請檢查 Google Sheets 連結與工作表名稱。")
