import streamlit as st
import numpy as np

# --- 1. ゲーム設定 & ユニットデータ ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 110, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 220, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 450, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 650, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 900, "icon": "💣"},
}
MAP_SIZE = 5

# --- 2. CSS: ハイブリッド配置の心臓部 ---
st.markdown("""
<style>
    .tile-container {
        position: relative;
        width: 100%;
        height: 130px;
        margin-bottom: 15px;
    }
    /* 背景デザイン層 */
    .tile-design {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        border-radius: 12px;
        border: 2px solid #444;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 1;
        pointer-events: none; /* クリックを背後のボタンへ通す */
        transition: 0.3s;
    }
    /* 所有者別スタイル */
    .owner-1 { background: linear-gradient(135deg, #1e3a8a, #3b82f6); border-color: #60a5fa !important; box-shadow: 0 0 10px rgba(59,130,246,0.5); }
    .owner-2 { background: linear-gradient(135deg, #7f1d1d, #ef4444); border-color: #f87171 !important; box-shadow: 0 0 10px rgba(239,68,68,0.5); }
    .owner-0 { background: #1f2937; }
    
    .moved { filter: grayscale(0.8) brightness(0.5); }
    
    .stat-text { font-size: 0.7rem; color: #e5e7eb; margin: 2px 0; }
    .unit-tag { background: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; margin-top: 5px; }
    .unit-empty { font-size: 0.7rem; color: #9ca3af; font-style: italic; margin-top: 5px; }

    /* Streamlitボタンを透明にして最前面に被せる */
    .stButton > button {
        position: absolute !important;
        top: 0 !important; left: 0 !important;
        width: 100% !important; height: 130px !important;
        z-index: 10 !important;
        background-color: transparent !important;
        color: transparent !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ゲーム状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    # 地形: 平野(🌾), 森林(🌲), 山岳(⛰️)
    st.session_state.terrain = np.random.choice(["🌾", "🌲", "⛰️"], size=(MAP_SIZE, MAP_SIZE), p=[0.4, 0.35, 0.25])
    st.session_state.defense = np.zeros((MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.zeros((MAP_SIZE, MAP_SIZE))
    
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            t = st.session_state.terrain[r,c]
            if t == "⛰️":
                st.session_state.defense[r,c], st.session_state.economy[r,c] = np.random.randint(180, 260), np.random.randint(5, 15)
            elif t == "🌲":
                st.session_state.defense[r,c], st.session_state.economy[r,c] = np.random.randint(90, 140), np.random.randint(20, 35)
            else:
                st.session_state.defense[r,c], st.session_state.economy[r,c] = np.random.randint(40, 70), np.random.randint(40, 65)

    st.session_state.unit_type = np.full((MAP_SIZE, MAP_SIZE), None)
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool)
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.gold = {1: 600, 2: 600}
    st.session_state.turn = 1
    st.session_state.phase = "拡大"
    st.session_state.winner = None
    st.session_state.selected = None

# --- 4. ロジック関数 ---
def handle_click(r, c):
    p = st.session_state.turn
    phase = st.session_state.phase
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        if st.session_state.capitals[p] is None and owner == 0:
            st.session_state.capitals[p] = (r, c)
            st.session_state.owner[r, c] = p
            st.session_state.defense[r, c] += 200
        elif owner == 0 and st.session_state.gold[p] >= 40:
            st.session_state.owner[r, c] = p
            st.session_state.gold[p] -= 40

    elif phase == "配置":
        if owner == p:
            u_name = st.session_state.get("buying_unit", "剣士団")
            cost = UNITS[u_name]["cost"]
            if st.session_state.gold[p] >= cost:
                st.session_state.unit_type[r, c] = u_name
                st.session_state.gold[p] -= cost
                st.session_state.defense[r, c] += 20

    elif phase == "侵攻":
        if st.session_state.selected is None:
            if owner == p and st.session_state.unit_type[r, c] and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
        else:
            sr, sc = st.session_state.selected
            if abs(sr - r) <= 1 and abs(sc - c) <= 1 and not (sr == r and sc == c):
                atk_u = st.session_state.unit_type[sr, sc]
                if owner != p:
                    if (UNITS[atk_u]["atk"] + np.random.randint(0, 80)) > st.session_state.defense[r, c]:
                        if (r, c) == st.session_state.capitals[3-p]: st.session_state.winner = p
                        st.session_state.owner[r, c] = p
                        st.session_state.unit_type[r, c] = atk_u
                        st.session_state.unit_type[sr, sc] = None
                elif st.session_state.unit_type[r, c] is None:
                    st.session_state.unit_type[r, c] = atk_u
                    st.session_state.unit_type[sr, sc] = None
                st.session_state.moved[r, c] = True
            st.session_state.selected = None

# --- 5. メインUI ---
st.title("🛡️ Kingdom Strategy")

if st.session_state.winner:
    st.balloons()
    st.success(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} が大陸を統一しました！")
    if st.button("新世界を創造する"): 
        st.session_state.clear()
        st.rerun()
else:
    p = st.session_state.turn
    col_info = st.columns([2, 2, 3])
    col_info[0].metric("Player", "A (Blue)" if p==1 else "B (Red)")
    col_info[1].metric("Gold", f"{st.session_state.gold[p]}G")
    
    if st.session_state.phase == "配置":
        st.session_state.buying_unit = st.selectbox("雇用ユニット", list(UNITS.keys()))

    if st.button(f"➔ {st.session_state.phase}フェーズを終了"):
        if st.session_state.phase == "拡大": st.session_state.phase = "配置"
        elif st.session_state.phase == "配置": st.session_state.phase = "侵攻"
        else:
            income = int(st.session_state.economy[st.session_state.owner == p].sum())
            st.session_state.gold[p] += income
            st.session_state.moved.fill(False)
            st.session_state.turn = 3 - p
            st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.rerun()

    # --- マップ描画（ハイブリッド方式） ---
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r, c]
            terrain = st.session_state.terrain[r, c]
            unit = st.session_state.unit_type[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            is_moved = st.session_state.moved[r, c]
            is_sel = (r, c) == st.session_state.selected
            
            with cols[c]:
                # 1. コンテナ開始
                st.markdown('<div class="tile-container">', unsafe_allow_html=True)
                
                # 2. 背面のHTMLデザイン
                sel_style = "border: 4px solid yellow;" if is_sel else ""
                st.markdown(f"""
                    <div class="tile-design owner-{owner} {'moved' if is_moved else ''}" style="{sel_style}">
                        <div style="font-size:1.4rem;">{terrain} {'🏰' if is_cap else ''}</div>
                        <div class="stat-text">🛡️ {int(st.session_state.defense[r,c])}</div>
                        <div class="stat-text">💰 {int(st.session_state.economy[r,c])}</div>
                        <div class="{'unit-tag' if unit else 'unit-empty'}">
                            {UNITS[unit]['icon'] + " " + unit if unit else "空"}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 3. 前面の透明ボタン
                st.button("", key=f"b_{r}_{c}", on_click=handle_click, args=(r, c))
                
                # 4. コンテナ終了
                st.markdown('</div>', unsafe_allow_html=True)