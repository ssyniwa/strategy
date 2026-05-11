import streamlit as st
import numpy as np
import base64
import os
from PIL import Image
from io import BytesIO

# --- 1. 画像を軽量化してBase64化する関数 ---
def get_base64_image_optimized(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    
    if os.path.exists(full_path):
        try:
            img = Image.open(full_path)
            # ボタンサイズに合わせて150pxに縮小（これで十分綺麗です）
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            
            buffered = BytesIO()
            # JPEG形式で圧縮（quality=70で劇的に軽くなります）
            img.convert("RGB").save(buffered, format="JPEG", quality=70)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            return None
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

# --- 3. CSS：疑似要素を画像レイヤーにする（これが一番確実） ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: #333 !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        position: relative !important;
        z-index: 1 !important;
        overflow: hidden !important;
    }

    /* 画像を表示する専用レイヤー */
    div.stButton > button::before {
        content: "" !important;
        display: block !important;
        position: absolute !important;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover !important;
        background-position: center !important;
        z-index: -1 !important;
    }

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
st.title("⚔️ Optimized Tactical Map")

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# 画像を最適化して事前ロード
images = {k: get_base64_image_optimized(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        img_data = images[t_key]
        b_key = f"b_{r}_{c}"
        
        if img_data:
            st.markdown(f"""
                <style>
                button[key="{b_key}"]::before {{
                    background-image: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url("{img_data}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))