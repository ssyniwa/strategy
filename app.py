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
            # PNG/JPGどちらでも動くように調整
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
    st.session_state.capitals = {1: None, 2: None}

# --- 3. サイドバー：ターン表示とデバッグ ---
st.sidebar.title("🎮 SYSTEM")
turn_mark = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
st.sidebar.subheader(f"現在：{turn_mark}")

st.sidebar.divider()
st.sidebar.write("🖼️ 画像読み込みテスト:")
for k, v in TILE_DEFS.items():
    res = "✅ OK" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), v['file'])) else "❌ Missing"
    st.sidebar.write(f"{v['icon']} {v['file']}: {res}")

# --- 4. 共通スタイル（重要：!important を多用して標準スタイルに勝つ） ---
st.markdown("""
<style>
    /* ボタンそのものの背景と枠線をリセット */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-color: transparent !important; /* 標準のグレーを消す */
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 10px !important;
        transition: 0.2s !important;
    }
    
    /* マウスホップ時の演出 */
    div.stButton > button:hover {
        border-color: #F1C40F !important;
        box-shadow: 0 0 10px rgba(241, 196, 15, 0.5) !important;
    }

    /* テキストの縁取り（袋文字） */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 
            2px 2px 0 #000, -1px -1px 0 #000, 
            1px -1px 0 #000, -1px 1px 0 #000 !important;
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

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
        
        # 🟢 ここが「画像が映らない」を解決する最重要CSS 🟢
        # button[key] を直接狙い、背景を上書きします
        if img_b64:
            st.markdown(f"""
                <style>
                button[key="{b_key}"] {{
                    background-image: 
                        linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), 
                        url("{img_b64}") !important;
                }}
                </style>
                """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}{conf['icon']}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))