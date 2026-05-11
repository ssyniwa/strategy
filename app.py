import streamlit as st
import numpy as np
import base64
import os

# --- 1. 基本設定 ---
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

# --- 2. 初期化 ---
if 'phase' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 100, 2: 100}
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. CSS：透明ボタンハイブリッド方式 ---
st.markdown("""
<style>
    .tile-container {
        position: relative;
        width: 100%;
        height: 110px;
        margin-bottom: 10px;
        border-radius: 8px;
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
        transition: 0.3s;
        color: white;
        text-shadow: 1px 1px 2px black;
        font-weight: bold;
        line-height: 1.1;
        text-align: center;
        font-size: 0.8rem;
    }
    .owner-1 { border: 4px solid #3498DB !important; box-shadow: inset 0 0 15px #3498DB; }
    .owner-2 { border: 4px solid #E74C3C !important; box-shadow: inset 0 0 15px #E74C3C; }
    .is-selected { background-color: #F1C40F !important; color: black !important; }
    .is-moved { filter: brightness(0.4) grayscale(0.6); }

    .tile-container div.stButton > button {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10;
    }
    .tile-container div.stButton > button:hover {
        background-color: rgba(255,255,255,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. ロジック関数 ---
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

# --- 5. UI構築 ---
p = st.session_state.turn
st.sidebar.title(f"Player {'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("軍資金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "2_PLACEMENT":
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

if st.session_state.winner:
    st.balloons(); st.success(f"勝利者: PLAYER {st.session_state.winner}"); st.stop()

# --- マップ描画 ---
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        def_val = st.session_state.defense[r,c]
        eco_val = st.session_state.economy[r,c]
        unit = st.session_state.units.get((r,c))
        
        # 地形スタイル決定
        if def_val > 150: t_icon, color = "⛰️", "#7D7D7D"
        elif eco_val > 35: t_icon, color = "🌾", "#F4D03F"
        else: t_icon, color = "🌲", "#27AE60"

        # 特殊ラベル
        special = ""
        if (r,c) == st.session_state.capitals[1]: special = "🏰A"
        elif (r,c) == st.session_state.capitals[2]: special = "🏰B"
        
        # 状態クラス
        classes = f"owner-{owner}" if owner > 0 else ""
        if st.session_state.selected_pos == (r,c): classes += " is-selected"
        if (r,c) in st.session_state.moved_units: classes += " is-moved"

        with cols[c]:
            st.markdown(f"""
                <div class="tile-container">
                    <div class="tile-bg {classes}" style="background-color: {color};">
                        <div>{t_icon} {special}</div>
                        <div style="font-size: 0.7rem;">🛡️{def_val} 💰{eco_val}</div>
                        <div style="font-size: 1.2rem;">{unit['icon'] if unit else ""}</div>
                    </div>
            """, unsafe_allow_html=True)
            
            # 透明ボタン
            st.button("", key=f"btn{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))
            st.markdown("</div>", unsafe_allow_html=True)