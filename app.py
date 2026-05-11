import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み（MIMEタイプ対応） ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        ext = file_name.split(".")[-1].lower()
        mime = f"image/{ext}" if ext in ["png", "jpg", "jpeg"] else "image/png"
        with open(full_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:{mime};base64,{data}"
    return None

# --- 2. 設定とセッション初期化 ---
MAP_SIZE = 6
TILE_DEFS = {
    "mountain": {"icon": "⛰️", "file": "mount.png"},
    "field": {"icon": "🌾", "file": "field.png"},
    "forest": {"icon": "🌲", "file": "forest.png"}
}

if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.turn = 1

# --- 3. グローバルCSS（ボタンの共通設定） ---
st.markdown("""
<style>
    /* ボタンの標準色を完全に排除し、枠線とサイズを固定 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: transparent !important;
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
        padding: 0 !important;
    }
    /* ボタン内部の疑似要素（グレーの膜）を強制削除 */
    div.stButton > button::before {
        content: none !important;
        display: none !important;
    }
    /* 文字の視認性向上 */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 3px black, -1px -1px 3px black !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー（ターン表示） ---
st.sidebar.title("🎮 SYSTEM")
turn_mark = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
st.sidebar.subheader(f"現在：{turn_mark}")

# --- 5. メインマップ描画 ---
st.title("⚔️ $6 \\times 6$ World Tactics")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# マップ生成
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形判定
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        conf = TILE_DEFS[t_key]
        
        # 個別キーの設定
        b_key = f"tile_{r}_{c}"
        img_b64 = get_base64_image(conf["file"])
        
        # 🟢 ここが最終回答：セレクタを極限まで具体化
        if img_b64:
            st.markdown(f"""
                <style>
                /* data-testidを利用して特定のボタンのみを狙い撃ち */
                div[data-testid="column"]:nth-child({c+1}) button[key="{b_key}"] {{
                    background-image: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url("{img_b64}") !important;
                }}
                </style>
                """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))