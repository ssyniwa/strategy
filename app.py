import streamlit as st
import numpy as np

# --- 設定 ---
MAP_SIZE = 5
INCOME_PER_CELL = 10
COST_DEFENSE_UP = 50
DEFENSE_UP_AMOUNT = 100

UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

# --- 初期化 ---
if 'phase' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {} 
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 0, 2: 0}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.winner = None
    # 行動済み部隊を管理するリスト
    st.session_state.moved_units = []

# --- ロジック関数 ---
def get_neighbors(r, c):
    res = []
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < MAP_SIZE and 0 <= nc < MAP_SIZE:
            res.append((nr, nc))
    return res

def handle_battle(start_pos, end_pos):
    atk_p = st.session_state.turn
    def_p = 3 - atk_p
    unit = st.session_state.units[start_pos]
    target_unit = st.session_state.units.get(end_pos)
    target_def = st.session_state.defense[end_pos]

    # 戦闘解決
    if target_unit:
        if unit["atk"] > target_unit["atk"]:
            st.session_state.battle_reports.append(f"勝利！{end_pos}の敵部隊を撃破")
            st.session_state.owner[end_pos] = atk_p
            st.session_state.units[end_pos] = unit
            st.session_state.defense[end_pos] = unit["atk"] // 2
            del st.session_state.units[start_pos]
            st.session_state.moved_units.append(end_pos) # 移動先で行動済み
        else:
            st.session_state.battle_reports.append(f"敗北...{start_pos}の部隊が消滅")
            del st.session_state.units[start_pos]
    else:
        if unit["atk"] > target_def:
            st.session_state.battle_reports.append(f"占領！{end_pos}を奪取")
            st.session_state.owner[end_pos] = atk_p
            st.session_state.defense[end_pos] = max(10, unit["atk"] - target_def)
            st.session_state.units[end_pos] = unit
            del st.session_state.units[start_pos]
            st.session_state.moved_units.append(end_pos) # 移動先で行動済み
        else:
            st.session_state.battle_reports.append(f"攻撃失敗！{end_pos}の防御を削りました")
            st.session_state.defense[end_pos] -= unit["atk"]
            st.session_state.moved_units.append(start_pos) # 移動できなかったが行動済み

    # 首都チェック
    if end_pos == st.session_state.capitals[def_p] and st.session_state.owner[end_pos] == atk_p:
        st.session_state.winner = atk_p
        st.session_state.phase = "GAME_OVER"

def on_cell_click(r, c, mode=None, unit_name=None):
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
            if mode == "部隊配置":
                u_data = UNITS[unit_name]
                if st.session_state.money[p] >= u_data["cost"]:
                    st.session_state.money[p] -= u_data["cost"]
                    st.session_state.units[(r,c)] = u_data.copy()
            elif mode == "防御増強":
                if st.session_state.money[p] >= COST_DEFENSE_UP:
                    st.session_state.money[p] -= COST_DEFENSE_UP
                    st.session_state.defense[r,c] += DEFENSE_UP_AMOUNT

    elif st.session_state.phase == "3_INVASION":
        # 行動済みのマスなら選択不可
        if (r, c) in st.session_state.moved_units:
            st.warning("この部隊は既に行動済みです。")
            return

        if st.session_state.selected_pos is None:
            if (r,c) in st.session_state.units and st.session_state.owner[r,c] == p:
                st.session_state.selected_pos = (r,c)
        else:
            start_pos = st.session_state.selected_pos
            if (r,c) in get_neighbors(*start_pos):
                if st.session_state.owner[r,c] == p:
                    if (r,c) not in st.session_state.units:
                        st.session_state.units[(r,c)] = st.session_state.units[start_pos]
                        del st.session_state.units[start_pos]
                        st.session_state.moved_units.append((r, c)) # 移動完了
                else:
                    handle_battle(start_pos, (r,c))
            st.session_state.selected_pos = None

# --- メインUI ---
st.title("⚔️ 陣地取りタクティクス")

if st.session_state.phase == "GAME_OVER":
    st.balloons()
    st.header(f"🎉 プレイヤー {st.session_state.winner} の勝利！")
    if st.button("もう一度遊ぶ"):
        st.session_state.clear()
        st.rerun()
    st.stop()

p = st.session_state.turn
st.sidebar.subheader(f"プレイヤー {'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("所持金", f"${st.session_state.money[p]}")

mode, selected_u = None, None

if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("空き地を選んで陣地を広げてください。")

elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("アクション", ["部隊配置", "防御増強"])
    if mode == "部隊配置":
        selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
    if st.sidebar.button("配置完了（ターン終了）"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
        else:
            st.session_state.phase = "3_INVASION"
            st.session_state.turn = 1
            st.session_state.moved_units = [] # リセット
        st.rerun()

elif st.session_state.phase == "3_INVASION":
    st.sidebar.warning("部隊を選んで隣接マスへ移動・攻撃！")
    if st.sidebar.button("侵攻完了（ターン終了）"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
            st.session_state.moved_units = [] # プレイヤー交代時にリセット
        else:
            st.session_state.phase = "5_RESULT"
        st.rerun()

elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("次のターンへ"):
        for i in [1, 2]:
            st.session_state.money[i] += np.sum(st.session_state.owner == i) * INCOME_PER_CELL
        st.session_state.turn = 1
        st.session_state.battle_reports = []
        st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ表示
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        is_cap = (st.session_state.capitals[1] == (r,c) or st.session_state.capitals[2] == (r,c))
        
        bg = "🔵" if owner == 1 else "🔴" if owner == 2 else "⬜"
        if is_cap: bg = "🏰"
        
        # 選択中ハイライト
        if st.session_state.selected_pos == (r,c):
            bg = "🟡"
        # 行動済みを視覚的に表現（灰色っぽく）
        elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION":
            bg = "⬛"
            
        content = f"{unit['icon']}" if unit else f"{st.session_state.defense[r,c]}"
        cols[c].button(f"{bg}\n{content}", key=f"{r}-{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))

if st.session_state.battle_reports:
    st.divider()
    for msg in st.session_state.battle_reports:
        st.caption(msg)