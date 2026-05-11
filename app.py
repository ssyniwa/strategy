import streamlit as st
import numpy as np
import random
import base64
# --- 1. 定数・設定 ---
MAP_SIZE = 6
TOTAL_CELLS = MAP_SIZE * MAP_SIZE
COST_DEFENSE_UP = 50
DEFENSE_UP_AMOUNT = 100
def get_image_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return f"data:image/png;base64,{base64.b64encode(data).decode()}"
# 地形ごとの背景画像URL (ここを自分の画像パスに変更してください)
IMAGES = {
    0: get_image_base64("nmount.png"), # 山
    1: get_image_base64("nforest.png"),      # 森
    2: get_image_base64("nshop.png"),   # 町
    3: get_image_base64("nriver.png")          # 農村
}

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
    
    terrain_types = [0]*9 + [1]*9 + [2]*9 + [3]*9
    random.shuffle(terrain_types)
    st.session_state.terrain_map = np.array(terrain_types).reshape(MAP_SIZE, MAP_SIZE)
    
    def_map = np.zeros((MAP_SIZE, MAP_SIZE))
    eco_map = np.zeros((MAP_SIZE, MAP_SIZE))
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            t = st.session_state.terrain_map[r, c]
            if t == 0: # 山
                def_map[r,c] = np.random.randint(500, 801); eco_map[r,c] = np.random.randint(5, 15)
            elif t == 1: # 森
                def_map[r,c] = np.random.randint(201, 500); eco_map[r,c] = np.random.randint(15, 30)
            elif t == 2: # 平野
                def_map[r,c] = np.random.randint(100, 200); eco_map[r,c] = np.random.randint(40, 61)
            else: # 草原
                def_map[r,c] = np.random.randint(50, 150); eco_map[r,c] = np.random.randint(30, 45)
                
    st.session_state.defense = def_map
    st.session_state.economy = eco_map
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 100, 2: 100}
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None

# --- 3. ロジック関数 ---
def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

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
        st.session_state.defense[end_pos] = max(50, unit["atk"] // 2)
        del st.session_state.units[start_pos]
        st.session_state.moved_units.append(end_pos)
        if end_pos == st.session_state.capitals[def_p]:
            st.session_state.winner = atk_p

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
                u_key = unit_name.split(" (")[0] # コスト表示を除去してキーを取得
                u_data = UNITS[u_key]
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

# --- 4. CSS ---
st.set_page_config(layout="wide", page_title="World Tactics 6x6")
st.markdown("""
<style>
    .tile-container { position: relative; width: 100%; height: 100px; margin-bottom: 8px; border-radius: 8px; overflow: hidden; border: 1px solid #444; }
    .tile-bg { 
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
        background-size: cover; background-position: center;
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        z-index: 1; color: white; font-weight: bold; line-height: 1.1; text-align: center; font-size: 0.7rem; 
    }
    /* 文字を読みやすくするためのオーバーレイ */
    .text-overlay {
        background: rgba(0, 0, 0, 0.4); width: 100%; height: 100%;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    
    .owner-1 { border: 4px solid #3498DB !important; }
    .owner-2 { border: 4px solid #E74C3C !important; }
    
    @keyframes pulse-border {
        0% { box-shadow: inset 0 0 10px #FFF; }
        50% { box-shadow: inset 0 0 25px #FFF; }
        100% { box-shadow: inset 0 0 10px #FFF; }
    }
    .active-unit { animation: pulse-border 1.5s infinite; z-index: 2; }
    .is-selected { border: 4px solid #F1C40F !important; }
    .is-moved { filter: brightness(0.4) grayscale(0.8); }

    .tile-container div.stButton > button { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: transparent !important; border: none !important; color: transparent !important; z-index: 10; }
</style>
""", unsafe_allow_html=True)

# --- 5. サイドバーコントロール ---
mode, selected_u = None, None

if st.session_state.winner:
    st.sidebar.title("🏁 ゲーム終了")
    if st.sidebar.button("🎮 最初からやり直す"): reset_game()
else:
    p = st.session_state.turn
    st.sidebar.title(f"Player {'A 🔵' if p==1 else 'B 🔴'}")
    st.sidebar.metric("軍資金", f"${st.session_state.money[p]}")

    if st.session_state.phase == "1_EXPANSION":
        st.sidebar.info("陣地を交互に選択してください")
    elif st.session_state.phase == "2_PLACEMENT":
        mode = st.sidebar.radio("行動", ["部隊配置", "防御増強"])
        if mode == "部隊配置":
            # コストを表示した選択肢を作成
            unit_options = [f"{k} (${v['cost']})" for k, v in UNITS.items()]
            selected_u = st.sidebar.selectbox("ユニットを選択", unit_options)
        elif mode == "防御増強":
            st.sidebar.write(f"コスト: ${COST_DEFENSE_UP}")
            st.sidebar.write(f"上昇値: +{DEFENSE_UP_AMOUNT}")
            
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
        if st.sidebar.button("次ターンへ（資金回収）"):
            for i in [1, 2]: st.session_state.money[i] += int(np.sum(st.session_state.economy[st.session_state.owner == i]))
            st.session_state.turn = 1; st.session_state.phase = "2_PLACEMENT"
            st.rerun()

# --- 6. メイン描画 ---
st.title("🗺️ World Tactics 6x6")
if st.session_state.winner:
    st.balloons()
    st.header(f"👑 Player {'A' if st.session_state.winner == 1 else 'B'} の勝利！")

current_p = st.session_state.turn
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        def_val = st.session_state.defense[r,c]
        eco_val = st.session_state.economy[r,c]
        unit = st.session_state.units.get((r,c))
        t_type = st.session_state.terrain_map[r,c]

        t_icon = {0:"⛰️", 1:"🌲", 2:"🏙️", 3:"🌊"}[t_type]
        bg_url = IMAGES[t_type]

        classes = f"owner-{owner}" if owner > 0 else ""
        if st.session_state.phase == "3_INVASION" and owner == current_p and unit and (r, c) not in st.session_state.moved_units:
            classes += " active-unit"
        if st.session_state.selected_pos == (r,c): classes += " is-selected"
        if (r,c) in st.session_state.moved_units: classes += " is-moved"

        special = ""
        if (r,c) == st.session_state.capitals[1]: special = "🏰A"
        elif (r,c) == st.session_state.capitals[2]: special = "🏰B"

        with cols[c]:
            st.markdown(f"""
                <div class="tile-container {classes}">
                    <div class="tile-bg" style="background-image: url('{bg_url}');">
                        <div class="text-overlay">
                            <div>{t_icon} {special}</div>
                            <div style="font-size: 0.6rem;">🛡️{int(def_val)} 💰{int(eco_val)}</div>
                            <div style="font-size: 1.2rem;">{unit['icon'] if unit else ""}</div>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            st.button("", key=f"btn{r}{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))
            st.markdown("</div>", unsafe_allow_html=True)