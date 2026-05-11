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

# --- 3. 構造を破壊しない最強CSS ---
st.markdown("""
<style>
    /* 1. ボタンを包む親コンテナを「画像表示板」にする */
    div[data-testid="stButton"] {
        height: 100px !important;
        background-size: cover !important;
        background-position: center !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        overflow: hidden !important;
    }

    /* 2. ボタン本体と、その中にある全divを「透明」にする */
    /* これにより、ボタンに background: none !important が付いていても関係なくなります */
    div[data-testid="stButton"] button,
    div[data-testid="stButton"] button div,
    div[data-testid="stButton"] button:hover,
    div[data-testid="stButton"] button:active,
    div[data-testid="stButton"] button:focus {
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        height: 100px !important;
        margin: 0 !important;
    }

    /* 3. テキストだけは最前面に白く表示 */
    div[data-testid="stButton"] p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ 6x6 World Tactics")

# 画像ロード
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形タイプを決定
        t_key = "mountain" if (r + c) % 3 == 0 else "field" if (r + c) % 3 == 1 else "forest"
        img_data = images[t_key]
        b_key = f"b_{r}_{c}"
        
        # 🟢 ここがポイント：
        # ボタンそのものではなく、その親である「div[data-testid="stButton"]」を狙う。
        # 親要素に画像を貼ることで、ボタンの background: none 設定を物理的に回避します。
        if img_data:
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child({c+1}) div[data-testid="stButton"]:has(button[key="{b_key}"]) {{
                    background-image: url("{img_data}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        cols[c].button(f"{TILE_DEFS[t_key]['icon']}\n{r},{c}", key=b_key)