import streamlit as st
import numpy as np

# --- 1. 定数・設定 ---
MAP_SIZE = 6
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
    # 防御力の最大値を800に変更
    st.session_state.defense = np.random.randint(50, 801, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 61, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 100, 2: 100}
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. ロジック関数 ---
def reset_game():
    """全セッションステートを削除してリロード"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

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
        # 占領後の防御力は攻撃ユニットの半分（最低50）に再設定
        st.session_state.defense[end_pos] = max(50, unit["atk"] // 2)
        del st.session_state.units[start_pos]
        st.session_state.moved_units.append(end_pos)
        if end_pos == st.session_state.capitals[def_p]:
            st.session_state.winner = atk_p

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

# --- 4. CSS ---
st.set_page_config(layout="wide")
st.markdown("""
<style>
    .tile-container {
        position: relative;
        width: 100%;
        height: 95px;
        margin-bottom: 6px;
        border-radius: 6px;
        overflow: hidden;
    }
    .tile-bg {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 1;
        color: white;
        text-shadow: 1px 1px 3px black;
        font-weight: bold;
        line-height: 1.1;
        text-align: center;
        font-size: 0.7rem;
    }
    .owner-1 { border: 3px solid #3498DB !important; box-shadow: inset 0 0 10px #3498DB; }
    .owner-2 { border: 3px solid #E74C3C !important; box-shadow: inset 0 0 10px #E74C3C; }
    .is-selected { background-color: #F1C40F !important; color: black !important; border: 3px solid white !important; }
    .is-moved { filter: brightness(0.4) grayscale(0.8); }

    .tile-container div.stButton > button {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. サイドバーコントロール ---
if st.session_state.winner:
    st.sidebar.title("🏁 ゲーム終了")
    st.sidebar.success(f"Player {'A' if st.session_state.winner == 1 else 'B'} の勝利！")
    if st.sidebar.button("🎮 最初からやり直す", on_click=reset_game):
        pass # reset_game内でrerunされる
else:
    p = st.session_state.turn
    st.sidebar.title(f"Player {'A 🔵' if p==1 else 'B 🔴'}")
    st.sidebar.metric("軍資金", f"${st.session_state.money[p]}")

    mode, selected_u = None, None
    if st.session_state.phase == "1_EXPANSION":
        st.sidebar.info("陣地を交互に選択してください")
    elif st.session_state.phase == "2_PLACEMENT":
        mode = st.sidebar.radio("行動", ["部隊配置", "防御増強"])
        if mode == "部隊配置": selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
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
        if st.sidebar.button("次ターンへ（資金回収）"):
            for i in [1, 2]: st.session_state.money[i] += int(np.sum(st.session_state.economy[st.session_state.owner == i]))
            st.session_state.turn = 1; st.session_state.phase = "2_PLACEMENT"
            st.rerun()

# --- 6. メイン描画 ---
if st.session_state.winner:
    st.balloons()
    st.title(f"👑 Player {'A' if st.session_state.winner == 1 else 'B'} の勝利！")
    st.write("左メニューのボタンからリスタートできます。")
if 'mode' not in locals():
    mode = None
if 'selected_u' not in locals():
    selected_u = None
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        def_val = st.session_state.defense[r,c]
        eco_val = st.session_state.economy[r,c]
        unit = st.session_state.units.get((r,c))
        
        # 防御力の高さで色を変える
        if def_val > 500: t_icon, color = "⛰️", "#4A4A4A" # 険しい山
        elif def_val > 200: t_icon, color = "🌲", "#78AE27" # 深い森
        elif eco_val > 40: t_icon, color = "🌾", "#F1A20F" # 豊かな平野
        else: t_icon, color = "🍃", "#0634FF" # 草原

        special = ""
        if (r,c) == st.session_state.capitals[1]: special = "🏰A"
        elif (r,c) == st.session_state.capitals[2]: special = "🏰B"
        
        classes = f"owner-{owner}" if owner > 0 else ""
        if st.session_state.selected_pos == (r,c): classes += " is-selected"
        if (r,c) in st.session_state.moved_units: classes += " is-moved"

        with cols[c]:
            st.markdown(f"""
                <div class="tile-container">
                    <div class="tile-bg {classes}" style="background-color: {color};">
                        <div>{t_icon} {special}</div>
                        <div style="font-size: 0.6rem;">🛡️{int(def_val)} 💰{int(eco_val)}</div>
                        <div style="font-size: 1.1rem;">{unit['icon'] if unit else ""}</div>
                    </div>
            """, unsafe_allow_html=True)
            st.button("", key=f"btn{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))
            st.markdown("</div>", unsafe_allow_html=True)