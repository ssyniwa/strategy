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

# --- 3. 最強CSS：ボタンの全要素を透明化し、背景画像を露出させる ---
st.markdown("""
<style>
    /* 全てのボタン関連要素を透明化 */
    button[kind="secondary"], 
    button[kind="secondary"] div,
    button[kind="secondary"] p {
        background-color: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
    }

    /* 膜（擬似要素）の完全削除 */
    button[kind="secondary"]::before, 
    button[kind="secondary"]::after {
        display: none !important;
        content: none !important;
    }

    /* 基本サイズ設定 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 10px !important;
        background-size: cover !important;
        background-position: center !important;
    }

    /* 文字の視認性 */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 SYSTEM")
p_label = "A 🔵" if st.session_state.turn == 1 else "B 🔴"
st.sidebar.subheader(f"現在：Player {p_label}")

# --- 5. メインマップ ---
st.title("⚔️ $6 \\times 6$ World Tactics")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像事前ロード
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        img_b64 = images[t_key]
        b_key = f"b{r}{c}" # シンプルなキー
        
        # 🟢 セレクタに「button[kind="secondary"]」を追加して詳細度を最大化
        if img_b64:
            st.markdown(f"""
                <style>
                div.stButton > button[kind="secondary"][key="{b_key}"] {{
                    background-image: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url("{img_b64}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{TILE_DEFS[t_key]['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))