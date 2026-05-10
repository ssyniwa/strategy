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
    # 地形の多様性：防御力 (50-200) と 資金力 (10-50)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {} # {(r, c): unit_dict}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 200, 2: 200} # 初期資金
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None # 侵攻時の移動元
    st.session_state.moved_units = [] # 1ターン1行動制限用
    st.session_state.winner = None

# --- 3. 戦闘解決ロジック ---
def handle_battle(start_pos, end_pos):
    atk_p = st.session_state.turn
    def_p = 3 - atk_p
    unit = st.session_state.units[start_pos]
    target_unit = st.session_state.units.get(end_pos)
    target_def = st.session_state.defense[end_pos]

    victory = False
    if target_unit:
        # 部隊 vs 部隊
        if unit["atk"] > target_unit["atk"]:
            st.session_state.battle_reports.append(f"🔵P{atk_p}が{end_pos}の敵部隊を撃破！")
            victory = True
        else:
            st.session_state.battle_reports.append(f"🔴P{atk_p}の部隊が{end_pos}で返り討ちに遭いました")
            del st.session_state.units[start_pos]
    else:
        # 部隊 vs 防御力
        if unit["atk"] > target_def:
            st.session_state.battle_reports.append(f"⛳P{atk_p}が{end_pos}を占領！")
            victory = True
        else:
            st.session_state.battle_reports.append(f"🛡️P{atk_p}の攻撃！{end_pos}の防御を削りました")
            st.session_state.defense[end_pos] -= unit["atk"]
            st.session_state.moved_units.append(start_pos)

    if victory:
        st.session_state.owner[end_pos] = atk_p
        st.session_state.units[end_pos] = unit
        st.session_state.defense[end_pos] = max(20, unit["atk"] // 2)
        del st.session_state.units[start_pos]
        st.session_state.moved_units.append(end_pos)
        # 首都陥落判定
        if end_pos == st.session_state.capitals[def_p]:
            st.session_state.winner = atk_p
            st.session_state.phase = "GAME_OVER"

# --- 4. クリックイベントハンドラ ---
def on_cell_click(r, c, mode=None, unit_name=None):
    if st.session_state.winner: return
    p = st.session_state.turn
    
    # 【拡大フェーズ】初期陣地と首都決定
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None:
                st.session_state.capitals[p] = (r, c)
            if np.all(st.session_state.owner != 0):
                st.session_state.phase = "2_PLACEMENT"
            st.session_state.turn = 3 - p

    # 【配置フェーズ】
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

    # 【侵攻フェーズ】移動と戦闘
    elif st.session_state.phase == "3_INVASION":
        if (r, c) in st.session_state.moved_units: return
        if st.session_state.selected_pos is None:
            if (r,c) in st.session_state.units and st.session_state.owner[r,c] == p:
                st.session_state.selected_pos = (r,c)
        else:
            start_pos = st.session_state.selected_pos
            if abs(r - start_pos[0]) + abs(c - start_pos[1]) == 1: # 隣接判定
                if st.session_state.owner[r,c] == p:
                    if (r,c) not in st.session_state.units: # 空き自陣へ移動
                        st.session_state.units[(r,c)] = st.session_state.units[start_pos]
                        del st.session_state.units[start_pos]
                        st.session_state.moved_units.append((r, c))
                else:
                    handle_battle(start_pos, (r,c))
            st.session_state.selected_pos = None

# --- 5. 地形描画スタイル定義 ---
def get_terrain_style(r, c):
    def_val = st.session_state.defense[r,c]
    eco_val = st.session_state.economy[r,c]
    owner = st.session_state.owner[r,c]
    
    # 地形種別
    if def_val > 160:
        terrain_icon, color = "⛰️", "#7D7D7D" # 山岳
    elif eco_val > 35:
        terrain_icon, color = "🌾", "#F1C40F" # 平野
    else:
        terrain_icon, color = "🌲", "#27AE60" # 森林

    bg_color = color
    border = "1px solid #eee"
    if owner == 1: border = "5px solid #3498DB" # P1(青)
    if owner == 2: border = "5px solid #E74C3C" # P2(赤)
    
    if st.session_state.selected_pos == (r,c): bg_color = "#FFF176"
    elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": bg_color = "#424242"

    return terrain_icon, bg_color, border

# --- 6. 画面UI構成 ---
st.set_page_config(page_title="World Tactics Map", layout="wide")
st.title("🗺️ ワールド・タクティクス・シミュレーター")

# CSS: ボタンのスタイル調整
st.markdown("""
<style>
    .stButton > button {
        width: 100% !important; height: 110px !important;
        color: white !important; text-shadow: 1px 1px 2px black;
        font-weight: bold !important; white-space: pre-wrap !important;
        font-size: 13px !important; line-height: 1.1 !important;
    }
</style>
""", unsafe_allow_html=True)

# 勝利判定
if st.session_state.phase == "GAME_OVER":
    st.balloons()
    st.success(f"🎊 プレイヤー {st.session_state.winner} の勝利！首都を陥落させました！")
    if st.button("新しくゲームを始める"):
        st.session_state.clear(); st.rerun()
    st.stop()

# サイドバー：ステータスとフェーズ操作
p = st.session_state.turn
st.sidebar.title(f"Turn: Player {'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("軍資金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("拡大フェーズ：陣地を広げてください。最初の地点が首都になります。")

elif st.session_state.phase == "2_PLACEMENT":
    st.sidebar.markdown("---")
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置":
        selected_u = st.sidebar.selectbox("派遣部隊", list(UNITS.keys()))
        st.sidebar.caption(f"ATK: {UNITS[selected_u]['atk']} / Cost: {UNITS[selected_u]['cost']}")
    
    if st.sidebar.button("配置フェーズを終了する"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
        else:
            st.session_state.phase = "3_INVASION"
            st.session_state.turn = 1
            st.session_state.moved_units = []
        st.rerun()

elif st.session_state.phase == "3_INVASION":
    st.sidebar.warning("侵攻フェーズ：部隊を選び隣接マスへ移動・攻撃してください。")
    if st.sidebar.button("侵攻フェーズを終了する"):
        if st.session_state.turn == 1:
            st.session_state.turn = 2
            st.session_state.moved_units = []
        else:
            st.session_state.phase = "5_RESULT"
        st.rerun()

elif st.session_state.phase == "5_RESULT":
    st.sidebar.success("ターン終了。各領土から資金を回収します。")
    if st.sidebar.button("資金を回収して次のターンへ"):
        for i in [1, 2]:
            income = np.sum(st.session_state.economy[st.session_state.owner == i])
            st.session_state.money[i] += income
        st.session_state.turn = 1
        st.session_state.battle_reports = []
        st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        unit = st.session_state.units.get((r,c))
        def_val = st.session_state.defense[r,c]
        eco_val = st.session_state.economy[r,c]
        
        icon, bg_color, border = get_terrain_style(r, c)
        
        special = ""
        if (r,c) == st.session_state.capitals[1]: special = "🏰A"
        elif (r,c) == st.session_state.capitals[2]: special = "🏰B"
        
        u_disp = unit["icon"] if unit else "---"
        
        label = f"{icon}{special}\n🛡️{def_val} 💰{eco_val}\n{u_disp}"
        
        # 個別ボタンのCSS注入
        st.markdown(f"""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child({c+1}) button[key="key{r}{c}"] {{
                background-color: {bg_color} !important;
                border: {border} !important;
            }}
            </style>
        """, unsafe_allow_html=True)
        
        cols[c].button(label, key=f"key{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))

# 戦闘レポート
if st.session_state.battle_reports:
    st.divider()
    with st.expander("📝 直近の戦闘ログ", expanded=True):
        for report in st.session_state.battle_reports:
            st.write(report)