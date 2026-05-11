import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み関数 ---
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

# --- 3. 共通CSS：ボタンの「皮」を剥ぎ取る ---
st.markdown("""
<style>
    /* ボタンを包むコンテナの背景を優先 */
    div.stButton {
        background-color: transparent !important;
    }

    /* ボタン本体：背景色、影、疑似要素をすべて無効化 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
    }

    /* Streamlitが後から被せてくる「グレーの膜」を完全に消す */
    div.stButton > button::before, 
    div.stButton > button::after,
    div.stButton > button:focus,
    div.stButton > button:active {
        background-color: transparent !important;
        background-image: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* 文字を最前面へ */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 SYSTEM")
p_emoji = "🔵" if st.session_state.turn == 1 else "🔴"
st.sidebar.subheader(f"ターン: {p_emoji}")

# --- 5. メインマップ ---
st.title("⚔️ $6 \\times 6$ Strategy Board")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像の事前ロード
img_data = {k: get_base64_image(v["file"]) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        conf = TILE_DEFS[t_key]
        img_b64 = img_data[t_key]
        
        b_key = f"btn_{r}_{c}"
        
        # 🟢 修正：セレクタの詳細度を最大(html body ...)に上げ、
        # ボタン自体に背景を直接叩き込む
        if img_b64:
            st.markdown(f"""
                <style>
                html body div.stButton > button[key="{b_key}"] {{
                    background-image: url("{img_b64}") !important;
                    background-size: cover !important;
                    background-position: center !important;
                    background-repeat: no-repeat !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))