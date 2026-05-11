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

# --- 3. 疑似要素を「画像レイヤー」に変えるCSS ---
st.markdown("""
<style>
    /* ボタン本体の設定 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: #222 !important; /* 画像が出ない時の予備色 */
        border: 1px solid rgba(255,255,255,0.2) !important;
        position: relative !important;
        z-index: 1 !important;
        overflow: hidden !important;
    }

    /* 🟢 ここが重要：::before を強制的に「画像を表示する板」にする */
    div.stButton > button::before {
        content: "" !important;
        display: block !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background-size: cover !important;
        background-position: center !important;
        z-index: -1 !important; /* ボタン内の文字よりは後ろに置く */
    }

    /* ボタン内の文字(p)を最前面に浮かせる */
    div.stButton p {
        position: relative !important;
        z-index: 2 !important;
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. メイン描画 ---
st.title("⚔️ Tactical Map Reconstruction")

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
        b_key = f"btn_{r}_{c}"
        
        # 🟢 セレクタで「::before」を狙って画像を貼る
        # これにより button 自体の background-image: none 設定を無視できる
        if img_b64:
            st.markdown(f"""
                <style>
                button[key="{b_key}"]::before {{
                    background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{img_b64}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{TILE_DEFS[t_key]['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))

st.sidebar.write(f"現在の番: {'🔵' if st.session_state.turn == 1 else '🔴'}")