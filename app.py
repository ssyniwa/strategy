import streamlit as st
import numpy as np

# --- 1. 設定 ---
MAP_SIZE = 5
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

# --- 2. 初期化 ---
if 'owner' not in st.session_state:
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

# --- 3. ロジック (handle_battle, on_cell_click は変更なし) ---
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
                if st.session_state.money[p] >= 50:
                    st.session_state.money[p] -= 50
                    st.session_state.defense[r,c] += 100
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

# --- 4. CSS: ラベルのテキストに基づいて色を変える魔法の指定 ---
st.markdown("""
<style>
    /* 基本スタイル */
    .stButton > button {
        width: 100% !important; height: 110px !important;
        border-radius: 8px !important; font-weight: bold !important;
        transition: none !important; /* アニメーションを切ることで即時反映 */
    }
    .stButton > button p { color: white !important; text-shadow: 1px 1px 2px black !important; font-size: 14px !important; }

    /* 所有者による色分け (ラベル内の [P1], [P2] などの文字列に反応させる) */
    div[data-testid="stVerticalBlock"]:has(button p:contains("[P1]")) button { background-color: #3498DB !important; border: 3px solid #005599 !important; }
    div[data-testid="stVerticalBlock"]:has(button p:contains("[P2]")) button { background-color: #E74C3C !important; border: 3px solid #990000 !important; }
    div[data-testid="stVerticalBlock"]:has(button p:contains("[--]")) button { background-color: #7D7D7D !important; border: 1px solid #444 !important; }
    
    /* 選択中・行動済み (優先順位を上げる) */
    div[data-testid="stVerticalBlock"]:has(button p:contains("[SEL]")) button { background-color: #F1C40F !important; border: 3px solid #FFD700 !important; }
    div[data-testid="stVerticalBlock"]:has(button p:contains("[MOV]")) button { background-color: #444444 !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. メイン描画 ---
st.title("🛡️ タクティカル・カラー・マップ")

# 勝利処理
if st.session_state.winner:
    st.balloons(); st.success(f"PLAYER {st.session_state.winner} WIN!"); st.stop()

# サイドバー (省略せず全て記述)
p = st.session_state.turn
st.sidebar.header(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("資金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("拡大フェーズ: 土地を占領せよ")
elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("派遣", list(UNITS.keys()))
    if st.sidebar.button("配置完了"):
        st.session_state.turn = 2 if st.session_state.turn == 1 else 1
        if st.session_state.turn == 1: st.session_state.phase = "3_INVASION"; st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍完了"):
        st.session_state.turn = 2 if st.session_state.turn == 1 else 1
        if st.session_state.turn == 1: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("次ターンへ"):
        for i in [1, 2]: st.session_state.money[i] += np.sum(st.session_state.economy[st.session_state.owner == i])
        st.session_state.turn = 1; st.session_state.battle_reports = []; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        def_v, eco_v = st.session_state.defense[r,c], st.session_state.economy[r,c]
        
        # 内部的な状態識別タグ（これがCSSに反応する）
        tag = "[--]"
        if owner == 1: tag = "[P1]"
        if owner == 2: tag = "[P2]"
        if st.session_state.selected_pos == (r,c): tag = "[SEL]"
        elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": tag = "[MOV]"

        # 地形アイコン
        t_icon = "⛰️" if def_v > 160 else "🌾" if eco_v > 35 else "🌲"
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        u_icon = unit["icon"] if unit else ""
        
        # ラベルの構築 (tagは見えないようにするか、デザインの一部にする)
        label = f"{t_icon}{cap}{tag}\n🛡️{def_v} 💰{eco_v}\n{u_icon}"
        
        cols[c].button(label, key=f"bt_{r}_{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))

if st.session_state.battle_reports:
    with st.expander("ログ"):
        for m in st.session_state.battle_reports: st.write(m)