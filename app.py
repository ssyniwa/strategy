import streamlit as st
import numpy as np

# --- 1. 定数・設定 ---
MAP_SIZE = 5
COST_DEFENSE_UP = 50
DEFENSE_UP_AMOUNT = 100

UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

# --- 2. セッション状態の初期化 ---
if 'phase' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 200, 2: 200}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. ロジック関数 ---
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
                if st.session_state.money[p] >= COST_DEFENSE_UP:
                    st.session_state.money[p] -= COST_DEFENSE_UP
                    st.session_state.defense[r,c] += DEFENSE_UP_AMOUNT
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

# --- 4. 【修正】地形と所有者の色分け描画ロジック ---
def get_terrain_style(r, c):
    def_val = st.session_state.defense[r,c]
    eco_val = st.session_state.economy[r,c]
    owner = st.session_state.owner[r,c]
    
    # 基本の地形
    if def_val > 160: icon, base_color = "⛰️", "#7D7D7D" # 山
    elif eco_val > 35: icon, base_color = "🌾", "#F1C40F" # 平野
    else: icon, base_color = "🌲", "#27AE60" # 森

    # 所有者に応じた色の上書き
    bg_color = base_color
    border = "1px solid #444"
    
    if owner == 1:
        bg_color = "#3498DB" # 鮮やかな青
        border = "3px solid #005599"
    elif owner == 2:
        bg_color = "#E74C3C" # 鮮やかな赤
        border = "3px solid #990000"

    # 選択中や行動済みのハイライト
    if st.session_state.selected_pos == (r,c):
        bg_color = "#FFF176"
    elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION":
        bg_color = "#424242"

    return icon, bg_color, border

# --- 5. UI構築 ---
st.set_page_config(layout="wide")
st.title("🗺️ 領土拡大ストラテジー")

st.markdown("""
<style>
    .stButton > button {
        width: 100% !important; height: 110px !important;
        color: white !important; text-shadow: 1px 2px 2px black;
        font-weight: bold !important; font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# 勝利画面
if st.session_state.winner:
    st.balloons(); st.success(f"🎊 PLAYER {st.session_state.winner} WINS!"); st.stop()

# サイドバー
p = st.session_state.turn
st.sidebar.title(f"Turn: Player {'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("資金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("拡大フェーズ: 未占領のマス(灰色)を選んでください。")
elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("派遣", list(UNITS.keys()))
    if st.sidebar.button("配置終了"):
        if st.session_state.turn == 1: st.session_state.turn = 2
        else: st.session_state.phase = "3_INVASION"; st.session_state.turn = 1; st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍終了"):
        if st.session_state.turn == 1: st.session_state.turn = 2; st.session_state.moved_units = []
        else: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("資金回収"):
        for i in [1, 2]: st.session_state.money[i] += np.sum(st.session_state.economy[st.session_state.owner == i])
        st.session_state.turn = 1; st.session_state.battle_reports = []; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        unit = st.session_state.units.get((r,c))
        def_val, eco_val = st.session_state.defense[r,c], st.session_state.economy[r,c]
        icon, bg_color, border = get_terrain_style(r, c)
        
        # 首都と部隊
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        u_disp = unit["icon"] if unit else ""
        
        label = f"{icon}{cap}\n🛡️{def_val} 💰{eco_val}\n{u_disp}"
        
        # 拡大フェーズで未占領のマスを分かりやすくするために
        # 所有者がいない(0)かつ拡大フェーズの場合のみ、背景を少しグレーにする
        current_bg = bg_color if st.session_state.owner[r,c] != 0 else "#DDDDDD"
        current_color = "white" if st.session_state.owner[r,c] != 0 else "#333333"

        st.markdown(f"""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child({c+1}) button[key="k{r}{c}"] {{
                background-color: {current_bg} !important;
                border: {border} !important;
                color: {current_color} !important;
            }}
            </style>
        """, unsafe_allow_html=True)
        
        cols[c].button(label, key=f"k{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))