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

# --- 3. 最強の「透明化」CSS ---
st.markdown("""
<style>
    /* 1. ボタンを包む親要素(div)を画像を表示するキャンバスにする */
    div[data-testid="stButton"] {
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border-radius: 10px !important;
        height: 100px !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
    }

    /* 2. ボタン本体、およびその全ての内部要素を「物理的に透明」にする */
    /* これにより background-image: none が効いていても関係なくなります */
    div[data-testid="stButton"] > button,
    div[data-testid="stButton"] > button div,
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stButton"] > button:active,
    div[data-testid="stButton"] > button:focus {
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
    }

    /* 3. 文字だけは見えるように最前面へ（透過させない） */
    div[data-testid="stButton"] p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
        opacity: 1 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー ---
st.sidebar.title("🎮 SYSTEM")
p_mark = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
st.sidebar.markdown(f"### 現在の番\n{p_mark}")

# --- 5. メイン描画 ---
st.title("⚔️ $6 \\times 6$ World Tactics")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像の事前キャッシュ
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        img_b64 = images[t_key]
        b_key = f"b{r}_{c}"
        
        # 🟢 戦略変更：ボタン(button)ではなく、親のdivに対して背景を貼る
        if img_b64:
            st.markdown(f"""
                <style>
                /* column内の何番目のstButtonかを特定して画像を流し込む */
                div[data-testid="column"]:nth-child({c+1}) div[data-testid="stButton"]:has(button[key="{b_key}"]) {{
                    background-image: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url("{img_b64}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{TILE_DEFS[t_key]['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))