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
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 200, 2: 200}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. ロジック関数 ---
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

# --- 4. スタイル計算ロジック ---
def get_cell_colors(r, c):
    owner = st.session_state.owner[r,c]
    def_val = st.session_state.defense[r,c]
    eco_val = st.session_state.economy[r,c]
    
    # 地形デフォルト
    if def_val > 160: icon, terrain_c = "⛰️", "#7D7D7D"
    elif eco_val > 35: icon, terrain_c = "🌾", "#F1C40F"
    else: icon, terrain_c = "🌲", "#27AE60"

    # 色の決定
    if owner == 1: bg, border = "#3498DB", "#005599" # 青
    elif owner == 2: bg, border = "#E74C3C", "#990000" # 赤
    else: bg, border = "#EEEEEE", "#CCCCCC" # 未占領（グレー）

    # 特殊状態
    if st.session_state.selected_pos == (r,c): bg = "#FFFF00"; border = "#FFD700"
    elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": bg = "#555555"

    return icon, bg, border

# --- 5. UI構築 ---
st.set_page_config(layout="wide")
st.title("🛡️ 領土奪取タクティクス")

# 強力なCSS強制適用
st.markdown("""
<style>
    /* 全ボタン共通 */
    .stButton > button {
        width: 100% !important;
        height: 120px !important;
        white-space: pre-wrap !important;
        font-weight: bold !important;
        font-size: 14px !important;
        transition: all 0.2s ease;
        border-radius: 8px !important;
    }
    /* テキストが見やすいように影をつける */
    .stButton > button div p {
        color: white !important;
        text-shadow: 1px 1px 3px black !important;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.winner:
    st.balloons(); st.success(f"🎊 PLAYER {st.session_state.winner} の勝利！"); st.stop()

# サイドバー
p = st.session_state.turn
st.sidebar.title(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("所持金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("拡大フェーズ: 土地をクリックして占領してください。")
elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
    if st.sidebar.button("配置を終了"):
        st.session_state.turn = 2 if st.session_state.turn == 1 else 1
        if st.session_state.turn == 1: 
            st.session_state.phase = "3_INVASION"; st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍を終了"):
        st.session_state.turn = 2 if st.session_state.turn == 1 else 1
        if st.session_state.turn == 1: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("資金回収して次のターンへ"):
        for i in [1, 2]: st.session_state.money[i] += np.sum(st.session_state.economy[st.session_state.owner == i])
        st.session_state.turn = 1; st.session_state.battle_reports = []; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# --- マップ描画とCSSインジェクション ---
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        unit = st.session_state.units.get((r,c))
        def_v, eco_v = st.session_state.defense[r,c], st.session_state.economy[r,c]
        icon, bg, border = get_cell_colors(r, c)
        
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        u_icon = unit["icon"] if unit else ""
        
        label = f"{icon}{cap}\n🛡️{def_v} 💰{eco_v}\n{u_icon}"
        
        # セルごとに個別のスタイルを生成（重要：!importantで強制上書き）
        st.markdown(f"""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child({c+1}) button {{
                background-color: {bg} !important;
                border: {border} !important;
            }}
            /* ホバー時も色を維持 */
            div[data-testid="stHorizontalBlock"] > div:nth-child({c+1}) button:hover {{
                background-color: {bg} !important;
                opacity: 0.8;
                border: {border} !important;
            }}
            </style>
        """, unsafe_allow_html=True)
        
        cols[c].button(label, key=f"cell_{r}_{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))

if st.session_state.battle_reports:
    with st.expander("📝 記録"):
        for msg in st.session_state.battle_reports: st.write(msg)