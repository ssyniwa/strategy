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

# --- 2. ユニット・地形設定 ---
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
    st.session_state.history = ["ゲーム開始：首都を設置してください。"]
    st.session_state.selected = None

# --- 4. ロジック管理 ---
def next_phase():
    if st.session_state.winner: return
    phases = ["拡大", "配置", "侵攻"]
    idx = phases.index(st.session_state.phase)
    if idx < 2:
        st.session_state.phase = phases[idx + 1]
    else:
        # ターン終了時の収入計算
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
                st.session_state.history.append(f"P{p}: 首都を({r},{c})に設置")
        elif owner == 0 and st.session_state.gold[p] >= 30:
            st.session_state.owner[r, c] = p
            st.session_state.gold[p] -= 30

    elif phase == "配置":
        if owner == p:
            u_name = st.session_state.get("selected_unit_to_buy", "剣士団")
            cost = UNITS[u_name]["cost"]
            if st.session_state.gold[p] >= cost:
                st.session_state.unit_type[r, c] = u_name
                st.session_state.gold[p] -= cost
                st.session_state.defense[r, c] += 30
                st.toast(f"{u_name} を配備！")

    elif phase == "侵攻":
        if st.session_state.selected is None:
            if owner == p and st.session_state.unit_type[r, c] and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
                st.toast(f"選択中: {st.session_state.unit_type[r,c]} (移動先を選んでください)")
        else:
            sr, sc = st.session_state.selected
            if abs(sr - r) <= 1 and abs(sc - c) <= 1 and not (sr == r and sc == c):
                atk_unit = st.session_state.unit_type[sr, sc]
                if owner != p:
                    # 攻撃
                    atk_pwr = UNITS[atk_unit]["atk"] + np.random.randint(0, 100)
                    if atk_pwr > st.session_state.defense[r, c]:
                        if (r, c) == st.session_state.capitals[3-p]: st.session_state.winner = p
                        st.session_state.owner[r, c] = p
                        st.session_state.unit_type[r, c] = atk_unit
                        st.session_state.unit_type[sr, sc] = None
                        st.session_state.history.append(f"P{p}: ({r},{c}) を占領")
                    else: st.session_state.history.append(f"P{p}: ({r},{c}) への攻撃失敗")
                else:
                    # 移動
                    if st.session_state.unit_type[r, c] is None:
                        st.session_state.unit_type[r, c] = atk_unit
                        st.session_state.unit_type[sr, sc] = None
                st.session_state.moved[r, c] = True
            st.session_state.selected = None

# --- 5. デザイン (CSS) ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 115px; border-radius: 10px; overflow: hidden; border: 2px solid #444; margin-bottom: 5px; }
    .owner-1 { border-color: #3498db !important; }
    .owner-2 { border-color: #e74c3c !important; }
    .moved { filter: grayscale(1) brightness(0.6); }
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; pointer-events: none; }
    .unit-tag { background: white; color: black; padding: 1px 5px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; margin-top: 3px; }
    .unit-empty { color: #ccc; font-size: 0.7rem; margin-top: 3px; }
    /* 透明ボタンを全面に被せる */
    .stButton > button { position: absolute; top: 0; left: 0; width: 100% !important; height: 115px !important; background-color: transparent !important; color: transparent !important; border: none !important; z-index: 10; cursor: pointer; }
    .stButton > button:hover { background-color: rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

# --- 6. UI表示 ---
if st.session_state.winner:
    st.title(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} の勝利！")
    if st.button("もう一度遊ぶ"):
        st.session_state.clear()
        st.rerun()
else:
    p = st.session_state.turn
    st.title("🛡️ Kingdom Strategy")
    
    # ステータスバー
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("手番", f"Player {'A' if p==1 else 'B'}")
    col_b.metric("フェーズ", st.session_state.phase)
    col_c.metric("資金", f"{st.session_state.gold[p]}G")

    # フェーズ別UI
    if st.session_state.phase == "配置":
        st.session_state.selected_unit_to_buy = st.selectbox("雇用するユニットを選択:", list(UNITS.keys()))
    
    if st.button(f"➔ 【{st.session_state.phase}フェーズ】を終了"):
        next_phase()
        st.rerun()

    # 地形画像アセット
    images = {
        0: {"icon": "🌾", "img": get_base64_image("field.png")},
        1: {"icon": "🌲", "img": get_base64_image("forest.png")},
        2: {"icon": "⛰️", "img": get_base64_image("mount.png")}
    }

    # マップ描画
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            t_idx = st.session_state.terrain[r, c]
            owner = st.session_state.owner[r, c]
            utype = st.session_state.unit_type[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            tile = images[t_idx]
            
            # クラス判定
            w_class = f"owner-{owner}" if owner > 0 else ""
            if st.session_state.moved[r, c]: w_class += " moved"
            
            # 情報HTML
            unit_disp = f"<div class='unit-tag'>{UNITS[utype]['icon']} {utype}</div>" if utype else "<div class='unit-empty'>空</div>"
            cap_disp = "<div style='position:absolute;top:2px;left:5px;z-index:3;font-size:1.5rem;'>🏰</div>" if is_cap else ""
            
            with cols[c]:
                # 1. 見た目を描画
                st.markdown(f"""
                <div class="tile-wrapper {w_class}">
                    <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                    {cap_disp}
                    <div class="tile-info">
                        <div style="font-size:1.2rem;">{tile['icon']}</div>
                        <div style="font-size:0.65rem;">🛡️ {int(st.session_state.defense[r,c])} 💰 {int(st.session_state.economy[r,c])}</div>
                        {unit_disp}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. クリック判定用の透明ボタン（見た目の上に被せる）
                st.button("", key=f"btn_{r}_{c}", on_click=handle_click, args=(r, c))

    with st.sidebar:
        st.write("📜 ログ")
        for log in reversed(st.session_state.history[-8:]):
            st.caption(log)