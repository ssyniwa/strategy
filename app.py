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

# --- セッション状態の初期化 ---
if 'phase' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {} # {(r, c): unit_dict}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 0, 2: 0}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None # 侵攻時の移動元選択用
    st.session_state.winner = None

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
    
    target_owner = st.session_state.owner[end_pos]
    target_unit = st.session_state.units.get(end_pos)
    target_def = st.session_state.defense[end_pos]

    # 戦闘解決
    if target_unit:
        # 部隊vs部隊
        if unit["atk"] > target_unit["atk"]:
            st.session_state.battle_reports.append(f"勝利！{end_pos}の敵部隊を撃破")
            st.session_state.owner[end_pos] = atk_p
            st.session_state.units[end_pos] = unit
            st.session_state.defense[end_pos] = unit["atk"] // 2 # 占領後の初期防御
            del st.session_state.units[start_pos]
        else:
            st.session_state.battle_reports.append(f"敗北...{start_pos}の部隊が消滅")
            del st.session_state.units[start_pos]
    else:
        # 部隊vs防御力
        if unit["atk"] > target_def:
            st.session_state.battle_reports.append(f"占領！{end_pos}を奪取")
            st.session_state.owner[end_pos] = atk_p
            st.session_state.defense[end_pos] = unit["atk"] - target_def
            st.session_state.units[end_pos] = unit
            del st.session_state.units[start_pos]
        else:
            st.session_state.battle_reports.append(f"攻撃失敗！{end_pos}の防御を削りました")
            st.session_state.defense[end_pos] -= unit["atk"]

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
        if st.session_state.selected_pos is None:
            if (r,c) in st.session_state.units and st.session_state.owner[r,c] == p:
                st.session_state.selected_pos = (r,c)
        else:
            start_pos = st.session_state.selected_pos
            if (r,c) in get_neighbors(*start_pos):
                if st.session_state.owner[r,c] == p:
                    # 移動（部隊がいない場合のみ）
                    if (r,c) not in st.session_state.units:
                        st.session_state.units[(r,c)] = st.session_state.units[start_pos]
                        del st.session_state.units[start_pos]
                else:
                    # 戦闘
                    handle_battle(start_pos, (r,c))
            st.session_state.selected_pos = None

# --- メインUI ---
st.title("⚔️ 陣地取りタクティクス：完全版")

if st.session_state.phase == "GAME_OVER":
    st.balloons()
    st.header(f"🎉 プレイヤー {st.session_state.winner} の勝利！")
    if st.button("もう一度遊ぶ"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# サイドバーステータス
p = st.session_state.turn
st.sidebar.subheader(f"プレイヤー {'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("所持金", f"${st.session_state.money[p]}")

mode, selected_u = None, None

# フェーズ別コントロール
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("空き地を選んで陣地を広げてください。最初の選択地点が首都になります。")

elif st.session_state.phase == "2_PLACEMENT":
    st.sidebar.markdown("---")
    mode = st.sidebar.radio("アクション", ["部隊配置", "防御増強"])
    if mode == "部隊配置":
        selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
    if st.sidebar.button("配置完了（ターン終了）"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
        else:
            st.session_state.phase = "3_INVASION"
            st.session_state.turn = 1
        st.rerun()

elif st.session_state.phase == "3_INVASION":
    st.sidebar.warning("部隊を選択し、隣接するマスへ移動・攻撃してください。")
    if st.sidebar.button("侵攻完了（ターン終了）"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
        else:
            st.session_state.phase = "5_RESULT"
        st.rerun()

elif st.session_state.phase == "5_RESULT":
    st.sidebar.success("戦闘結果を確認してください。")
    if st.sidebar.button("次のターンへ"):
        st.session_state.money[1] += np.sum(st.session_state.owner == 1) * INCOME_PER_CELL
        st.session_state.money[2] += np.sum(st.session_state.owner == 2) * INCOME_PER_CELL
        st.session_state.turn = 1
        st.session_state.battle_reports = []
        st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ表示
if st.session_state.battle_reports:
    with st.expander("📝 直近の戦闘レポート", expanded=True):
        for msg in st.session_state.battle_reports:
            st.write(msg)

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        is_cap = (st.session_state.capitals[1] == (r,c) or st.session_state.capitals[2] == (r,c))
        
        # アイコン
        bg = "🔵" if owner == 1 else "🔴" if owner == 2 else "⬜"
        if is_cap: bg = "🏰"
        
        content = f"{unit['icon']}" if unit else f"{st.session_state.defense[r,c]}"
        if st.session_state.selected_pos == (r,c):
            bg = "🟡" # 選択中のハイライト
            
        label = f"{bg}\n{content}"
        cols[c].button(label, key=f"btn-{r}-{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))

if st.sidebar.button("強制リセット"):
    st.session_state.clear()
    st.rerun()