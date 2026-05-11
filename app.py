import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

# --- 2. ユニットデータ ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

MAP_SIZE = 6

# --- 3. ゲーム状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.terrain = np.random.choice([0, 1, 2], size=(MAP_SIZE, MAP_SIZE), p=[0.4, 0.35, 0.25])
    st.session_state.defense = np.zeros((MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.zeros((MAP_SIZE, MAP_SIZE))
    
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            t = st.session_state.terrain[r,c]
            if t == 2: # 山岳
                st.session_state.defense[r,c] = np.random.randint(150, 250)
                st.session_state.economy[r,c] = np.random.randint(5, 15)
            elif t == 1: # 森林
                st.session_state.defense[r,c] = np.random.randint(80, 130)
                st.session_state.economy[r,c] = np.random.randint(15, 30)
            else: # 平野
                st.session_state.defense[r,c] = np.random.randint(40, 70)
                st.session_state.economy[r,c] = np.random.randint(30, 60)

    st.session_state.unit_type = np.full((MAP_SIZE, MAP_SIZE), None)
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool)
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.gold = {1: 500, 2: 500}
    st.session_state.turn = 1
    st.session_state.phase = "拡大"
    st.session_state.winner = None
    st.session_state.history = ["ゲーム開始！"]
    st.session_state.selected = None

# --- 4. ロジック ---
def next_phase():
    if st.session_state.winner: return
    phases = ["拡大", "配置", "侵攻"]
    idx = phases.index(st.session_state.phase)
    if idx < 2:
        st.session_state.phase = phases[idx + 1]
    else:
        p = st.session_state.turn
        income = int(st.session_state.economy[st.session_state.owner == p].sum())
        st.session_state.gold[p] += income
        st.session_state.moved.fill(False)
        st.session_state.turn = 3 - p
        st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"

def handle_click(r, c):
    p = st.session_state.turn
    phase = st.session_state.phase
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        if st.session_state.capitals[p] is None:
            if owner == 0:
                st.session_state.capitals[p] = (r, c)
                st.session_state.owner[r, c] = p
                st.session_state.defense[r, c] += 200
        elif owner == 0 and st.session_state.gold[p] >= 30:
            st.session_state.owner[r, c] = p
            st.session_state.gold[p] -= 30

    elif phase == "配置":
        if owner == p:
            u_name = st.session_state.selected_unit_to_buy
            cost = UNITS[u_name]["cost"]
            if st.session_state.gold[p] >= cost:
                st.session_state.unit_type[r, c] = u_name
                st.session_state.gold[p] -= cost
                st.session_state.defense[r, c] += 30

    elif phase == "侵攻":
        if st.session_state.selected is None:
            if owner == p and st.session_state.unit_type[r, c] and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
        else:
            sr, sc = st.session_state.selected
            if abs(sr - r) <= 1 and abs(sc - c) <= 1 and not (sr == r and sc == c):
                attacker_unit = st.session_state.unit_type[sr, sc]
                if owner != p:
                    atk_pwr = UNITS[attacker_unit]["atk"] + np.random.randint(0, 100)
                    if atk_pwr > st.session_state.defense[r, c]:
                        if (r, c) == st.session_state.capitals[3-p]: st.session_state.winner = p
                        st.session_state.owner[r, c] = p
                        st.session_state.unit_type[r, c] = attacker_unit
                        st.session_state.unit_type[sr, sc] = None
                else:
                    if st.session_state.unit_type[r, c] is None:
                        st.session_state.unit_type[r, c] = attacker_unit
                        st.session_state.unit_type[sr, sc] = None
                st.session_state.moved[r, c] = True
            st.session_state.selected = None

# --- 5. CSS ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 110px; margin-bottom: 8px; border-radius: 10px; overflow: hidden; border: 2px solid #555; }
    .owner-1 { border-color: #3498db !important; }
    .owner-2 { border-color: #e74c3c !important; }
    .moved { filter: grayscale(1) brightness(0.5); }
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; pointer-events: none; }
    .unit-tag { background: white; color: black; padding: 2px 5px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; margin-top: 4px; }
    .unit-empty { color: #ccc; font-size: 0.7rem; margin-top: 4px; }
    .stButton > button { position: absolute; top: 0; left: 0; width: 100% !important; height: 110px !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 10; }
</style>
""", unsafe_allow_html=True)

# --- 6. メインUI ---
if st.session_state.winner:
    st.title(f"勝利者: Player {'A' if st.session_state.winner==1 else 'B'}")
    if st.button("リセット"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    st.subheader(f"Player {'A' if p==1 else 'B'} の手番 | {st.session_state.phase}フェーズ | 資金: {st.session_state.gold[p]}G")
    
    if st.session_state.phase == "配置":
        st.session_state.selected_unit_to_buy = st.selectbox("雇用:", list(UNITS.keys()))
    
    if st.button(f"【{st.session_state.phase}】終了"): next_phase(); st.rerun()

    images = {0: {"icon": "🌾", "img": get_base64_image("field.png")},
              1: {"icon": "🌲", "img": get_base64_image("forest.png")},
              2: {"icon": "⛰️", "img": get_base64_image("mount.png")}}

    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            t_idx = st.session_state.terrain[r, c]
            owner = st.session_state.owner[r, c]
            utype = st.session_state.unit_type[r, c]
            tile = images[t_idx]
            is_cap = (r, c) in st.session_state.capitals.values()
            
            # HTML文字列を慎重に構築
            unit_html = f"<div class='unit-tag'>{UNITS[utype]['icon']} {utype}</div>" if utype else "<div class='unit-empty'>空</div>"
            cap_html = "<div style='position:absolute;top:2px;left:5px;z-index:3;'>🏰</div>" if is_cap else ""
            w_class = f"owner-{owner}" if owner > 0 else ""
            if st.session_state.moved[r, c]: w_class += " moved"

            with cols[c]:
                # タイルの描画（文字列を分割せず一気に構築）
                html_code = f"""
                <div class="tile-wrapper {w_class}">
                    <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                    {cap_html}
                    <div class="tile-info">
                        <div>{tile['icon']}</div>
                        <div style="font-size:0.6rem;">🛡️{int(st.session_state.defense[r,c])} 💰{int(st.session_state.economy[r,c])}</div>
                        {unit_html}
                    </div>
                </div>"""
                st.markdown(html_code, unsafe_allow_html=True)
                st.button("", key=f"b{r}{c}", on_click=handle_click, args=(r, c))