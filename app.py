import streamlit as st
import numpy as np
import base64
from io import BytesIO

# --- 1. 基本設定 ---
MAP_SIZE = 6
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

# --- 2. セッション状態の初期化 ---
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
    # 地形タイル画像の生成を一度だけ行う（本来はGemini APIをここで1回叩く）
    # 今回は例として、地形ごとのURLやダミーデータを想定します
    st.session_state.tile_images = {
        "mountain": "https://img.freepik.com/free-photo/view-rocky-mountain-landscape_23-2150763618.jpg",
        "field": "https://img.freepik.com/free-photo/wheat-field-landscape_23-2150692723.jpg",
        "forest": "https://img.freepik.com/free-photo/deep-forest-landscape_23-2150838025.jpg"
    }

# --- 3. ロジック関数 (変更なし) ---
def handle_battle(start_pos, end_pos):
    atk_p = st.session_state.turn
    def_p = 3 - atk_p
    unit = st.session_state.units[start_pos]
    target_unit = st.session_state.units.get(end_pos)
    target_def = st.session_state.defense[end_pos]
    victory = False
    if target_unit:
        if unit["atk"] > target_unit["atk"]: victory = True
        else: del st.session_state.units[start_pos]
    else:
        if unit["atk"] > target_def: victory = True
        else:
            st.session_state.defense[end_pos] -= unit["atk"]
            st.session_state.moved_units.append(start_pos)
    if victory:
        st.session_state.owner[end_pos] = atk_p
        st.session_state.units[end_pos] = unit
        st.session_state.defense[end_pos] = max(20, unit["atk"] // 2)
        del st.session_state.units[start_pos]
        st.session_state.moved_units.append(end_pos)
        if end_pos == st.session_state.capitals[def_p]:
            st.session_state.winner = atk_p
            st.session_state.phase = "GAME_OVER"

def on_cell_click(r, c, mode=None, unit_name=None):
    if st.session_state.winner: return
    p = st.session_state.turn
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None: st.session_state.capitals[p] = (r, c)
            if np.all(st.session_state.owner != 0): st.session_state.phase = "2_PLACEMENT"
            st.session_state.turn = 3 - p
    elif st.session_state.phase == "2_PLACEMENT":
        if st.session_state.owner[r,c] == p:
            if mode == "部隊配置" and unit_name:
                u_data = UNITS[unit_name]
                if st.session_state.money[p] >= u_data["cost"]:
                    st.session_state.money[p] -= u_data["cost"]
                    st.session_state.units[(r,c)] = u_data.copy()
            elif mode == "防御増強":
                if st.session_state.money[p] >= 50:
                    st.session_state.money[p] -= 50
                    st.session_state.defense[r,c] += 100
    elif st.session_state.phase == "3_INVASION":
        if (r, c) in st.session_state.moved_units: return
        if st.session_state.selected_pos is None:
            if (r,c) in st.session_state.units and st.session_state.owner[r,c] == p:
                st.session_state.selected_pos = (r,c)
        else:
            start_pos = st.session_state.selected_pos
            if abs(r - start_pos[0]) + abs(c - start_pos[1]) == 1:
                if st.session_state.owner[r,c] == p:
                    if (r,c) not in st.session_state.units:
                        st.session_state.units[(r,c)] = st.session_state.units[start_pos]
                        del st.session_state.units[start_pos]
                        st.session_state.moved_units.append((r, c))
                else: handle_battle(start_pos, (r,c))
            st.session_state.selected_pos = None

# --- 4. CSS設定 (タイル画像と文字色の統合) ---
st.set_page_config(layout="wide")
st.title("🛡️ Tile-Based Strategy $6 \\times 6$")

# --- 5. マップとボタンの描画 ---
# サイドバー
p = st.session_state.turn
st.sidebar.header(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("資金", f"${st.session_state.money[p]}")

# 共通CSS
button_css = """
<style>
    .stButton > button {
        width: 100% !important; height: 110px !important;
        border-radius: 4px !important;
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
        box-shadow: inset 0 0 40px rgba(0,0,0,0.5) !important; /* テキストを読みやすく */
    }
    button:has(p:contains("🔵")) p { color: #2196F3 !important; font-weight: 900 !important; font-size: 16px !important; }
    button:has(p:contains("🔴")) p { color: #FF5252 !important; font-weight: 900 !important; font-size: 16px !important; }
    button:has(p:contains("🟡")) p { color: #FFEB3B !important; font-weight: 900 !important; }
    button:has(p:contains("⬛")) p { color: #BDBDBD !important; }
    .stButton p { text-shadow: 2px 2px 4px #000 !important; }
</style>
"""
st.markdown(button_css, unsafe_allow_html=True)

if st.session_state.winner:
    st.success(f"PLAYER {st.session_state.winner} WIN!"); st.stop()

# モード選択
mode, selected_u = None, None
if st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("派遣", list(UNITS.keys()))
    if st.sidebar.button("配置完了"):
        st.session_state.turn = 3 - p
        if st.session_state.turn == 1: st.session_state.phase = "3_INVASION"; st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍完了"):
        st.session_state.turn = 3 - p
        if st.session_state.turn == 1: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("次ターンへ"):
        for i in [1, 2]: st.session_state.money[i] += int(np.sum(st.session_state.economy[st.session_state.owner == i]))
        st.session_state.turn = 1; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ生成
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        def_v, eco_v = st.session_state.defense[r,c], st.session_state.economy[r,c]
        
        # タイル画像決定
        if def_v > 160: img_url = st.session_state.tile_images["mountain"]
        elif eco_v > 35: img_url = st.session_state.tile_images["field"]
        else: img_url = st.session_state.tile_images["forest"]

        # ボタン専用の背景CSSを個別に適用
        key = f"btn_{r}_{c}"
        st.markdown(f"""
            <style>
            div[data-testid="column"]:nth-child({c+1}) button[key="{key}"] {{
                background-image: url("{img_url}") !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # ラベル構築
        status = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
        if st.session_state.selected_pos == (r,c): status = "🟡"
        elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": status = "⬛"
        
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        u_icon = unit["icon"] if unit else ""
        label = f"{status}{cap}\n🛡️{def_v} 💰{eco_v}\n{u_icon}"
        
        cols[c].button(label, key=key, on_click=on_cell_click, args=(r,c, mode, selected_u))