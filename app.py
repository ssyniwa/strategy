import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像をBase64に変換し、CSSで使える形式にする関数 ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            data = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{data}"
    else:
        return None

# --- 2. 地形設定と画像データの準備 ---
TILE_CONFIG = {
    "mountain": {"icon": "⛰️", "file": "mount.png"},
    "field": {"icon": "🌾", "file": "field.png"},
    "forest": {"icon": "🌲", "file": "forest.png"}
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

# --- 4. CSS: 全体スタイルと文字色 ---
st.markdown("""
<style>
    /* ボタンの基本形 */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
    }
    /* 文字の視認性向上（袋文字） */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        text-shadow: 
            2px 2px 0 #000, -2px -2px 0 #000,
            2px -2px 0 #000, -2px 2px 0 #000,
            0 2px 4px rgba(0,0,0,0.8) !important;
    }
    /* プレイヤーカラー */
    button:has(p:contains("🔵")) p { color: #3498db !important; }
    button:has(p:contains("🔴")) p { color: #e74c3c !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. サイドバー：ターンの明示表示 ---
st.sidebar.title("🎮 ゲーム情報")
current_p = st.session_state.turn
p_color = "青 (Player A)" if current_p == 1 else "赤 (Player B)"
p_emoji = "🔵" if current_p == 1 else "🔴"

# サイドバーに現在のターンを大きく表示
st.sidebar.subheader(f"現在のターン: {p_emoji}")
st.sidebar.markdown(f"### **{p_color}** の行動中です")

if st.sidebar.button("🔄 マップをリセット"):
    st.session_state.clear()
    st.rerun()

# --- 6. マップ描画と個別背景CSSの適用 ---
def get_tile_type(r, c):
    d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
    if d > 160: return "mountain"
    if e > 35: return "field"
    return "forest"

def on_cell_click(r, c):
    p = st.session_state.turn
    if st.session_state.phase == "1_EXPANSION" and st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = p
        if st.session_state.capitals[p] is None: st.session_state.capitals[p] = (r, c)
        st.session_state.turn = 3 - p
        if np.all(st.session_state.owner != 0): st.session_state.phase = "2_ACTION"

# マップループ
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        t_type = get_tile_type(r, c)
        config = TILE_CONFIG[t_type]
        b_key = f"btn_{r}_{c}"
        
        # 画像をBase64で取得
        img_b64 = get_base64_image(config["file"])
        
        if img_b64:
            # 強力なCSSセレクタで背景を上書き
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child({c+1}) button[key="{b_key}"] {{
                    background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{img_b64}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        else:
            # 画像がない場合のデバッグ用背景色
            bg_color = "#8b4513" if t_type == "mountain" else "#228b22" if t_type == "forest" else "#daa520"
            st.markdown(f"<style>button[key='{b_key}'] {{ background-color: {bg_color} !important; }}</style>", unsafe_allow_html=True)

        owner = st.session_state.owner[r,c]
        p_icon = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        label = f"{p_icon}{config['icon']}{cap}\n🛡️{st.session_state.defense[r,c]}\n💰{st.session_state.economy[r,c]}"
        
        cols[c].button(label, key=b_key, on_click=on_cell_click, args=(r,c))

# 画像ファイルがない場合の警告表示
missing_files = [v["file"] for v in TILE_CONFIG.values() if not os.path.exists(v["file"])]
if missing_files:
    st.warning(f"以下の画像ファイルが見つかりません: {', '.join(missing_files)}")