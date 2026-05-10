import streamlit as st
import numpy as np
import time

# --- ページ設定 ---
st.set_page_config(page_title="戦略陣地タクティクス", layout="wide")

# --- 定数設定 ---
MAP_SIZE = 5
INCOME_PER_TERRITORY = 10  # 1マスにつき10

UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

# --- セッション状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    # 防御力をランダムに設定 (50〜200)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.money = {1: 0, 2: 0}
    st.session_state.turn = 1
    st.session_state.phase = "EXPANSION"
    st.session_state.animating = None  # アニメーション管理用

# --- ゲームロジック ---
def next_turn():
    if np.all(st.session_state.owner != 0) and st.session_state.phase == "EXPANSION":
        st.session_state.phase = "BATTLE"
    
    st.session_state.turn = 2 if st.session_state.turn == 1 else 1
    
    if st.session_state.phase == "BATTLE":
        territory_count = np.sum(st.session_state.owner == st.session_state.turn)
        st.session_state.money[st.session_state.turn] += territory_count * INCOME_PER_TERRITORY

def handle_click(r, c, selected_unit_name, action_mode):
    p = st.session_state.turn
    
    # 拡大フェーズ
    if st.session_state.phase == "EXPANSION":
        if st.session_state.owner[r, c] == 0:
            st.session_state.owner[r, c] = p
            next_turn()
        return

    # 戦闘フェーズ
    if action_mode == "攻撃 (部隊派遣)":
        unit = UNITS[selected_unit_name]
        if st.session_state.money[p] >= unit["cost"]:
            st.session_state.money[p] -= unit["cost"]
            
            # アニメーション開始合図
            st.session_state.animating = {"target": (r, c), "icon": unit["icon"]}
            
            # 判定ロジック
            if st.session_state.owner[r, c] != p:
                if unit["atk"] > st.session_state.defense[r, c]:
                    st.session_state.owner[r, c] = p
                    st.session_state.defense[r, c] = unit["atk"] - st.session_state.defense[r, c]
                else:
                    st.session_state.defense[r, c] -= unit["atk"]
            else:
                st.warning("自陣には攻撃できません。防御向上を選んでください。")
                return
            next_turn()
        else:
            st.error("資金不足です")

    elif action_mode == "防御向上 (+100)":
        if st.session_state.money[p] >= 50: # 防御向上コストは一律50と仮定
            if st.session_state.owner[r, c] == p:
                st.session_state.money[p] -= 50
                st.session_state.defense[r, c] += 100
                next_turn()
            else:
                st.error("敵陣の防御は上げられません")
        else:
            st.error("資金不足です（防御向上には50必要）")

# --- UI構築 ---
st.title("⚔️ 高度戦略陣地取り：タクティカル・ムーブ")

# サイドバーステータス
st.sidebar.header(f"Turn: Player {'A' if st.session_state.turn ==1 else 'B'}")
st.sidebar.metric("所持金", f"${st.session_state.money[st.session_state.turn]}")

if st.session_state.phase == "BATTLE":
    action_mode = st.sidebar.radio("アクション選択", ["攻撃 (部隊派遣)", "防御向上 (+100)"])
    selected_unit = st.sidebar.selectbox("派遣部隊", list(UNITS.keys()))
    u = UNITS[selected_unit]
    st.sidebar.caption(f"コスト: {u['cost']} / 攻撃力: {u['atk']}")
else:
    st.sidebar.info("空き地をタップして占領してください")
    action_mode = None
    selected_unit = None

# マップ表示エリア
grid_placeholder = st.empty()

def render_map():
    with grid_placeholder.container():
        for r in range(MAP_SIZE):
            cols = st.columns(MAP_SIZE)
            for c in range(MAP_SIZE):
                owner = st.session_state.owner[r, c]
                defense = st.session_state.defense[r, c]
                color = "🔵" if owner == 1 else "🔴" if owner == 2 else "⬜"
                
                # アニメーション中の表示
                display_label = f"{color}\n{defense}"
                if st.session_state.animating and st.session_state.animating["target"] == (r, c):
                    display_label = f"{st.session_state.animating['icon']}\n⚡️"
                
                cols[c].button(display_label, key=f"cell-{r}-{c}-{time.time()}", 
                               on_click=handle_click, args=(r, c, selected_unit, action_mode))

# 初回描画
render_map()

# アニメーション処理（演出）
if st.session_state.animating:
    time.sleep(0.5) # 移動演出の時間
    st.session_state.animating = None
    st.rerun()

if st.button("リセット"):
    st.session_state.clear()
    st.rerun()