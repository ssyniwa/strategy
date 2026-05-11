import streamlit as st
import numpy as np
import base64
import os
from PIL import Image
from io import BytesIO

# --- 1. 画像を劇的に軽量化（2.6MB -> 数KB）する関数 ---
def get_base64_optimized(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    
    if os.path.exists(full_path):
        try:
            # 画像を開く
            img = Image.open(full_path)
            # ボタンサイズ（約100px）に合わせて120pxに縮小
            # これによりデータ量が1/100以下になります
            img = img.resize((120, 120), Image.LANCZOS)
            
            # メモリ上にJPEGとして保存（PNGより軽い）
            buffered = BytesIO()
            img.convert("RGB").save(buffered, format="JPEG", quality=75)
            
            # Base64に変換
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            st.error(f"Error processing {file_name}: {e}")
            return None
    return None

# --- 2. 初期設定 ---
MAP_SIZE = 6
TILE_DEFS = {
    "mountain": {"icon": "⛰️", "file": "mount.png"},
    "field": {"icon": "🌾", "file": "field.png"},
    "forest": {"icon": "🌲", "file": "forest.png"}
}

# --- 3. CSS設定 ---
st.markdown("""
<style>
    /* 全てのボタンを一旦透明な土台にする */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: #333 !important; /* 予備の色 */
        border: 1px solid rgba(255,255,255,0.2) !important;
        position: relative !important;
        overflow: hidden !important;
        z-index: 1 !important;
    }
    /* 画像を表示するレイヤー（疑似要素） */
    div.stButton > button::before {
        content: "" !important;
        position: absolute !important;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover !important;
        background-position: center !important;
        z-index: -1 !important; /* 文字の後ろ */
    }
    /* 文字の視認性向上 */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px black !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ Optimized Strategy Map")

# 🟢 ここで画像をリサイズ・軽量化して取得
images = {k: get_base64_optimized(v['file']) for k, v in TILE_DEFS.items()}

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形を適当に割り当て
        t_type = "mountain" if (r+c) % 3 == 0 else "field" if (r+c) % 3 == 1 else "forest"
        img_data = images[t_type]
        b_key = f"btn_{r}_{c}"
        
        # 🟢 短くなったBase64ならCSSが受理される
        if img_data:
            st.markdown(f"""
                <style>
                button[key="{b_key}"]::before {{
                    background-image: url("{img_data}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        cols[c].button(f"{TILE_DEFS[t_type]['icon']}", key=b_key)