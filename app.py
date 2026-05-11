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

# --- 3. 基礎CSS（全ボタンを透明化して画像を見せる準備） ---
st.markdown("""
<style>
    /* 全てのボタンの背景を透明にし、中身の層を消す */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: transparent !important;
        background-image: none !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* ボタンの擬似要素（グレーの膜）を強制排除 */
    div.stButton > button::before, div.stButton > button::after {
        content: none !important;
        display: none !important;
    }

    /* 文字を浮かび上がらせる */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 3px black !important;
        z-index: 10 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：ターン表示 ---
st.sidebar.title("🎮 SYSTEM")
p_name = "Player A 🔵" if st.session_state.turn == 1 else "Player B 🔴"
st.sidebar.markdown(f"### 現在のターン\n## **{p_name}**")

# --- 5. メインマップ描画 ---
st.title("⚔️ $6 \\times 6$ World Tactics")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像データのキャッシュ（ループ内の負荷軽減）
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        conf = TILE_DEFS[t_key]
        img_b64 = images[t_key]
        
        # 🟢 セレクタを極限までシンプルに。button[key="..."] を直接叩く
        b_key = f"btn_{r}_{c}"
        
        if img_b64:
            # 擬似要素ではなく、ボタン自体の背景に直接 url を流し込む
            st.markdown(f"""
                <style>
                button[key="{b_key}"] {{
                    background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{img_b64}") !important;
                    background-size: cover !important;
                    background-position: center !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))