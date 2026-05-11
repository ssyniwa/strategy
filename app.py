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

# --- 2. データ定義 ---
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
    # 地形タイプを固定 (0:平野, 1:森林, 2:山岳)
    st.session_state.terrain = np.random.choice([0, 1, 2], size=(MAP_SIZE, MAP_SIZE), p=[0.4, 0.4, 0.2])
    
    # 地形に応じた初期ステータス
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
    st.session_state.history = ["ゲーム開始：拡大フェーズで首都を設置してください。"]
    st.session_state.selected = None

# --- 4. ロジック関数 ---
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
        st.session_state.history.append(f"ターン交代: P{st.session_state.turn} (収入 {income}G)")

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
                st.session_state.history.append(f"P{p}: ({r},{c}) に首都を建設！")
            else: st.toast("占領済みです")
        else:
            if owner == 0 and st.session_state.gold[p] >= 30:
                st.session_state.owner[r, c] = p
                st.session_state.gold[p] -= 30
            elif owner == 0: st.toast("資金不足(30G)")

    elif phase == "配置":
        if owner == p:
            u_name = st.session_state.selected_unit_to_buy
            cost = UNITS[u_name]["cost"]
            if st.session_state.gold[p] >= cost:
                st.session_state.unit_type[r, c] = u_name
                st.session_state.gold[p] -= cost
                st.session_state.defense[r, c] += 30 # 配置による防御UP
                st.toast(f"{u_name} を配置しました")
            else: st.toast("資金不足です")

    elif phase == "侵攻":
        if st.session_state.selected is None:
            if owner == p and st.session_state.unit_type[r, c] is not None and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
            else: st.toast("行動可能な部隊を選択してください")
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
                        st.session_state.history.append(f"奪取成功! ({r},{c})")
                    else: st.session_state.history.append(f"攻撃失敗 ({r},{c})")
                else:
                    if st.session_state.unit_type[r, c] is None:
                        st.session_state.unit_type[r, c] = attacker_unit
                        st.session_state.unit_type[sr, sc] = None
                st.session_state.moved[r, c] = True
                st.session_state.selected = None
            else:
                st.session_state.selected = None
                st.toast("隣接マスのみ有効です")

# --- 5. CSS ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 110px; margin-bottom: 8px; border-radius: 10px; overflow: hidden; border: 2px solid #555; }
    .owner-1 { border-color: #3498db !important; box-shadow: 0 0 10px #3498db; }
    .owner-2 { border-color: #e74c3c !important; box-shadow: 0 0 10px #e74c3c; }
    .moved { filter: grayscale(1) brightness(0.5); }
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; pointer-events: none; }
    .unit-tag { background: white; color: black; padding: 1px 4px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; margin-top: 2px; }
    .tile-wrapper div.stButton > button { position: absolute; top: 0; left: 0; width: 100% !important; height: 110px !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 10; }
</style>
""", unsafe_allow_html=True)

# --- 6. メインUI ---
if st.session_state.winner:
    st.title(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} の勝利！")
    if st.button("リスタート"):
        st.session_state.clear()
        st.rerun()
else:
    st.title("🛡️ Kingdom Conquest: 3 Terrains")
    p = st.session_state.turn
    c1, c2, c3 = st.columns(3)
    c1.metric("Turn", f"Player {'A' if p==1 else 'B'}")
    c2.warning(f"Phase: {st.session_state.phase}")
    c3.metric("Gold", f"{st.session_state.gold[p]}G")

    if st.session_state.phase == "配置":
        st.session_state.selected_unit_to_buy = st.selectbox("配置するユニット", list(UNITS.keys()))
    
    if st.button(f"【{st.session_state.phase}】フェーズを終了"):
        next_phase()
        st.rerun()

    images = {
        0: {"icon": "🌾", "img": get_base64_image("field.png")},
        1: {"icon": "🌲", "img": get_base64_image("forest.png")},
        2: {"icon": "⛰️", "img": get_base64_image("mount.png")}
    }

    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            t_idx = st.session_state.terrain[r, c]
            owner = st.session_state.owner[r, c]
            utype = st.session_state.unit_type[r, c]
            tile = images[t_idx]
            
            w_class = f"owner-{owner}" if owner > 0 else ""
            if st.session_state.moved[r, c]: w_class += " moved"

            with cols[c]:
                st.markdown(f"""
                    <div class="tile-wrapper {w_class}">
                        <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                        <div class="tile-info">
                            <div style="font-size:1.1rem;">{tile['icon']}</div>
                            <div style="font-size:0.65rem;">🛡️{int(st.session_state.defense[r,c])} 💰{int(st.session_state.economy[r,c])}</div>
                            {f"<div class='unit-tag'>{UNITS[utype]['icon']} {utype}</div>" if utype else ""}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.button("", key=f"btn_{r}_{c}", on_click=handle_click, args=(r, c))