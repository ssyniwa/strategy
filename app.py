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
    st.session_state.terrain = np.random.choice([0, 1, 2], size=(MAP_SIZE, MAP_SIZE), p=[0.4, 0.35, 0.25])
    st.session_state.defense = np.zeros((MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.zeros((MAP_SIZE, MAP_SIZE))
    
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            t = st.session_state.terrain[r,c]
            if t == 2: # 山岳
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 200, 10
            elif t == 1: # 森林
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 110, 25
            else: # 平野
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 60, 50

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
            st.session_state.capitals[p], st.session_state.owner[r, c] = (r, c), p
            st.session_state.defense[r, c] += 200
        elif owner == 0 and st.session_state.gold[p] >= 30:
            st.session_state.owner[r, c], st.session_state.gold[p] = p, st.session_state.gold[p] - 30

    elif phase == "配置" and owner == p:
        u_name = st.session_state.get("selected_unit", "剣士団")
        cost = UNITS[u_name]["cost"]
        if st.session_state.gold[p] >= cost:
            st.session_state.unit_type[r, c], st.session_state.gold[p] = u_name, st.session_state.gold[p] - cost
            st.session_state.defense[r, c] += 25

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

# --- 5. デザイン (CSS) ---
st.markdown("""
<style>
    .tile-container { position: relative; width: 100%; height: 130px; margin-bottom: 10px; }
    .tile-visual { 
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
        border-radius: 10px; border: 2px solid #555; overflow: hidden; z-index: 1;
    }
    .owner-1 { border-color: #3b82f6 !important; background: rgba(59, 130, 246, 0.2); }
    .owner-2 { border-color: #ef4444 !important; background: rgba(239, 68, 68, 0.2); }
    .is-moved { filter: grayscale(1) brightness(0.6); }
    .is-selected { border: 4px solid #facc15 !important; }

    .tile-bg { width: 100%; height: 100%; background-size: cover; position: absolute; z-index: 1; opacity: 0.7; }
    .tile-overlay { 
        position: absolute; width: 100%; height: 100%; z-index: 2; 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        color: white; pointer-events: none; text-shadow: 1px 1px 2px black;
    }
    .unit-tag { background: white; color: black; padding: 1px 5px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; margin-top: 4px; }
    .unit-empty { color: #ccc; font-size: 0.7rem; margin-top: 4px; font-style: italic; }

    /* 透明ボタンを最前面へ固定 */
    .stButton > button {
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 130px !important;
        z-index: 10 !important; background: transparent !important;
        border: none !important; color: transparent !important;
    }
    .stButton > button:hover { background: rgba(255, 255, 255, 0.1) !important; }
</style>
""", unsafe_allow_html=True)

# --- 6. メインUI ---
if st.session_state.winner:
    st.title(f"👑 Player {'A' if st.session_state.winner==1 else 'B'} 勝利！")
    if st.button("リスタート"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    st.subheader(f"Player {'A' if p==1 else 'B'} | {st.session_state.phase} | {st.session_state.gold[p]}G")
    
    col_menu1, col_menu2 = st.columns([2, 1])
    with col_menu1:
        if st.session_state.phase == "配置":
            st.session_state.selected_unit = st.selectbox("雇用ユニット", list(UNITS.keys()))
    with col_menu2:
        if st.button(f"➔ {st.session_state.phase}終了"):
            phases = ["拡大", "配置", "侵攻"]
            idx = phases.index(st.session_state.phase)
            if idx < 2:
                st.session_state.phase = phases[idx + 1]
            else:
                # ターン交代時の処理
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

    # マップ描画
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            t_idx = st.session_state.terrain[r, c]
            owner = st.session_state.owner[r, c]
            utype = st.session_state.unit_type[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            # CSSクラス付与
            w_class = f"owner-{owner}" if owner > 0 else ""
            if st.session_state.moved[r, c]: w_class += " is-moved"
            if (r, c) == st.session_state.selected: w_class += " is-selected"

            with cols[c]:
                # タイルの構造：1つのcontainerの中に「見た目」と「ボタン」を同居させる
                st.markdown(f'<div class="tile-container">', unsafe_allow_html=True)
                
                # 表示部分
                st.markdown(f"""
                    <div class="tile-visual {w_class}">
                        <div class="tile-bg" style="background-image: url('{images[t_idx]['img']}');"></div>
                        <div class="tile-overlay">
                            <div style="font-size:1.3rem;">{images[t_idx]['icon']} {'🏰' if is_cap else ''}</div>
                            <div style="font-size:0.7rem;">🛡️{int(st.session_state.defense[r,c])} 💰{int(st.session_state.economy[r,c])}</div>
                            {f'<div class="unit-tag">{UNITS[utype]["icon"]} {utype}</div>' if utype else '<div class="unit-empty">空</div>'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 操作部分（透明ボタン）
                st.button("", key=f"c_{r}_{c}", on_click=handle_click, args=(r, c))
                
                st.markdown('</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.write("📜 歴史")
        for log in reversed(st.session_state.history[-8:]):
            st.caption(log)