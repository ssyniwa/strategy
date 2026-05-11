import streamlit as st
import numpy as np

# --- 1. データ定義 ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 110, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 220, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 450, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 650, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 900, "icon": "💣"},
}
MAP_SIZE = 5

# --- 2. CSS：レイアウトの要 ---
st.markdown("""
<style>
    /* 親コンテナ：ここに全ての要素を詰め込む */
    .tile-container {
        position: relative;
        width: 100%;
        height: 130px;
        margin-bottom: 10px;
    }

    /* 地形画像と色表示の層 (z-index: 1) */
    .tile-base {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        border-radius: 10px;
        border: 2px solid #444;
        z-index: 1;
        overflow: hidden;
        transition: 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        background-color: #2c3e50;
    }

    /* 所有者別の背景グラデーション */
    .p1-bg { background: linear-gradient(135deg, #1e3a8a, #3b82f6); border-color: #60a5fa !important; }
    .p2-bg { background: linear-gradient(135deg, #7f1d1d, #ef4444); border-color: #f87171 !important; }
    .neutral-bg { background: #1f2937; }

    /* ステータス表示層 (z-index: 2) */
    .status-overlay {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 2;
        pointer-events: none; /* クリックをボタンに通す */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-shadow: 1px 1px 3px black;
    }

    /* 部隊タグ */
    .unit-badge {
        background: white; color: black; padding: 2px 6px;
        border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-top: 5px;
    }
    .empty-badge { font-size: 0.7rem; color: #cbd5e1; font-style: italic; margin-top: 5px; }

    /* 操作ボタン (z-index: 10) */
    .stButton > button {
        position: absolute !important;
        top: 0 !important; left: 0 !important;
        width: 100% !important;
        height: 130px !important;
        z-index: 10 !important;
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ゲーム初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.terrain = np.random.choice(["🌾", "🌲", "⛰️"], size=(MAP_SIZE, MAP_SIZE))
    st.session_state.defense = np.random.randint(50, 100, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(20, 50, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.unit_type = np.full((MAP_SIZE, MAP_SIZE), None)
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool)
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.gold = {1: 500, 2: 500}
    st.session_state.turn = 1
    st.session_state.phase = "拡大"
    st.session_state.winner = None

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
        u_name = st.session_state.get("current_unit", "剣士団")
        cost = UNITS[u_name]["cost"]
        if st.session_state.gold[p] >= cost:
            st.session_state.unit_type[r, c], st.session_state.gold[p] = u_name, st.session_state.gold[p] - cost

    elif phase == "侵攻":
        if st.session_state.selected is None:
            if owner == p and st.session_state.unit_type[r, c] and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
        else:
            sr, sc = st.session_state.selected
            if abs(sr - r) <= 1 and abs(sc - c) <= 1:
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

# --- 5. メインUI ---
st.title("🛡️ Kingdom Conquest")

if st.session_state.winner:
    st.balloons()
    st.success(f"Player {'A' if st.session_state.winner==1 else 'B'} の勝利！")
    if st.button("再起動"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    col_st = st.columns(3)
    col_st[0].metric("Player", "A" if p==1 else "B")
    col_st[1].metric("Phase", st.session_state.phase)
    col_st[2].metric("Gold", f"{st.session_state.gold[p]}G")

    if st.session_state.phase == "配置":
        st.session_state.current_unit = st.selectbox("雇用ユニット", list(UNITS.keys()))

    if st.button(f"➔ 【{st.session_state.phase}】フェーズを終了"):
        if st.session_state.phase == "拡大": st.session_state.phase = "配置"
        elif st.session_state.phase == "配置": st.session_state.phase = "侵攻"
        else:
            st.session_state.gold[p] += int(st.session_state.economy[st.session_state.owner == p].sum())
            st.session_state.moved.fill(False)
            st.session_state.turn = 3 - p
            st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.rerun()

    # マップ描画
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r, c]
            terrain = st.session_state.terrain[r, c]
            unit = st.session_state.unit_type[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            bg_class = "p1-bg" if owner == 1 else "p2-bg" if owner == 2 else "neutral-bg"
            if st.session_state.moved[r, c]: bg_class += " grayscale" # 行動済み

            with cols[c]:
                # コンテナの開始
                st.markdown(f'<div class="tile-container">', unsafe_allow_html=True)
                
                # 表示層 (z-index: 1 & 2)
                st.markdown(f"""
                    <div class="tile-base {bg_class}">
                        <div class="status-overlay">
                            <div style="font-size:1.5rem;">{terrain} {'🏰' if is_cap else ''}</div>
                            <div style="font-size:0.7rem;">🛡️{int(st.session_state.defense[r,c])} 💰{int(st.session_state.economy[r,c])}</div>
                            <div class="{'unit-badge' if unit else 'empty-badge'}">
                                {UNITS[unit]['icon'] + " " + unit if unit else "空"}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 操作層 (z-index: 10)
                st.button("", key=f"tile_{r}_{c}", on_click=handle_click, args=(r, c))
                
                st.markdown('</div>', unsafe_allow_html=True)