import streamlit as st
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

# --- 2. 設定 ---
MAP_SIZE = 6
TILE_DEFS = {
    "mountain": {"icon": "⛰️", "file": "mount.png"},
    "field": {"icon": "🌾", "file": "field.png"},
    "forest": {"icon": "🌲", "file": "forest.png"}
}

st.title("⚔️ 6x6 Custom Tactics Map")

# 画像ロード
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

# --- 3. 自作ボタンの描画 ---
# st.buttonを使わず、直接HTMLを書くことでStreamlitのCSS干渉を物理的に排除します。
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        t_key = "mountain" if (r + c) % 3 == 0 else "field" if (r + c) % 3 == 1 else "forest"
        img_data = images[t_key]
        icon = TILE_DEFS[t_key]['icon']
        
        # HTMLボタンを文字列として作成
        # inline-styleで背景を指定するため、noneに上書きされることはありません。
        custom_button_html = f"""
        <div style="
            width: 100%;
            height: 80px;
            background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('{img_data}');
            background-size: cover;
            background-position: center;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.2rem;
            text-shadow: 2px 2px 4px black;
            cursor: pointer;
            margin-bottom: 10px;
        ">
            {icon}
        </div>
        """
        cols[c].write(custom_button_html, unsafe_allow_html=True)

st.info("この方法は st.button を使っていないため、Streamlitの標準CSSによる『noneリセット』を物理的に受けません。")