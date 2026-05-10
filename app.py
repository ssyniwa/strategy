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
    st.session_state.selected_unit_pos = None
# --- ヘルパー関数 ---
def get_neighbors(r, c):
    res = []
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < MAP_SIZE and 0 <= nc < MAP_SIZE:
            res.append((nr, nc))
    return res

def process_battle(attacker_pos, defender_pos, unit_data):
    atk_p = st.session_state.turn
    def_p = 3 - atk_p
    target_def = st.session_state.defense[defender_pos]
    
    # 敵部隊がいるか確認
    target_unit = st.session_state.units.get(defender_pos)
    
    if target_unit:
        # 部隊間戦闘
        if unit_data["atk"] > target_unit["atk"]:
            st.session_state.battle_reports.append(f"勝利！ {defender_pos} の敵部隊を撃破")
            st.session_state.owner[defender_pos] = atk_p
            st.session_state.units[defender_pos] = unit_data
            del st.session_state.units[attacker_pos]
        else:
            st.session_state.battle_reports.append(f"敗北... {attacker_pos} の自軍部隊が消滅")
            del st.session_state.units[attacker_pos]
    else:
        # 防御施設との戦闘
        if unit_data["atk"] > target_def:
            st.session_state.owner[defender_pos] = atk_p
            st.session_state.defense[defender_pos] = unit_data["atk"] - target_def
            st.session_state.units[defender_pos] = unit_data
            del st.session_state.units[attacker_pos]
            st.session_state.battle_reports.append(f"占領！ {defender_pos} を奪取")
        else:
            st.session_state.defense[defender_pos] -= unit_data["atk"]
            st.session_state.battle_reports.append(f"攻撃失敗！ {defender_pos} の防御を削りました")
    
    # 首都陥落チェック
    if defender_pos == st.session_state.capitals[def_p]:
        if st.session_state.owner[defender_pos] == atk_p:
            st.session_state.winner = atk_p
            st.session_state.phase = "GAME_OVER"
# --- クリックイベント関数 ---
def on_cell_click(r, c, mode=None, unit_name=None):
    p = st.session_state.turn
    
    # 1. 拡大フェーズ
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r, c] == 0:
            st.session_state.owner[r, c] = p
            if st.session_state.capitals[p] is None:
                st.session_state.capitals[p] = (r, c)
            
            # 全マス埋まったら配置フェーズへ
            if np.all(st.session_state.owner != 0):
                st.session_state.phase = "2_PLACEMENT"
                st.session_state.money[1] = np.sum(st.session_state.owner == 1) * INCOME_PER_CELL
                st.session_state.money[2] = np.sum(st.session_state.owner == 2) * INCOME_PER_CELL
            st.session_state.turn = 3 - p
            
    # 2. 配置フェーズ
    elif st.session_state.phase == "2_PLACEMENT":
        if st.session_state.owner[r, c] == p:
            if mode == "部隊配置":
                u_data = UNITS[unit_name]
                if st.session_state.money[p] >= u_data["cost"]:
                    st.session_state.money[p] -= u_data["cost"]
                    st.session_state.units[(r, c)] = u_data.copy()
                    st.toast(f"{unit_name}を配置しました！")
                else:
                    st.error("資金が足りません")
            elif mode == "防御増強":
                if st.session_state.money[p] >= COST_DEFENSE_UP:
                    st.session_state.money[p] -= COST_DEFENSE_UP
                    st.session_state.defense[r, c] += DEFENSE_UP_AMOUNT
                    st.toast("防御力を強化しました")
                else:
                    st.error("資金が足りません")

    # 3. 侵攻フェーズ
    elif st.session_state.phase == "3_INVASION":
        if st.session_state.selected_unit_pos is None:
            if (r, c) in st.session_state.units and st.session_state.owner[r,c] == p:
                st.session_state.selected_unit_pos = (r, c)
        else:
            # 移動・攻撃実行
            start_pos = st.session_state.selected_unit_pos
            if (r, c) in get_neighbors(*start_pos):
                unit_data = st.session_state.units[start_pos]
                if st.session_state.owner[r, c] == p:
                    # 移動のみ
                    if (r, c) not in st.session_state.units:
                        st.session_state.units[r, c] = unit_data
                        del st.session_state.units[start_pos]
                else:
                    # 戦闘
                    process_battle(start_pos, (r, c), unit_data)
                st.session_state.selected_unit_pos = None

# --- UI構築 ---
st.title("🛡️ 陣地取りタクティクス")

p = st.session_state.turn
st.sidebar.subheader(f"プレイヤー {p} の番")
st.sidebar.metric("所持金", f"${st.session_state.money[p]}")

# 配置フェーズの操作パネル
mode = None
selected_u = None
if st.session_state.phase == "2_PLACEMENT":
    st.sidebar.markdown("---")
    mode = st.sidebar.radio("アクション", ["部隊配置", "防御増強"])
    if mode == "部隊配置":
        selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
        u = UNITS[selected_u]
        st.sidebar.caption(f"コスト:${u['cost']} / 攻撃力:{u['atk']}")
    
    if st.sidebar.button("配置を確定して次へ"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
        else:
            st.session_state.phase = "3_INVASION"
        st.rerun()

# --- マップ描画 ---
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r, c]
        unit = st.session_state.units.get((r, c))
        is_cap = (st.session_state.capitals[1] == (r, c) or st.session_state.capitals[2] == (r, c))
        
        # 背景色とアイコンの決定
        color_icon = "🔵" if owner == 1 else "🔴" if owner == 2 else "⬜"
        if is_cap: color_icon = "🏰"
        
        # ユニットがいればユニットアイコンを表示、いなければ防御数値を表示
        display_text = f"{unit['icon']}" if unit else f"{st.session_state.defense[r,c]}"
        
        btn_label = f"{color_icon}\n{display_text}"
        
        cols[c].button(btn_label, key=f"btn-{r}-{c}", 
                       on_click=on_cell_click, args=(r, c, mode, selected_u))

# リセットボタン
if st.sidebar.button("リセット"):
    st.session_state.clear()
    st.rerun()