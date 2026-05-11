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

# --- 3. 究極のCSS：ボタンの全階層を「透明」にする ---
st.markdown("""
<style>
    /* 1. ボタン本体の背景色を完全に抹消 */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-color: transparent !important;
        background-image: none !important; /* 標準のグラデーションを消す */
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid rgba(255,255,255,0.5) !important;
        border-radius: 10px !important;
        position: relative !important;
    }

    /* 2. 【重要】ボタンの「中身」を塗っている疑似要素を破壊する */
    div.stButton > button::before, 
    div.stButton > button::after {
        content: none !important; /* 疑似要素そのものを消去 */
        display: none !important;
    }

    /* 3. ボタン内のコンテナも透明化（最新Streamlit対策） */
    div.stButton > button > div {
        background-color: transparent !important;
    }

    /* 4. 文字を最前面に浮き上がらせる */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
        z-index: 10 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 SYSTEM")
turn_mark = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
st.sidebar.subheader(f"現在：{turn_mark}")

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
        
        # 🟢 個別ボタンに画像を叩き込む 🟢
        if img_b64:
            st.markdown(f"""
                <style>
                button[key="{b_key}"] {{
                    background-image: 
                        linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), 
                        url("{img_b64}") !important;
                }}
                </style>
                """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))