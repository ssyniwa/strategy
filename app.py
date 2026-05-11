import streamlit as st
import numpy as np

# --- 1. 定数・設定 ---
MAP_SIZE = 6
COST_DEFENSE_UP = 50
DEFENSE_UP_AMOUNT = 150  # 増加量をアップ
MAX_DEFENSE_DISPLAY = 999 # 表示上の目安

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
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE)).astype(float)
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 100, 2: 100}
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. ロジック関数 ---
def reset_game():
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
        st.session_state.defense[end_pos] = max(50.0, unit["atk"] // 1.5) # 占領後の防御力を高めに設定
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

# --- 4. CSS (レイアウト調整) ---
st.set_page_config(layout="wide")
st.markdown("""
<style>
    .tile-container {
        position: relative;
        width: 100%;
        height: 105px;
        margin-bottom: 8px;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #444;
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
        text-align: center;
        transition: 0.2s;
    }
    .owner-1 { border: 4px solid #3498DB !important; background-image: linear-gradient(135deg, rgba(52,152,219,0.2) 0%, transparent 100%); }
    .owner-2 { border: 4px solid #E74C3C !important; background-image: linear-gradient(135deg, rgba(231,76,60,0.2) 0%, transparent 100%); }
    .is-selected { background-color: #F1C40F !important; color: black !important; border: 4px solid white !important; }
    .is-moved { filter: brightness(0.3) saturate(0.5); }

    .tile-container div.stButton > button {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. UI構築 ---
if st.session_state.winner:
    st.balloons()
    st.title(f"👑 Player {'A' if st.session_state.winner==1 else 'B'} の完全勝利！")
    if st.button("🔄 ゲームをリセットして最初から遊ぶ", type="primary", use_container_width=True):
        reset_game()
    st.stop()

# サイドバー
p = st.session_state.turn
st.sidebar.title(f"Player {'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("現在の軍資金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("拡大フェーズ: 交互に空地を占領してください。")
elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("アクション選択", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("雇用ユニット", list(UNITS.keys()))
    if st.sidebar.button("このフェーズを終了"):
        if st.session_state.turn == 1: st.session_state.turn = 2
        else: st.session_state.phase = "3_INVASION"; st.session_state.turn = 1; st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍を終了"):
        if st.session_state.turn == 1: st.session_state.turn = 2; st.session_state.moved_units = []
        else: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("領地から資金を回収"):
        for i in [1, 2]: st.session_state.money[i] += int(np.sum(st.session_state.economy[st.session_state.owner == i]))
        st.session_state.turn = 1; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# --- マップ表示 ---
st.title("🗺️ World Tactics: 6x6 Map")

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        def_val = int(st.session_state.defense[r,c])
        eco_val = st.session_state.economy[r,c]
        unit = st.session_state.units.get((r,c))
        
        # 地形スタイル決定
        if def_val > 400: t_icon, color = "🏰", "#2C3E50" # 要塞化
        elif def_val > 250: t_icon, color = "⛰️", "#5D6D7E" # 堅牢
        elif eco_val > 35: t_icon, color = "🌾", "#D4AC0D" # 豊穣
        else: t_icon, color = "🌲", "#1E8449" # 標準

        special = ""
        if (r,c) == st.session_state.capitals[1]: special = " (HQ-A)"
        elif (r,c) == st.session_state.capitals[2]: special = " (HQ-B)"
        
        classes = f"owner-{owner}" if owner > 0 else ""
        if st.session_state.selected_pos == (r,c): classes += " is-selected"
        if (r,c) in st.session_state.moved_units: classes += " is-moved"

        with cols[c]:
            st.markdown(f"""
                <div class="tile-container">
                    <div class="tile-bg {classes}" style="background-color: {color};">
                        <div style="font-size: 0.6rem; opacity: 0.9;">{t_icon}{special}</div>
                        <div style="font-size: 0.75rem;">🛡️{def_val} 💰{eco_val}</div>
                        <div style="font-size: 1.3rem; margin-top: 2px;">{unit['icon'] if unit else ""}</div>
                    </div>
            """, unsafe_allow_html=True)
            st.button("", key=f"btn{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))
            st.markdown("</div>", unsafe_allow_html=True)