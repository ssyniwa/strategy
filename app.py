import streamlit as st
import numpy as np

# --- 1. 設定 ---
MAP_SIZE = 6
# 地形ごとの画像URL（Unsplashなどのフリー素材。お好みのURLに差し替え可能です）
TERRAIN_IMAGES = {
    "MOUNTAIN": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=150&q=80",
    "FIELD": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=150&q=80",
    "FOREST": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=150&q=80"
}

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
    # 地形の固定（画像表示のため）
    st.session_state.terrain_type = np.zeros((MAP_SIZE, MAP_SIZE), dtype=object)
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
            if d > 160: st.session_state.terrain_type[r,c] = "MOUNTAIN"
            elif e > 35: st.session_state.terrain_type[r,c] = "FIELD"
            else: st.session_state.terrain_type[r,c] = "FOREST"
    
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 200, 2: 200}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. ロジック (変更なし) ---
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

# --- 4. CSS: 背景画像と透明ボタンの設定 ---
st.markdown("""
<style>
    /* ボタンを格納するコンテナの設定 */
    .cell-container {
        position: relative;
        width: 100%;
        height: 100px;
        margin-bottom: 10px;
        border-radius: 8px;
        overflow: hidden;
    }
    /* 背景画像レイヤー */
    .cell-bg {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover;
        background-position: center;
        z-index: 1;
        opacity: 0.7;
    }
    /* ボタン本体：背景を透明化し、テキストを前面に出す */
    .stButton > button {
        position: relative;
        z-index: 2;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        width: 100% !important;
        height: 100px !important;
    }
    /* 文字色の設定（前回の改善を継承） */
    button:has(p:contains("🔵")) p { color: #2196F3 !important; font-weight: 900 !important; text-shadow: 2px 2px 4px black !important; }
    button:has(p:contains("🔴")) p { color: #FF5252 !important; font-weight: 900 !important; text-shadow: 2px 2px 4px black !important; }
    button:has(p:contains("🟡")) p { color: #FFFF00 !important; text-shadow: 2px 2px 4px black !important; }
    button:has(p:contains("⬛")) p { color: #888888 !important; text-shadow: 1px 1px 2px black !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. メイン描画 ---
st.title(f"🌍 大戦略：{MAP_SIZE}x{MAP_SIZE} ビジュアル・タクティクス")

p = st.session_state.turn
st.sidebar.header(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("資金", f"${st.session_state.money[p]}")

# (サイドバーロジックは以前と同様)
mode, selected_u = None, None
if st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
    if st.sidebar.button("配置完了"):
        st.session_state.turn = 3 - st.session_state.turn
        if st.session_state.turn == 1: st.session_state.phase = "3_INVASION"; st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍完了"):
        st.session_state.turn = 3 - st.session_state.turn
        if st.session_state.turn == 1: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("次ターンへ"):
        for i in [1, 2]: st.session_state.money[i] += np.sum(st.session_state.economy[st.session_state.owner == i])
        st.session_state.turn = 1; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        terrain = st.session_state.terrain_type[r,c]
        img_url = TERRAIN_IMAGES[terrain]
        
        # 状態絵文字
        status = "⚪"
        if owner == 1: status = "🔵"
        elif owner == 2: status = "🔴"
        if st.session_state.selected_pos == (r,c): status = "🟡"
        elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": status = "⬛"

        unit = st.session_state.units.get((r,c))
        label = f"{status}\n🛡️{st.session_state.defense[r,c]}\n{unit['icon'] if unit else ''}"

        # 背景画像とボタンを重ねる
        with cols[c]:
            st.markdown(f'<div class="cell-container"><div class="cell-bg" style="background-image: url({img_url});"></div>', unsafe_allow_html=True)
            st.button(label, key=f"btn_{r}_{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.winner:
    st.balloons(); st.success(f"PLAYER {st.session_state.winner} の勝利！")