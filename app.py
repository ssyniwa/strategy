import streamlit as st
import numpy as np

# --- 1. 基本設定とタイル画像定義 ---
MAP_SIZE = 6

# 各地形に対応するアイコンと高品質な画像URL
TILE_CONFIG = {
    "mountain": {
        "icon": "⛰️",
        "image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=300&q=80",
        "label": "山岳"
    },
    "field": {
        "icon": "🌾",
        "image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=300&q=80",
        "label": "平野"
    },
    "forest": {
        "icon": "🌲",
        "image": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=300&q=80",
        "label": "森林"
    }
}

# --- 2. セッション状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    # 防御値と経済値に基づいて地形を決定するため、初期値を生成
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.turn = 1
    st.session_state.phase = "1_EXPANSION"
    st.session_state.capitals = {1: None, 2: None}

# --- 3. 視認性向上のための共通CSS ---
st.markdown("""
<style>
    /* ボタンの共通スタイル */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 10px !important;
        margin-bottom: 5px;
    }

    /* テキスト（アイコン含む）の袋文字処理 */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        text-shadow: 
            3px 3px 0 #000, -1px -1px 0 #000,
            1px -1px 0 #000, -1px 1px 0 #000,
            0 2px 5px rgba(0,0,0,0.8) !important;
    }

    /* プレイヤー勢力の色 */
    button:has(p:contains("🔵")) p { color: #3498db !important; }
    button:has(p:contains("🔴")) p { color: #e74c3c !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. ヘルパー関数 ---
def get_tile_type(r, c):
    """防御力と経済力から地形を判定する"""
    def_v = st.session_state.defense[r,c]
    eco_v = st.session_state.economy[r,c]
    if def_v > 160: return "mountain"
    elif eco_v > 35: return "field"
    return "forest"

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

# --- 5. メインUI表示 ---
st.title("🛡️ $6 \\times 6$ Terrain Strategy")

# ターンの表示
p_label = "A 🔵" if st.session_state.turn == 1 else "B 🔴"
st.sidebar.subheader(f"現在：Player {p_label}")
if st.sidebar.button("マップ再生成"):
    st.session_state.clear()
    st.rerun()

# --- 6. マップと背景画像の動的生成 ---
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形データの取得
        t_type = get_tile_type(r, c)
        config = TILE_CONFIG[t_type]
        
        b_key = f"tile_{r}_{c}"
        
        # 🟢 ここでボタンごとに背景画像をCSSで割り当てる
        st.markdown(f"""
            <style>
            div:has(> button[key="{b_key}"]) > button {{
                background-image: 
                    linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), 
                    url("{config['image']}") !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # ラベル構築（地形アイコン + 勢力アイコン + ステータス）
        owner = st.session_state.owner[r,c]
        p_icon = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        cap_icon = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        
        label = f"{p_icon}{config['icon']}{cap_icon}\n🛡️{st.session_state.defense[r,c]}\n💰{st.session_state.economy[r,c]}"
        
        cols[c].button(label, key=b_key, on_click=on_cell_click, args=(r,c))

st.caption("※山岳(⛰️): 防御高 / 平野(🌾): 経済高 / 森林(🌲): 標準")