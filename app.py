import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像をBase64に変換する関数 ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    else:
        # ファイルがない場合のフォールバック（色指定など）
        return ""

# --- 2. 地形設定と画像読み込み ---
# 生成したファイル名に合わせて読み込みます
TILE_CONFIG = {
    "mountain": {
        "icon": "⛰️",
        "img_base64": get_base64_image("mount.png"),
        "label": "山岳"
    },
    "field": {
        "icon": "🌾",
        "img_base64": get_base64_image("field.png"),
        "label": "平野"
    },
    "forest": {
        "icon": "🌲",
        "img_base64": get_base64_image("forest.png"),
        "label": "森林"
    }
}

# --- 3. セッション状態の初期化 ---
MAP_SIZE = 6
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.turn = 1
    st.session_state.phase = "1_EXPANSION"
    st.session_state.capitals = {1: None, 2: None}

# --- 4. 共通スタイル (袋文字・ボタンサイズ) ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 10px !important;
    }
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        text-shadow: 
            2px 2px 0 #000, -2px -2px 0 #000,
            2px -2px 0 #000, -2px 2px 0 #000,
            0 2px 4px rgba(0,0,0,0.8) !important;
    }
    button:has(p:contains("🔵")) p { color: #3498db !important; }
    button:has(p:contains("🔴")) p { color: #e74c3c !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. 地形判定とクリック処理 ---
def get_tile_type(r, c):
    def_v = st.session_state.defense[r,c]
    eco_v = st.session_state.economy[r,c]
    if def_v > 160: return "mountain"
    elif eco_v > 35: return "field"
    return "forest"

def on_cell_click(r, c):
    p = st.session_state.turn
    if st.session_state.phase == "1_EXPANSION" and st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = p
        if st.session_state.capitals[p] is None: st.session_state.capitals[p] = (r, c)
        st.session_state.turn = 3 - p
        if np.all(st.session_state.owner != 0): st.session_state.phase = "2_ACTION"

# --- 6. メイン描画 ---
st.title("⚔️ $6 \\times 6$ Custom Terrain Map")

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        t_type = get_tile_type(r, c)
        config = TILE_CONFIG[t_type]
        b_key = f"tile_{r}_{c}"
        
        # Base64データをCSSに注入
        bg_img = config['img_base64']
        st.markdown(f"""
            <style>
            div:has(> button[key="{b_key}"]) > button {{
                background-image: 
                    linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), 
                    url("{bg_img}") !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # ラベル構築
        owner = st.session_state.owner[r,c]
        p_icon = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        cap_icon = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        label = f"{p_icon}{config['icon']}{cap_icon}\n🛡️{st.session_state.defense[r,c]}\n💰{st.session_state.economy[r,c]}"
        
        cols[c].button(label, key=b_key, on_click=on_cell_click, args=(r,c))

st.sidebar.write(f"現在のフェーズ: {st.session_state.phase}")
if st.sidebar.button("リセット"):
    st.session_state.clear()
    st.rerun()