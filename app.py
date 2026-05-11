import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み関数（絶対パス & MIMEタイプ指定） ---
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
    st.session_state.capitals = {1: None, 2: None}

# --- 3. サイドバー：ターン表示の強化 ---
st.sidebar.title("🛡️ 司令部")

# 現在のプレイヤー情報を取得
curr_p = st.session_state.turn
p_name = "Player A (青)" if curr_p == 1 else "Player B (赤)"
p_emoji = "🔵" if curr_p == 1 else "🔴"

# 視認性の高いターン表示
st.sidebar.markdown(f"""
    <div style="padding:15px; border-radius:10px; background-color: rgba(255,255,255,0.1); border: 2px solid {'#3498db' if curr_p==1 else '#e74c3c'};">
        <h2 style="margin:0; text-align:center;">{p_emoji} {p_name}</h2>
        <p style="margin:0; text-align:center; font-weight:bold;">あなたのターンです</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🔄 マップをリセット"):
    st.session_state.clear()
    st.rerun()

# --- 4. 共通CSS（透明化と袋文字） ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-color: transparent !important;
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 10px !important;
    }
    div.stButton > button::before { display: none !important; } /* 膜を消す */
    
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 3px #000, -1px -1px 3px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. メインマップ ---
st.title("⚔️ $6 \\times 6$ World Tactics")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        # 首都の設定（各プレイヤーの最初の1手）
        if st.session_state.capitals[st.session_state.turn] is None:
            st.session_state.capitals[st.session_state.turn] = (r, c)
        st.session_state.turn = 3 - st.session_state.turn

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        conf = TILE_DEFS[t_key]
        img_b64 = get_base64_image(conf["file"])
        
        b_key = f"b_{r}_{c}"
        
        # 個別背景の適用
        if img_b64:
            st.markdown(f"""
                <style>
                button[key="{b_key}"] {{ background-image: url("{img_b64}") !important; }}
                </style>
            """, unsafe_allow_html=True)
        
        owner = st.session_state.owner[r,c]
        p_icon = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        is_cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        
        label = f"{p_icon}{conf['icon']}{is_cap}\n🛡️{d}\n💰{e}"
        cols[c].button(label, key=b_key, on_click=on_click, args=(r,c))