import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- 1. UI 設定 (維持俐落冷調) ---
st.set_page_config(page_title="物業管理終端 v4.0", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    .hero-text { background: linear-gradient(90deg, #00F2FF, #7000FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; padding: 15px 0; }
    div[data-testid="stMetric"] { background: #151517 !important; border: 1px solid #333333 !important; border-radius: 10px !important; }
    .stDataFrame { background: #000000 !important; border: 1px solid #444444 !important; }
    header, footer {visibility: hidden;}
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
        # 讀取全部資料並移除空房號
        data = pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板主介面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v4.0</p>', unsafe_allow_html=True)

if not df.empty:
    # 修正：精確對比您的「繳費狀態」欄位內容
    paid_count = len(df[df['繳費狀態'] == '已交'])
    unpaid_count = len(df[df['繳費狀態'] == '未交'])
    total_revenue = df['租金加電費'].sum()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("收費進度", f"{paid_count} / {len(df)} 戶", delta=f"待收 {unpaid_count} 戶", delta_color="inverse")
    with m2:
        st.metric("預計總營收", f"${total_revenue:,.0f}")
    with m3:
        st.metric("系統狀態", "SECURE LINK", delta="ONLINE")

    st.divider()

    t1, t2 = st.tabs(["📊 監控中心", "⚡ 智能結算"])

    with t1:
        col_chart, col_table = st.columns([1, 2.5])
        
        with col_chart:
            st.markdown("<p style='color:#888; font-size:14px; text-align:center;'>收費達成率</p>", unsafe_allow_html=True)
            # 圓環圖數據修正
            fig = px.pie(
                names=['已交', '未交'], 
                values=[paid_count, unpaid_count],
                hole=0.75,
                color=['已交', '未交'],
                color_discrete_map={'已交':'#00F2FF', '未交':'#262626'}
            )
            fig.update_layout(
                showlegend=False, margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_traces(textinfo='percent', textfont_size=18, textfont_color="white")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_table:
            # 完整顯示表格內容
            st.dataframe(df, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("⚡ 自動化抄表結算")
        target = st.selectbox("請選擇房號", df['房號'].astype(str).unique())
        room = df[df['房號'].astype(str) == target].iloc[-1] # 抓取最後一筆紀錄 (最新月份)
        
        status_color = "#00F2FF" if room['繳費狀態'] == '已交' else "#FF4B4B"
        st.markdown(f"月份：{room['月份']} | 狀態：<span style='color:{status_color}; font-weight:bold;'>{room['繳費狀態']}</span>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"租客：{room['租客']}")
            prev_v = float(room['上次電表'])
            curr_v = st.number_input("輸入本次電表讀數", value=float(room['本次電表']))
        
        with col_b:
            usage = curr_v - prev_v
            elec_fee = usage * 5.0
            total_bill = room['租金'] + elec_fee
            st.markdown(f"""
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333; text-align:center;">
                    <p style="color:#888; margin:0; font-size:14px;">應收總額</p>
                    <h2 style="color:#FFFFFF; margin:10px 0;">NT$ {total_bill:,.0f}</h2>
                </div>
            """, unsafe_allow_html=True)
else:
    st.error("讀取不到資料，請確認 Google Sheets 權限與欄位名稱。")
