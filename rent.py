import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- 1. 極致冷調科技 UI 設定 ---
st.set_page_config(page_title="物業管理終端 v5.0", layout="wide")

st.markdown("""
    <style>
    /* 全域設定：純黑背景 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* 標題漸層 */
    .hero-text {
        background: linear-gradient(90deg, #00F2FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 32px; font-weight: 800;
        padding: 15px 0;
    }
    
    /* 數據卡片：實線邊框，移除發光 (無光暈) */
    div[data-testid="stMetric"] {
        background: #151517 !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    /* 監控中心表格：深色模式優化 */
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
        width: 100% !important;
    }

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
        # 讀取資料並排除空房號
        data = pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
        # 處理維修費用：將空值補 0 並確保為數字
        if '維修費用' in data.columns:
            data['維修費用'] = pd.to_numeric(data['維修費用'], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板主介面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v5.0</p>', unsafe_allow_html=True)

if not df.empty:
    # 統計數據計算
    paid_count = len(df[df['繳費狀態'] == '已交'])
    unpaid_count = len(df[df['繳費狀態'] == '未交'])
    repair_pending = len(df[df['維修狀態'] == '待維修'])
    # 總收入 = 租金加電費 + 維修費用
    total_revenue = df['租金加電費'].sum() + df['維修費用'].sum()

    # 數據卡片列
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("收費進度", f"{paid_count} / {len(df)} 戶", delta=f"待維修: {repair_pending} 件", delta_color="inverse")
    with m2:
        st.metric("本月預計總收入", f"${total_revenue:,.0f}", help="包含租金、電費及所有維修費用")
    with m3:
        st.metric("系統狀態", "SECURE LINK", delta="ONLINE")

    st.divider()

    t1, t2 = st.tabs(["📊 監控中心", "⚡ 智能結算"])

    with t1:
        col_chart, col_table = st.columns([1, 2.5])
        with col_chart:
            st.markdown("<p style='color:#888; font-size:14px; text-align:center;'>收費達成率</p>", unsafe_allow_html=True)
            # 圓環圖：已交 vs 未交
            fig = px.pie(names=['已交', '未交'], values=[paid_count, unpaid_count], hole=0.75,
                         color=['已交', '未交'], color_discrete_map={'已交':'#00F2FF', '未交':'#262626'})
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            fig.update_traces(textinfo='percent', textfont_size=18, textfont_color="white")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_table:
            st.markdown("<p style='color:#00F2FF; font-size:16px;'>全房源實時監控 (含維修記錄)</p>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("⚡ 自動化抄表結算")
        # 選擇房號
        target = st.selectbox("請選擇房號", df['房號'].astype(str).unique())
        room = df[df['房號'].astype(str) == target].iloc[-1]
        
        # 狀態提醒
        status_color = "#00F2FF" if room['繳費狀態'] == '已交' else "#FF4B4B"
        st.markdown(f"月份：{room['月份']} | 狀態：<span style='color:{status_color}; font-weight:bold;'>{room['繳費狀態']}</span>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"租客：{room['租客']}")
            prev_v = float(room['上次電表'])
            # 預設值帶入 Excel 現有度數
            curr_v = st.number_input("輸入本次電表讀數", value=float(room['本次電表']))
            
            # 維修費用提醒
            if room['維修費用'] > 0:
                st.warning(f"⚠️ 維修項目: {room['損壞物品']} ({room['維修狀態']})")
        
        with col_b:
            usage = curr_v - prev_v
            elec_fee = usage * 5.0
            repair_fee = float(room['維修費用'])
            # 總帳單計算公式
            total_bill = room['租金'] + elec_fee + repair_fee
            
            st.markdown(f"""
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333; text-align:center;">
                    <p style="color:#888; margin:0; font-size:14px;">本期應收總額</p>
                    <h2 style="color:#FFFFFF; margin:10px 0;">NT$ {total_bill:,.0f}</h2>
                    <p style="color:#00F2FF; font-size:12px;">租金:{room['租金']:,} + 電費:{elec_fee:,.0f} + 維修:{repair_fee:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)

        if st.button("🚀 確認結算 (請手動填回 Excel)"):
            st.balloons()
            st.success(f"{target} 房數據計算完畢！")

else:
    st.error("讀取不到資料，請檢查 Google Sheets 連結與欄位名稱。")
