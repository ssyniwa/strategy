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

# --- 3. 最強の「レイヤー破壊」CSS ---
st.markdown("""
<style>
    /* 1. ボタンを包む親要素(stButton)の設定 */
    div[data-testid="stButton"] {
        height: 100px !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        background-size: cover !important;
        background-position: center !important;
    }

    /* 2. ボタン本体：背景を透明にし、上書きを完全に防ぐ */
    div[data-testid="stButton"] > button {
        background-color: transparent !important;
        background-image: none !important; /* ここで none を指定して標準を消す */
        border: none !important;
        width: 100% !important;
        height: 100% !important;
        box-shadow: none !important;
    }

    /* 3. Streamlitの「グレーの膜」を物理的に消し飛ばす */
    div[data-testid="stButton"] > button::before,
    div[data-testid="stButton"] > button::after {
        display: none !important;
    }

    /* 4. 文字をくっきりさせる（背景が透明なので、背後の画像が見える） */
    div[data-testid="stButton"] p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 GAME INFO")
p_emoji = "🔵" if st.session_state.turn == 1 else "🔴"
st.sidebar.markdown(f"### 現在のターン: {p_emoji}")

# --- 5. メイン描画 ---
st.title("⚔️ $6 \\times 6$ Tactical Map")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像キャッシュ
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        img_b64 = images[t_key]
        b_key = f"key_{r}_{c}"
        
        # 🟢 【解決策】
        # nth-child で列を指定し、さらに has(button[key=...]) で特定のボタンの「親div」を狙い撃ち
        if img_b64:
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child({c+1}) div[data-testid="stButton"]:has(button[key="{b_key}"]) {{
                    background-image: url("{img_b64}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{TILE_DEFS[t_key]['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))