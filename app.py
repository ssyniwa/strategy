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
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

# --- 2. CSS：ハイブリッド・タイルレイアウト ---
st.markdown("""
<style>
    .tile-container {
        position: relative;
        width: 100%;
        height: 110px;
        margin-bottom: 5px;
        border-radius: 10px;
        overflow: hidden;
        border: 2px solid #444;
    }
    .tile-visual {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover;
        background-position: center;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .owner-1 { box-shadow: inset 0 0 20px #3b82f6; border: 2px solid #3b82f6 !important; }
    .owner-2 { box-shadow: inset 0 0 20px #ef4444; border: 2px solid #ef4444 !important; }
    .is-moved { filter: grayscale(0.8) brightness(0.5); }
    .is-selected { border: 3px solid #facc15 !important; }
    .tile-label {
        color: white; font-weight: bold; text-shadow: 2px 2px 4px black; z-index: 2;
        text-align: center; font-size: 0.8rem;
    }
    .unit-badge {
        background: white; color: black; padding: 1px 4px; border-radius: 4px;
        font-size: 0.7rem; font-weight: bold; margin-top: 3px;
    }
    /* 透明ボタンを最前面に */
    .tile-container div.stButton > button {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. データと初期化 ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 110, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 220, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 450, "icon": "🐎"},
    "砲兵団": {"cost": 800, "atk": 900, "icon": "💣"},
}
MAP_SIZE = 6

if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.terrain = np.random.choice([0, 1, 2], size=(MAP_SIZE, MAP_SIZE)) 
    st.session_state.defense = np.zeros((MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.zeros((MAP_SIZE, MAP_SIZE))
    
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            t = st.session_state.terrain[r,c]
            if t == 2: # 山
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 220, 10
            elif t == 1: # 森林
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 120, 25
            else: # 平野
                st.session_state.defense[r,c], st.session_state.economy[r,c] = 60, 55

    st.session_state.unit_type = np.full((MAP_SIZE, MAP_SIZE), None)
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool)
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.gold = {1: 300, 2: 300} # 初期資金（拡大フェーズ用）
    st.session_state.turn = 1
    st.session_state.phase = "拡大"
    st.session_state.winner = None

# --- 4. クリックハンドラ ---
def handle_click(r, c):
    p, phase = st.session_state.turn, st.session_state.phase
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        # まだ自分の陣地でない場所のみ選択可能
        if owner == 0:
            if st.session_state.capitals[p] is None:
                # 最初の1手は首都
                st.session_state.capitals[p] = (r, c)
                st.session_state.owner[r, c] = p
                st.session_state.defense[r, c] += 200
                st.session_state.turn = 3 - p # 交代
            elif st.session_state.gold[p] >= 40:
                # 2手目以降は資金を消費して陣地拡大
                st.session_state.owner[r, c] = p
                st.session_state.gold[p] -= 40
                st.session_state.turn = 3 - p # 交代

    elif phase == "配置" and owner == p:
        u_name = st.session_state.get("buying_unit", "剣士団")
        if st.session_state.gold[p] >= UNITS[u_name]["cost"]:
            st.session_state.unit_type[r, c] = u_name
            st.session_state.gold[p] -= UNITS[u_name]["cost"]

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
                        st.session_state.moved[r, c] = True
                elif st.session_state.unit_type[r, c] is None:
                    st.session_state.unit_type[r, c], st.session_state.unit_type[sr, sc] = atk_u, None
                    st.session_state.moved[r, c] = True
            st.session_state.selected = None

# --- 5. UI構築 ---
if st.session_state.winner:
    st.title(f"👑 Player {'A' if st.session_state.winner==1 else 'B'} 勝利！")
    if st.button("リセット"): st.session_state.clear(); st.rerun()
else:
    p = st.session_state.turn
    st.subheader(f"Turn: Player {'A' if p==1 else 'B'} | Phase: {st.session_state.phase}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("資金", f"{st.session_state.gold[p]}G")
    
    with col3:
        button_label = "軍備フェーズへ移動" if st.session_state.phase == "拡大" else f"{st.session_state.phase}終了"
        if st.button(button_label):
            if st.session_state.phase == "拡大":
                # 拡大終了時に各陣地の経済力の合計を軍資金として追加
                st.session_state.gold[1] += int(st.session_state.economy[st.session_state.owner == 1].sum())
                st.session_state.gold[2] += int(st.session_state.economy[st.session_state.owner == 2].sum())
                st.session_state.phase = "配置"
                st.session_state.turn = 1
            elif st.session_state.phase == "配置":
                st.session_state.phase = "侵攻"
            else:
                # 侵攻終了 → ターン交代
                st.session_state.moved.fill(False)
                st.session_state.turn = 3 - p
                st.session_state.phase = "配置"
            st.rerun()

    if st.session_state.phase == "配置":
        st.session_state.buying_unit = st.selectbox("雇用ユニット", list(UNITS.keys()))

    # 地形設定
    imgs = {0: get_base64_image("field.png"), 1: get_base64_image("forest.png"), 2: get_base64_image("mount.png")}
    icons = {0: "🌾", 1: "🌲", 2: "⛰️"}

    # マップ描画
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r, c]
            t_type = st.session_state.terrain[r, c]
            unit = st.session_state.unit_type[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            style_class = f"owner-{owner}" if owner > 0 else ""
            if st.session_state.moved[r, c]: style_class += " is-moved"
            if (r, c) == st.session_state.selected: style_class += " is-selected"

            with cols[c]:
                st.markdown(f'''
                    <div class="tile-container">
                        <div class="tile-visual {style_class}" style="background-image: url('{imgs[t_type]}');">
                            <div class="tile-label">
                                {icons[t_type]}{'🏰' if is_cap else ''}<br>
                                <span style="font-size:0.6rem;">🛡️{int(st.session_state.defense[r,c])} 💰{int(st.session_state.economy[r,c])}</span>
                            </div>
                            <div class="{"unit-badge" if unit else ""}">
                                {UNITS[unit]["icon"] + " " + unit if unit else "空"}
                            </div>
                        </div>
                ''', unsafe_allow_html=True)
                
                st.button("", key=f"btn_{r}_{c}", on_click=handle_click, args=(r, c))
                st.markdown('</div>', unsafe_allow_html=True)