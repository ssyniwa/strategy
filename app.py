import streamlit as st
import numpy as np
import base64
import os

# --- 1. 画像読み込み関数 ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

# --- 2. ユニットデータ設定 ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 110, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 220, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 450, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 650, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 900, "icon": "💣"},
}
MAP_SIZE = 6

# --- 3. ゲーム状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    # 0:平野, 1:森林, 2:山岳
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
    st.session_state.selected = None
    st.session_state.history = ["ゲーム開始：首都を設置してください。"]

# --- 4. ロジック管理 ---
def handle_click(r, c):
    p, phase = st.session_state.turn, st.session_state.phase
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        if st.session_state.capitals[p] is None and owner == 0:
            st.session_state.capitals[p] = (r, c)
            st.session_state.owner[r, c] = p
            st.session_state.defense[r, c] += 200
            st.session_state.history.append(f"P{p}: ({r},{c})に首都を建設")
        elif owner == 0 and st.session_state.gold[p] >= 30:
            st.session_state.owner[r, c] = p
            st.session_state.gold[p] -= 30

    elif phase == "配置" and owner == p:
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
                atk_u = st.session_state.unit_type[sr, sc]
                if owner != p:
                    atk_pwr = UNITS[atk_u]["atk"] + np.random.randint(0, 100)
                    if atk_pwr > st.session_state.defense[r, c]:
                        if (r, c) == st.session_state.capitals[3-p]: st.session_state.winner = p
                        st.session_state.owner[r, c], st.session_state.unit_type[r, c] = p, atk_u
                        st.session_state.unit_type[sr, sc] = None
                        st.session_state.history.append(f"P{p}: ({r},{c})を攻略")
                elif st.session_state.unit_type[r, c] is None:
                    st.session_state.unit_type[r, c], st.session_state.unit_type[sr, sc] = atk_u, None
                st.session_state.moved[r, c] = True
            st.session_state.selected = None

# --- 5. ビジュアル設定 (CSS) ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 120px; border-radius: 12px; overflow: hidden; margin-bottom: 8px; border: 2px solid #555; }
    .owner-1 { border-color: #3498db !important; box-shadow: inset 0 0 15px rgba(52,152,219,0.5); }
    .owner-2 { border-color: #e74c3c !important; box-shadow: inset 0 0 15px rgba(231,76,60,0.5); }
    .moved { filter: grayscale(1) brightness(0.5); }
    .selected { border: 4px solid #f1c40f !important; z-index: 5; }
    
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; background-color: #2c3e50; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; pointer-events: none; }
    
    .unit-tag { background: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: 800; font-size: 0.7rem; margin-top: 4px; }
    .unit-empty { color: #aaa; font-size: 0.7rem; font-style: italic; margin-top: 4px; }
    
    .stButton > button { position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 120px !important; background: transparent !important; color: transparent !important; border: none !important; z-index: 10; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# --- 6. UIメイン ---
if st.session_state.winner:
    st.balloons()
    st.title(f"👑 Player {'A' if st.session_state.winner==1 else 'B'} 勝利！")
    if st.button("リスタート"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    st.title("🛡️ Kingdom Conquest")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Turn", f"Player {'A' if p==1 else 'B'}")
    c2.warning(f"Phase: {st.session_state.phase}")
    c3.metric("Gold", f"{st.session_state.gold[p]}G")

    if st.session_state.phase == "配置":
        st.session_state.selected_unit_to_buy = st.selectbox("雇用ユニット", list(UNITS.keys()))
    
    if st.button(f"【{st.session_state.phase}】フェーズを終了"):
        phases = ["拡大", "配置", "侵攻"]
        idx = phases.index(st.session_state.phase)
        if idx < 2:
            st.session_state.phase = phases[idx+1]
        else:
            income = int(st.session_state.economy[st.session_state.owner == p].sum())
            st.session_state.gold[p] += income
            st.session_state.moved.fill(False)
            st.session_state.turn = 3 - p
            st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.rerun()

    images = {
        0: {"icon": "🌾", "img": get_base64_image("field.png")},
        1: {"icon": "🌲", "img": get_base64_image("forest.png")},
        2: {"icon": "⛰️", "img": get_base64_image("mount.png")}
    }

    # マップレンダリング
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            t_idx = st.session_state.terrain[r, c]
            owner = st.session_state.owner[r, c]
            utype = st.session_state.unit_type[r, c]
            is_cap = (r, c) in st.session_state.capitals.values()
            
            w_class = f"owner-{owner}" if owner > 0 else ""
            if st.session_state.moved[r, c]: w_class += " moved"
            if (r, c) == st.session_state.selected: w_class += " selected"

            with cols[c]:
                # 表示レイヤー
                st.markdown(f"""
                    <div class="tile-wrapper {w_class}">
                        <div class="tile-bg" style="background-image: url('{images[t_idx]['img']}');"></div>
                        <div class="tile-info">
                            <div style="font-size:1.2rem;">{images[t_idx]['icon']} {'🏰' if is_cap else ''}</div>
                            <div style="font-size:0.65rem;">🛡️{int(st.session_state.defense[r,c])} 💰{int(st.session_state.economy[r,c])}</div>
                            {f"<div class='unit-tag'>{UNITS[utype]['icon']} {utype}</div>" if utype else "<div class='unit-empty'>空</div>"}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                # 操作レイヤー (透明ボタン)
                st.button("", key=f"cell_{r}_{c}", on_click=handle_click, args=(r, c))

    with st.sidebar:
        st.write("📜 ログ")
        for log in reversed(st.session_state.history[-10:]):
            st.caption(log)