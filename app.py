import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

# --- 2. 初期設定 ---
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

# --- 3. 最強CSS：ボタンの全階層を透明にし、背景画像を強制露出させる ---
st.markdown("""
<style>
    /* 全てのボタンの背景・影・疑似要素を根こそぎ透明化 */
    div.stButton > button,
    div.stButton > button:focus,
    div.stButton > button:active,
    div.stButton > button:hover,
    div.stButton > button div {
        background-color: transparent !important;
        background-image: none !important; /* 一旦リセット */
        box-shadow: none !important;
        outline: none !important;
    }

    /* 疑似要素（グレーの膜）を物理的に消去 */
    div.stButton > button::before, 
    div.stButton > button::after {
        content: none !important;
        display: none !important;
    }

    /* ボタンの基本形を定義 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
    }

    /* 文字を浮かび上がらせる */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
        pointer-events: none; /* 文字への反応を無効化 */
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 SYSTEM")
p_emoji = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
st.sidebar.subheader(f"現在：{p_emoji}")

# --- 5. メインマップ ---
st.title("⚔️ $6 \\times 6$ Tactical Map")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像データの準備
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        conf = TILE_DEFS[t_key]
        img_b64 = images[t_key]
        b_key = f"b_{r}_{c}"
        
        # 🟢 ここが重要：個別ボタンの「background-image」を「!important」で強制注入
        if img_b64:
            st.markdown(f"""
                <style>
                /* html body から記述することで詳細度を最大化 */
                html body div.stButton > button[key="{b_key}"] {{
                    background-image: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url("{img_b64}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))