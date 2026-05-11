import streamlit as st
import numpy as np
import base64
import os

# --- 1. 絶対パスでの画像読み込み ---
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

# --- 3. CSS: ここでボタンの「色」を完全に消し去ります ---
st.markdown("""
<style>
    /* ボタンの枠組みを透明にし、背景画像を最優先にする */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-color: transparent !important; /* ←これが無いと画像が隠れます */
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 10px !important;
        padding: 0 !important;
        display: block !important;
    }

    /* マウスを乗せたときに少し明るくする */
    div.stButton > button:hover {
        border-color: #F1C40F !important;
        background-color: rgba(255,255,255,0.1) !important;
    }

    /* 文字を浮かび上がらせる */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 2px #000, -1px -1px 2px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示とデバッグ ---
st.sidebar.title("🎮 SYSTEM")
turn_mark = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
st.sidebar.subheader(f"現在：{turn_mark}")

st.sidebar.divider()
st.sidebar.write("🖼️ 画像読み込みテスト:")
for k, v in TILE_DEFS.items():
    res = "✅ OK" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), v['file'])) else "❌ Missing"
    st.sidebar.write(f"{v['icon']} {v['file']}: {res}")

# --- 5. メインマップ ---
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
        
        # 🟢 個別のボタンに画像を割り当てる 🟢
        if img_b64:
            st.markdown(f"""
                <style>
                button[key="{b_key}"] {{
                    background-image: url("{img_b64}") !important;
                }}
                </style>
                """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))