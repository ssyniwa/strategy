import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み関数 ---
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

# --- 3. 強力なCSS（ボタンを透明化し、枠線を整える） ---
st.markdown("""
<style>
    /* ボタンが入っている外枠(div)の設定 */
    div[data-testid="stButton"] {
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    /* ボタンそのものを「完全に透明」にする（画像はこの下のdivに見える） */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-color: rgba(0,0,0,0.2) !important; /* 少し暗くして文字を見やすく */
        background-image: none !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
        color: white !important;
        transition: 0.2s !important;
    }

    /* ホバーしたときだけ少し白くする */
    div.stButton > button:hover {
        background-color: rgba(255,255,255,0.1) !important;
        border-color: white !important;
    }

    /* 文字の袋文字設定 */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 3px #000, -2px -2px 3px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 SYSTEM")
p_name = "Player A 🔵" if st.session_state.turn == 1 else "Player B 🔴"
st.sidebar.success(f"現在のターン: {p_name}")

# --- 5. メインマップ描画 ---
st.title("⚔️ $6 \\times 6$ World Tactics")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        conf = TILE_DEFS[t_key]
        img_b64 = get_base64_image(conf["file"])
        
        b_key = f"b_{r}_{c}"
        
        # 🟢 【解決策】ボタン本体ではなく、ボタンの親要素(stButton)に画像を貼る
        if img_b64:
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child({c+1}) div[data-testid="stButton"]:has(button[key="{b_key}"]) {{
                    background-image: url("{img_b64}") !important;
                }}
                </style>
                """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))