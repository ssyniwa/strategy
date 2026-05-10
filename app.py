import streamlit as st
import numpy as np

# --- 1. 基本設定と画像URL ---
MAP_SIZE = 6

# 確実に表示される高品質なタイル画像
# ※Gemini APIで生成した画像を表示する場合は、ここを生成したURLやBase64に変更します
TILE_IMAGES = {
    "mountain": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=300&q=80",
    "field": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=300&q=80",
    "forest": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=300&q=80"
}

# --- 2. セッション状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.turn = 1
    st.session_state.phase = "1_EXPANSION"
    st.session_state.capitals = {1: None, 2: None}

# --- 3. 強力なCSS注入 (ここが画像表示のキモ) ---
st.markdown("""
<style>
    /* ボタン全体の基本スタイル */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
        border-radius: 10px !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }

    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255,255,255,0.5) !important;
    }

    /* テキストの視認性（袋文字） */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        font-size: 14px !important;
        line-height: 1.2 !important;
        text-shadow: 
            2px 2px 0 #000, -2px -2px 0 #000,
            2px -2px 0 #000, -2px 2px 0 #000,
            0 2px 0 #000, 0 -2px 0 #000,
            2px 0 0 #000, -2px 0 0 #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. ロジック関数 ---
def on_cell_click(r, c):
    p = st.session_state.turn
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None:
                st.session_state.capitals[p] = (r, c)
            st.session_state.turn = 3 - p
            if np.all(st.session_state.owner != 0):
                st.session_state.phase = "2_ACTION"

# --- 5. メインUI ---
st.title("🗺️ $6 \\times 6$ Fantasy World")

# サイドバー
st.sidebar.header(f"Player {'A 🔵' if st.session_state.turn == 1 else 'B 🔴'} の番")
if st.sidebar.button("リセット"):
    st.session_state.clear()
    st.rerun()

# --- 6. マップ描画ロジック ---
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        def_v = st.session_state.defense[r,c]
        eco_v = st.session_state.economy[r,c]
        owner = st.session_state.owner[r,c]
        
        # 地形タイプによる画像決定
        if def_v > 160: 
            img_url = TILE_IMAGES["mountain"]
        elif eco_v > 35: 
            img_url = TILE_IMAGES["field"]
        else: 
            img_url = TILE_IMAGES["forest"]
            
        b_key = f"btn_{r}_{c}"
        
        # 個別ボタンへの背景画像流し込み（最強のCSSセレクタ）
        # data-testid="stBaseButton-secondary" などStreamlitの標準クラスを狙い撃ち
        st.markdown(f"""
            <style>
            div:has(> button[key="{b_key}"]) > button {{
                background-image: 
                    linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), 
                    url("{img_url}") !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # ラベル構築
        status = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        label = f"{status}{cap}\n🛡️{def_v}\n💰{eco_v}"
        
        cols[c].button(label, key=b_key, on_click=on_cell_click, args=(r,c))

# --- 7. 補足説明 ---
st.info("※画像が表示されない場合は、ブラウザで 'Ctrl + F5' (強制リロード) をお試しください。")