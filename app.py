import streamlit as st
import numpy as np

# --- 1. ユニット設定 ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 110, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 220, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 450, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 650, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 900, "icon": "💣"},
}
MAP_SIZE = 5

# --- 2. CSS: 表示層と操作層の完全分離 ---
st.markdown("""
<style>
    /* タイル全体の枠 */
    .tile-container {
        position: relative;
        width: 100%;
        height: 140px;
        margin-bottom: 20px;
    }

    /* 【表示層】HTML/CSSでのステータス描画 */
    .tile-display {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        border-radius: 15px;
        z-index: 1; /* ボタンの下 */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2px solid #333;
        transition: all 0.2s;
    }

    /* プレイヤーカラー */
    .p1-style { background: linear-gradient(145deg, #0f172a, #2563eb); border-color: #60a5fa; }
    .p2-style { background: linear-gradient(145deg, #450a0a, #dc2626); border-color: #f87171; }
    .neutral-style { background: #111827; border-color: #374151; }

    /* ステータス文字 */
    .info-box { color: white; text-align: center; pointer-events: none; }
    .terrain-ico { font-size: 1.5rem; margin-bottom: 2px; }
    .stat-line { font-size: 0.75rem; font-weight: bold; opacity: 0.9; }
    .unit-tag { 
        margin-top: 6px; padding: 2px 8px; border-radius: 20px;
        background: rgba(255,255,255,0.9); color: black; font-size: 0.7rem; font-weight: 900;
    }
    .empty-tag { margin-top: 6px; font-size: 0.7rem; color: #6b7280; font-style: italic; }

    /* 行動済み・選択中の特殊効果 */
    .is-moved { filter: grayscale(1) opacity(0.5); }
    .is-selected { border: 4px solid #facc15 !important; transform: scale(1.05); z-index: 2; }

    /* 【操作層】Streamlitボタンを「完全に透明」にして最前面に */
    .stButton > button {
        position: absolute !important;
        top: 0 !important; left: 0 !important;
        width: 100% !important; height: 140px !important;
        z-index: 10 !important; /* 最前面 */
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        cursor: pointer;
    }
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. セッション管理 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.terrain = np.random.choice(["🌾", "🌲", "⛰️"], size=(MAP_SIZE, MAP_SIZE), p=[0.4, 0.35, 0.25])
    st.session_state.defense = np.zeros((MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.zeros((MAP_SIZE, MAP_SIZE))
    
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            t = st.session_state.terrain[r,c]
            if t == "⛰️":
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 220, 10
            elif t == "🌲":
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 120, 25
            else:
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 60, 50

    st.session_state.unit_type = np.full((MAP_SIZE, MAP_SIZE), None)
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool)
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.gold = {1: 500, 2: 500}
    st.session_state.turn = 1
    st.session_state.phase = "拡大"
    st.session_state.winner = None
    st.session_state.selected = None

# --- 4. ロジック ---
def handle_click(r, c):
    p, phase = st.session_state.turn, st.session_state.phase
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        if st.session_state.capitals[p] is None and owner == 0:
            st.session_state.capitals[p], st.session_state.owner[r, c] = (r, c), p
            st.session_state.defense[r, c] += 200
        elif owner == 0 and st.session_state.gold[p] >= 30:
            st.session_state.owner[r, c], st.session_state.gold[p] = p, st.session_state.gold[p] - 30

    elif phase == "配置" and owner == p:
        u_name = st.session_state.get("buying_unit", "剣士団")
        cost = UNITS[u_name]["cost"]
        if st.session_state.gold[p] >= cost:
            st.session_state.unit_type[r, c], st.session_state.gold[p] = u_name, st.session_state.gold[p] - cost
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
                        st.session_state.owner[r, c], st.session_state.unit_type[r, c] = p, atk_u
                        st.session_state.unit_type[sr, sc] = None
                elif st.session_state.unit_type[r, c] is None:
                    st.session_state.unit_type[r, c], st.session_state.unit_type[sr, sc] = atk_u, None
                st.session_state.moved[r, c] = True
            st.session_state.selected = None

# --- 5. メイン画面 ---
st.title("🛡️ Kingdom Strategy")

if st.session_state.winner:
    st.success(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} 勝利！")
    if st.button("再起動"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    col_st1, col_st2, col_st3 = st.columns(3)
    col_st1.write(f"**手番:** {'Player A (Blue)' if p==1 else 'Player B (Red)'}")
    col_st2.write(f"**フェーズ:** {st.session_state.phase}")
    col_st3.write(f"**資金:** {st.session_state.gold[p]}G")

    if st.session_state.phase == "配置":
        st.session_state.buying_unit = st.selectbox("雇用ユニット", list(UNITS.keys()))

    if st.button(f"➔ {st.session_state.phase}フェーズを終了"):
        if st.session_state.phase == "拡大": st.session_state.phase = "配置"
        elif st.session_state.phase == "配置": st.session_state.phase = "侵攻"
        else:
            st.session_state.gold[p] += int(st.session_state.economy[st.session_state.owner == p].sum())
            st.session_state.moved.fill(False)
            st.session_state.turn = 3 - p
            st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.rerun()

    # --- マップ描画（表示層と操作層を分離） ---
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r, c]
            terrain = st.session_state.terrain[r, c]
            unit = st.session_state.unit_type[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            # CSSクラスの決定
            style_class = "p1-style" if owner == 1 else "p2-style" if owner == 2 else "neutral-style"
            if st.session_state.moved[r, c]: style_class += " is-moved"
            if (r, c) == st.session_state.selected: style_class += " is-selected"

            with cols[c]:
                # 1. 親コンテナ開始
                st.markdown('<div class="tile-container">', unsafe_allow_html=True)
                
                # 2. 【表示層】HTML/CSS
                st.markdown(f"""
                    <div class="tile-display {style_class}">
                        <div class="info-box">
                            <div class="terrain-ico">{terrain}{'🏰' if is_cap else ''}</div>
                            <div class="stat-line">🛡️ {int(st.session_state.defense[r,c])}</div>
                            <div class="stat-line">💰 {int(st.session_state.economy[r,c])}</div>
                            <div class="{'unit-tag' if unit else 'empty-tag'}">
                                {UNITS[unit]['icon'] + " " + unit if unit else "空"}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 3. 【操作層】透明ボタン（keyを必ずユニークに）
                st.button("", key=f"btn_{r}_{c}", on_click=handle_click, args=(r, c))
                
                # 4. コンテナ終了
                st.markdown('</div>', unsafe_allow_html=True)