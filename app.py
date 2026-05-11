import streamlit as st
import numpy as np
import base64
import os

# --- 1. 絶対パスで画像を確実に読み込む関数 ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

# --- 2. 設定 ---
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
    st.session_state.capitals = {1: None, 2: None}

# --- 3. サイドバー：ターン表示 & 画像チェック ---
st.sidebar.title("🎮 SYSTEM")
turn_emoji = "🔵" if st.session_state.turn == 1 else "🔴"
turn_name = "Player A (青)" if st.session_state.turn == 1 else "Player B (赤)"

st.sidebar.info(f"現在のターン: {turn_emoji}\n\n**{turn_name}**")

st.sidebar.divider()
st.sidebar.write("🖼️ 画像読み込みテスト:")
for k, v in TILE_DEFS.items():
    res = "✅ OK" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), v['file'])) else "❌ Missing"
    st.sidebar.write(f"{v['icon']} {v['file']}: {res}")

# --- 4. メインマップ表示 ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100% !important; height: 100px !important;
        background-size: cover !important; background-position: center !important;
        border-radius: 10px !important; border: 1px solid white !important;
    }
    div.stButton p {
        color: white !important; font-weight: 900 !important;
        text-shadow: 2px 2px 2px black !important;
    }
</style>
""", unsafe_allow_html=True)

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
        if img_b64:
            st.markdown(f'<style>button[key="{b_key}"] {{ background-image: url("{img_b64}") !important; }}</style>', unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))