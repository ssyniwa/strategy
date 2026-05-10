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
    # 防御力 (50-200) と 資金力 (10-50) をランダム生成
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 0, 2: 0}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. 戦闘ロジック ---
def handle_battle(start_pos, end_pos):
    atk_p = st.session_state.turn
    def_p = 3 - atk_p
    unit = st.session_state.units[start_pos]
    target_unit = st.session_state.units.get(end_pos)
    target_def = st.session_state.defense[end_pos]

    victory = False
    if target_unit:
        if unit["atk"] > target_unit["atk"]:
            st.session_state.battle_reports.append(f"勝利！{end_pos}の部隊を撃破")
            victory = True
        else:
            st.session_state.battle_reports.append(f"敗北...{start_pos}の部隊が消滅")
            del st.session_state.units[start_pos]
    else:
        if unit["atk"] > target_def:
            st.session_state.battle_reports.append(f"占領！{end_pos}を奪取")
            victory = True
        else:
            st.session_state.battle_reports.append(f"攻撃失敗！{end_pos}の防御を削りました")
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

# --- 4. クリックイベント ---
def on_cell_click(r, c, mode=None, unit_name=None):
    if st.session_state.winner: return
    p = st.session_state.turn
    
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None:
                st.session_state.capitals[p] = (r, c)
            if np.all(st.session_state.owner != 0):
                st.session_state.phase = "2_PLACEMENT"
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
                else:
                    handle_battle(start_pos, (r,c))
            st.session_state.selected_pos = None

# --- 5. UI構築 ---
st.title("🏙️ 領土戦略シミュレーター")

if st.session_state.phase == "GAME_OVER":
    st.success(f"🎊 プレイヤー {st.session_state.winner} の勝利！")
    if st.button("再挑戦"): st.session_state.clear(); st.rerun()
    st.stop()

# サイドバー設定
st.sidebar.title(f"Player {'A 🔵' if st.session_state.turn==1 else 'B 🔴'}")
st.sidebar.metric("現在の軍資金", f"${st.session_state.money[st.session_state.turn]}")

mode, selected_u = None, None
if st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("行動", ["部隊配置", "防御増強"])
    if mode == "部隊配置":
        selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
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
    if st.sidebar.button("資金回収して次ターンへ"):
        # 占領地点ごとの経済力(economy)を合計して加算
        for i in [1, 2]:
            income = np.sum(st.session_state.economy[st.session_state.owner == i])
            st.session_state.money[i] += income
        st.session_state.turn = 1; st.session_state.battle_reports = []; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# CSSでボタンのテキストを小さく調整
st.markdown("<style>div.stButton > button { font-size: 10px !important; padding: 2px !important; height: 100px !important; }</style>", unsafe_allow_html=True)

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        def_val = st.session_state.defense[r,c]
        eco_val = st.session_state.economy[r,c]
        is_cap1 = (st.session_state.capitals[1] == (r,c))
        is_cap2 = (st.session_state.capitals[2] == (r,c))
        
        # アイコンとステータス表示の組み立て
        bg = "🔵" if owner == 1 else "🔴" if owner == 2 else "⬜"
        if is_cap1: bg = "🏰(A)"
        elif is_cap2: bg = "🏰(B)"
        
        if st.session_state.selected_pos == (r,c): bg = "🟡"
        elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": bg = "⬛"
            
        unit_icon = unit["icon"] if unit else "空"
        
        # ボタン内のテキスト：所属、防御力、資金力、部隊を4行で表示
        label = f"{bg}\n🛡️{def_val}\n💰{eco_val}\n👤{unit_icon}"
        cols[c].button(label, key=f"x{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))

if st.session_state.battle_reports:
    with st.expander("📝 記録"):
        for msg in st.session_state.battle_reports: st.write(msg)