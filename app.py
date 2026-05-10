import streamlit as st
import numpy as np

# --- 1. 基本設定 ---
MAP_SIZE = 6
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

# --- 2. セッション初期化 ---
if 'owner' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 300, 2: 300}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None
    
    # 地形画像URL (Geminiで生成した画像のURLを想定)
    st.session_state.tile_images = {
        "mountain": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=200&q=80",
        "field": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=200&q=80",
        "forest": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=200&q=80"
    }

# --- 3. ロジック関数 (on_cell_click 等) ---
def on_cell_click(r, c, mode=None, unit_name=None):
    p = st.session_state.turn
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None: st.session_state.capitals[p] = (r, c)
            if np.all(st.session_state.owner != 0): st.session_state.phase = "2_PLACEMENT"
            st.session_state.turn = 3 - p
    # ... (前回のロジックをそのまま維持)

# --- 4. 共通CSS (文字色とボタンの基本構造) ---
st.markdown("""
<style>
    /* 全ボタン共通の基本設定 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        border-radius: 5px !important;
        background-size: cover !important;
        background-position: center !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: white !important;
        padding: 0 !important;
    }
    
    /* 文字色を際立たせるための影 */
    div.stButton p {
        text-shadow: 2px 2px 4px rgba(0,0,0,1), -1px -1px 0 rgba(0,0,0,1), 1px -1px 0 rgba(0,0,0,1), -1px 1px 0 rgba(0,0,0,1), 1px 1px 0 rgba(0,0,0,1) !important;
        line-height: 1.2 !important;
    }

    /* プレイヤーカラーの定義 */
    button:has(p:contains("🔵")) p { color: #3498DB !important; font-weight: bold !important; }
    button:has(p:contains("🔴")) p { color: #E74C3C !important; font-weight: bold !important; }
    button:has(p:contains("🟡")) p { color: #F1C40F !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. メインUI ---
st.title("🗺️ $6 \\times 6$ Tile Strategy")

# サイドバー処理 (省略なし)
p = st.session_state.turn
st.sidebar.header(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
mode = st.sidebar.radio("コマンド", ["移動/攻撃", "部隊配置", "防御増強"]) if st.session_state.phase != "1_EXPANSION" else None
selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys())) if mode == "部隊配置" else None

if st.sidebar.button("フェーズ/ターン終了"):
    if st.session_state.phase == "2_PLACEMENT": st.session_state.phase = "3_INVASION"
    elif st.session_state.phase == "3_INVASION": 
        st.session_state.turn = 3 - p
        if st.session_state.turn == 1:
            for i in [1, 2]: st.session_state.money[i] += int(np.sum(st.session_state.economy[st.session_state.owner == i]))
            st.session_state.phase = "2_PLACEMENT"
    st.rerun()

# --- 6. マップ描画と個別CSSの動的注入 ---
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        def_v, eco_v = st.session_state.defense[r,c], st.session_state.economy[r,c]
        
        # 地形による画像選別
        if def_v > 160: img = st.session_state.tile_images["mountain"]
        elif eco_v > 35: img = st.session_state.tile_images["field"]
        else: img = st.session_state.tile_images["forest"]

        # ボタンのキー
        b_key = f"tile_{r}_{c}"
        
        # 🟢 ここが重要: 各ボタンの「親要素(div)」を特定して背景画像を流し込む
        # Streamlitのボタンは div[data-testid="stButton"] の中に生成されるため
        # 独自のkeyを持つボタンを探してその親要素にスタイルを適用する
        st.markdown(f"""
            <style>
                div:has(> button[key="{b_key}"]) > button {{
                    background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{img}") !important;
                }}
            </style>
        """, unsafe_allow_html=True)

        # ラベル構築
        status = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        u_icon = unit["icon"] if unit else ""
        label = f"{status}\nDef:{def_v}\nEco:{eco_v}\n{u_icon}"
        
        cols[c].button(label, key=b_key, on_click=on_cell_click, args=(r,c, mode, selected_u))