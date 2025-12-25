import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- 1. UI 設定 (俐落冷調科技風) ---
st.set_page_config(page_title="物業管理終端 v7.2", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    .hero-text { background: linear-gradient(90deg, #00F2FF, #7000FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; padding: 15px 0; }
    div[data-testid="stMetric"] { background: #151517 !important; border: 1px solid #333333 !important; border-radius: 10px !important; padding: 15px !important; }
    .stDataFrame { background: #000000 !important; border: 1px solid #444444 !important; }
    .stButton>button { background: linear-gradient(45deg, #00F2FF, #7000FF) !important; color: white !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 8px !important; }
    .msg-box { background: #111; border: 1px dashed #00F2FF; padding: 15px; border-radius: 8px; font-family: monospace; color: #00F2FF; margin-top: 10px; }
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 資料讀取 ---
SHEET_ID = "1JjnIVHXruwhHSBvZGJE_aaLMK1da8uhKu_0fbRhnyDI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
SHEET_LINK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit" # 您的試算表編輯連結

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(CSV_URL)
        response.encoding = 'utf-8'
        # 精確讀取試算表並排除空房號
        data = pd.read_csv(io.StringIO(response.text)).dropna(subset=['房號'])
        # 確保數值欄位格式化
        num_cols = ['租金', '上次電表', '本次電表', '維修費用', '租金加電費']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. 儀表板主介面 ---
st.markdown('<p class="hero-text">🛸 PROPERTY TERMINAL v7.2</p>', unsafe_allow_html=True)

if not df.empty:
    # 統計數據計算
    paid_count = len(df[df['繳費狀態'] == '已繳'])
    unpaid_count = len(df[df['繳費狀態'] == '未繳'])
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("收費達成率", f"{paid_count} / {len(df)} 戶", delta=f"未繳: {unpaid_count}")
    with m2:
        # 提供快捷按鈕跳轉至 Google Sheets 查看「儲存格圖片」
        st.link_button("📂 開啟試算表對帳 (圖檔)", SHEET_LINK)
    with m3:
        st.metric("連線狀態", "SECURE", delta="CONNECTED")

    st.divider()

    t1, t2 = st.tabs(["📊 房源監控中心", "⚡ 智能結算與通知"])

    with t1:
        col_chart, col_table = st.columns([1, 2.5])
        with col_chart:
            # 圓環圖顯示收費進度
            fig = px.pie(names=['已繳', '未繳'], values=[paid_count, unpaid_count], hole=0.75,
                         color=['已繳', '未繳'], color_discrete_map={'已繳':'#00F2FF', '未繳':'#262626'})
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            fig.update_traces(textinfo='percent', textfont_size=18, textfont_color="white")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        with col_table:
            # 顯示完整資料表
            st.dataframe(df, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("⚡ 抄表結算與房客通知生成")
        target = st.selectbox("請選擇房號", df['房號'].astype(str).unique())
        room = df[df['房號'].astype(str) == target].iloc[-1]
        
        c1, c2 = st.columns(2)
        with c1:
            status_color = "#00F2FF" if room['繳費狀態'] == '已繳' else "#FF4B4B"
            st.markdown(f"👤 **租客：** {room['租客']} | **狀態：** <span style='color:{status_color};'>{room['繳費狀態']}</span>", unsafe_allow_html=True)
            prev_v = float(room['上次電表'])
            curr_v = st.number_input("輸入本次電表讀數", value=float(room['本次電表']))
            st.info("💡 提醒：若需確認匯款截圖，請點擊上方按鈕開啟試算表查看")

        with c2:
            usage = curr_v - prev_v
            elec_fee = usage * 5.0
            total_rent = room['租金'] + elec_fee
            repair_fee = room['維修費用']
            
            # 帳單預覽
            st.markdown(f"""
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333; margin-bottom:15px;">
                    <p style="color:#00F2FF; margin:0; font-size:14px;">🏠 房租與電費結算</p>
                    <h2 style="margin:10px 0;">NT$ {total_rent:,.0f}</h2>
                    <p style="color:#666; font-size:12px;">(租金:{room['租金']:,} + 電費:{elec_fee:,.0f})</p>
                </div>
            """, unsafe_allow_html=True)

            # 生成 LINE 通知文字
            msg = f"【{room['月份']}月房租通知】\n房號：{target}\n租客：{room['租客']} 您好\n---\n● 本期電費：${elec_fee:,.0f} (用電{usage:,.1f}度)\n● 本期房租：${room['租金']:,}\n● 應繳總額：${total_rent:,.0f}\n---\n※ 請於本月 5 號前匯款，並傳截圖告知，謝謝！"
            
            if st.button("📋 生成 LINE 通知訊息"):
                st.markdown(f'<div class="msg-box">{msg.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                st.code(msg)
                st.success("訊息已生成！長按下方代碼框即可複製")

            if repair_fee > 0:
                st.warning(f"🔧 另有獨立維修費：${repair_fee:,.0f} ({room['損壞物品']})")

else:
    st.error("讀取不到資料，請檢查 Google Sheets 連結。")
