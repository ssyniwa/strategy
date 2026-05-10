import streamlit as st
import numpy as np

# --- 1. 基本設定 ---
MAP_SIZE = 6
# サンプル画像URL（確実に表示される公開画像を使用。Geminiで生成したURLに置き換え可）
TILE_URLS = {
    "mountain": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=200&q=80",
    "field": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=200&q=80",
    "forest": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=200&q=80"
}

# --- 2. 初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.turn = 1
    st.session_state.phase = "1_EXPANSION"
    st.session_state.capitals = {1: None, 2: None}

# --- 3. 共通CSS (文字の視認性向上) ---
st.markdown("""
<style>
    /* 全ボタン共通: 背景画像の土台を作る */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
        padding: 0 !important;
    }
    /* テキストに黒い縁取り（袋文字）をつけて背景に埋もれないようにする */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 
            2px 2px 0 #000, -2px -2px 0 #000,
            2px -2px 0 #000, -2px 2px 0 #000,
            0 2px 0 #000, 0 -2px 0 #000,
            2px 0 0 #000, -2px 0 0 #000 !important;
    }
    /* 陣地ごとの文字色 */
    button:has(p:contains("🔵")) p { color: #5dade2 !important; }
    button:has(p:contains("🔴")) p { color: #ec7063 !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. マップ描画 ---
st.title("⚔️ $6 \\times 6$ Tactical Map")

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        def_v = st.session_state.defense[r,c]
        eco_v = st.session_state.economy[r,c]
        owner = st.session_state.owner[r,c]
        
        # 地形判定
        if def_v > 160: tile_type = "mountain"
        elif eco_v > 35: tile_type = "field"
        else: tile_type = "forest"
        
        img_url = TILE_URLS[tile_type]
        b_key = f"tile_{r}_{c}"
        
        # 🟢 【重要】個別のボタン背景を指定する最強のCSSセレクタ
        # data-testidでボタンを特定し、その直下の疑似要素や背景を上書き
        st.markdown(f"""
            <style>
            button[key="{b_key}"] {{
                background-image: 
                    linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), 
                    url("{img_url}") !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
        status = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        label = f"{status}\n🛡️{def_v}\n💰{eco_v}"
        
        cols[c].button(label, key=b_key)