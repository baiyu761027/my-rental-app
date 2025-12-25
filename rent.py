import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- 1. 極致冷調科技 UI 設定 ---
st.set_page_config(page_title="物業管理終端 v6.0", layout="wide")

st.markdown("""
    <style>
    /* 全域設定：純黑背景 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* 漸層標題 */
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

    /* 監控中心表格風格 */
    .stDataFrame {
        background: #000000 !important;
        border: 1px solid #444444 !important;
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
        data = pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
        # 確保費用欄位為數字格式，空值補 0
        data['維修費用'] = pd.to_numeric(data['維修費用'], errors='coerce').fillna(0)
        data['租金加電費'] = pd.to_numeric(data['租金加電費'], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板主介面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v6.0</p>', unsafe_allow_html=True)

if not df.empty:
    # 統計數據計算
    paid_count = len(df[df['繳費狀態'] == '已交'])
    unpaid_count = len(df[df['繳費狀態'] == '未交'])
    total_rent_due = df['租金加電費'].sum()
    total_repair_fee = df['維修費用'].sum()
    repair_pending = len(df[df['維修狀態'] == '待維修'])

    # 數據摘要卡片
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("收費達成率", f"{paid_count} / {len(df)} 戶", delta=f"待收房租: ${total_rent_due:,.0f}")
    with m2:
        # 維修費獨立統計項目
        st.metric("維修費總計", f"${total_repair_fee:,.0f}", help="當前試算表中記錄的所有維修支出")
    with m3:
        st.metric("待處理維修", f"{repair_pending} 件", delta="ACTIVE", delta_color="inverse")

    st.divider()

    t1, t2 = st.tabs(["📊 房源監控", "⚡ 結算與維修查詢"])

    with t1:
        col_chart, col_table = st.columns([1, 2.5])
        with col_chart:
            st.markdown("<p style='color:#888; font-size:14px; text-align:center;'>收費達成百分比</p>", unsafe_allow_html=True)
            # 圓環圖：顯示房租收齊進度
            fig = px.pie(names=['已交', '未交'], values=[paid_count, unpaid_count], hole=0.75,
                         color=['已交', '未交'], color_discrete_map={'已交':'#00F2FF', '未交':'#262626'})
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            fig.update_traces(textinfo='percent', textfont_size=18, textfont_color="white")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        with col_table:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("⚡ 智能抄表結算與維修詳情")
        target = st.selectbox("選擇要查詢的房號", df['房號'].astype(str).unique())
        room = df[df['房號'].astype(str) == target].iloc[-1]
        
        status_color = "#00F2FF" if room['繳費狀態'] == '已交' else "#FF4B4B"
        st.markdown(f"**月份：{room['月份']} | 繳費狀態：** <span style='color:{status_color};'>{room['繳費狀態']}</span>", unsafe_allow_html=True)
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"👤 **租客：** {room['租客']}")
            prev_v = float(room['上次電表'])
            curr_v = st.number_input("輸入本次電表讀數", value=float(room['本次電表']))
            
            # 維修紀錄獨立顯示區塊，不併入帳單金額
            st.info(f"🛠️ **維修項目詳情**\n\n- 損壞物品：{room['損壞物品']}\n- 維修狀態：{room['維修狀態']}")
        
        with col_right:
            usage = curr_v - prev_v
            elec_fee = usage * 5.0
            rent_total = room['租金'] + elec_fee
            repair_fee = float(room['維修費用'])
            
            # 分離式帳單視圖
            st.markdown(f"""
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333; margin-bottom:15px;">
                    <p style="color:#00F2FF; margin:0; font-size:14px;">🏠 應收房租總計</p>
                    <h2 style="margin:10px 0;">NT$ {rent_total:,.0f}</h2>
                    <p style="color:#666; font-size:12px;">(租金:{room['租金']:,} + 電費:{elec_fee:,.0f})</p>
                </div>
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #7000FF; border-left: 5px solid #7000FF;">
                    <p style="color:#BF40FF; margin:0; font-size:14px;">🔧 維修費用 (獨立紀錄)</p>
                    <h2 style="margin:5px 0; color:#FFFFFF;">NT$ {repair_fee:,.0f}</h2>
                    <p style="color:#666; font-size:12px;">*此項不計入上述房租總額*</p>
                </div>
            """, unsafe_allow_html=True)

        if st.button("🚀 確認結算結果"):
            st.balloons()
            st.success(f"{target} 房計算完成！請記得將結果手動記錄至您的試算表中。")
else:
    st.error("讀取不到資料，請檢查 Google Sheets 連結與欄位名稱。")
