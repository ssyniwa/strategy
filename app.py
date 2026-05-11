import streamlit as st
import numpy as np

# --- 1. ユニットデータ ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 110, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 220, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 450, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 650, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 900, "icon": "💣"},
}
MAP_SIZE = 5  # 画面に収まりやすくするため5x5に調整

# --- 2. CSS：表示パーツのデザイン ---
st.markdown("""
<style>
    /* ステータスカードのデザイン */
    .status-card {
        background-color: #1e293b;
        border: 2px solid #334155;
        border-radius: 8px 8px 0 0; /* 上側だけ丸く */
        height: 100px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        margin-bottom: 0px;
    }
    .owner-1 { border-color: #3b82f6; background-color: #1e3a8a; }
    .owner-2 { border-color: #ef4444; background-color: #7f1d1d; }
    
    .stat-row { font-size: 0.7rem; opacity: 0.9; }
    .unit-text { 
        font-size: 0.75rem; font-weight: bold; margin-top: 5px;
        background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;
    }
    .empty-text { font-size: 0.7rem; color: #64748b; font-style: italic; }

    /* 下の操作ボタンのスタイル調整 */
    .stButton > button {
        border-radius: 0 0 8px 8px !important; /* 下側だけ丸く */
        width: 100% !important;
        height: 35px !important;
        font-size: 0.8rem !important;
        margin-top: -1px !important; /* カードと密着させる */
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ゲーム状態の初期化 ---
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
    st.success(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} 勝利！")
    if st.button("再起動"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.metric("Player", "A" if p==1 else "B")
    col_h2.metric("Phase", st.session_state.phase)
    col_h3.metric("Gold", f"{st.session_state.gold[p]}G")

    if st.session_state.phase == "配置":
        st.session_state.buying_unit = st.selectbox("雇用:", list(UNITS.keys()))

    if st.button(f"➔ {st.session_state.phase}フェーズを終了"):
        if st.session_state.phase == "拡大": st.session_state.phase = "配置"
        elif st.session_state.phase == "配置": st.session_state.phase = "侵攻"
        else:
            st.session_state.gold[p] += int(st.session_state.economy[st.session_state.owner == p].sum())
            st.session_state.moved.fill(False)
            st.session_state.turn = 3 - p
            st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.rerun()

    # --- マップ描画 (分離レイアウト) ---
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r, c]
            terrain = st.session_state.terrain[r, c]
            unit = st.session_state.unit_type[r, c]
            defense = int(st.session_state.defense[r, c])
            economy = int(st.session_state.economy[r, c])
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            owner_class = f"owner-{owner}" if owner > 0 else ""
            
            with cols[c]:
                # 1. 上段：ステータス表示 (HTML)
                st.markdown(f"""
                    <div class="status-card {owner_class}">
                        <div style="font-size:1.2rem;">{terrain} {'🏰' if is_cap else ''}</div>
                        <div class="stat-row">🛡️{defense} 💰{economy}</div>
                        <div class="{'unit-text' if unit else 'empty-text'}">
                            {UNITS[unit]['icon'] + " " + unit if unit else "空"}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 2. 下段：操作ボタン (Streamlit Button)
                # ボタンのラベルには座標や状況に応じた文字を入れる
                btn_label = "選択中" if (r, c) == st.session_state.selected else "行動済" if st.session_state.moved[r, c] else "Action"
                st.button(btn_label, key=f"b_{r}_{c}", on_click=handle_click, args=(r, c))