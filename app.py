import streamlit as st
import numpy as np
import time

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
    st.session_state.units = {} # {(r, c): {"name": "剣士団", "atk": 100}}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 0, 2: 0}
    st.session_state.battle_reports = []
    st.session_state.selected_unit_pos = None # 移動元選択用

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

# --- メインロジック ---
st.title("🛡️ 陣地取りタクティクス：首都攻防戦")

# ステータス表示
p = st.session_state.turn
st.sidebar.subheader(f"現在：プレイヤー {p} ({'🔵' if p==1 else '🔴'})")
st.sidebar.write(f"フェーズ: {st.session_state.phase}")
st.sidebar.write(f"所持金: ${st.session_state.money[p]}")

if st.session_state.phase == "1_EXPANSION":
    st.info("空き地を1つ選び、自陣の「首都」にしてください" if not st.session_state.capitals[p] else "空き地を選んで陣地を広げてください")

elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("行動選択", ["部隊配置", "防御増強"])
    if mode == "部隊配置":
        u_type = st.sidebar.selectbox("ユニット選択", list(UNITS.keys()))
        st.sidebar.write(f"コスト: {UNITS[u_type]['cost']}")
    if st.sidebar.button("配置フェーズ終了"):
        st.session_state.phase = "3_INVASION"
        st.rerun()

elif st.session_state.phase == "3_INVASION":
    st.warning("移動させる部隊を選択してください")
    if st.sidebar.button("侵攻フェーズ終了"):
        st.session_state.phase = "5_RESULT"
        st.rerun()

# マップクリック処理
def on_cell_click(r, c):
    p = st.session_state.turn
    # 1. 拡大フェーズ
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None:
                st.session_state.capitals[p] = (r, c)
            
            if np.all(st.session_state.owner != 0):
                st.session_state.phase = "2_PLACEMENT"
            st.session_state.turn = 3 - p # 交代
            
    # 2. 配置フェーズ
    elif st.session_state.phase == "2_PLACEMENT":
        if st.session_state.owner[r,c] == p:
            # 外部で選択されたmodeを拾う（実装上はラジオボタン等）
            pass # UI側でボタンargsを使用して処理

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

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r, c]
        unit = st.session_state.units.get((r, c))
        is_cap = (st.session_state.capitals[1] == (r, c) or st.session_state.capitals[2] == (r, c))
        
        # アイコン決定
        bg = "🔵" if owner == 1 else "🔴" if owner == 2 else "⬜"
        content = f"{unit['icon']}" if unit else f"{st.session_state.defense[r,c]}"
        if is_cap: bg = "🏰"
        
        btn_label = f"{bg}\n{content}"
        
        # 選択中の強調
        if st.session_state.selected_unit_pos == (r, c):
            btn_label = "📍\n選択中"

        # ボタン実行 (配置フェーズの処理を簡略化するためargsを工夫)
        cols[c].button(btn_label, key=f"{r}-{c}", on_click=on_cell_click, args=(r, c))

# 配置・結果フェーズの補助UI
if st.session_state.phase == "5_RESULT":
    st.subheader("戦闘レポート")
    for report in st.session_state.battle_reports:
        st.write(f"- {report}")
    if st.button("次のターンへ (配置フェーズへ戻る)"):
        st.session_state.battle_reports = []
        st.session_state.turn = 1
        st.session_state.phase = "2_PLACEMENT"
        # 資金加算
        st.session_state.money[1] += np.sum(st.session_state.owner == 1) * INCOME_PER_CELL
        st.session_state.money[2] += np.sum(st.session_state.owner == 2) * INCOME_PER_CELL
        st.rerun()

if st.session_state.phase == "GAME_OVER":
    st.balloons()
    st.header(f"プレイヤー {st.session_state.winner} の勝利！！")