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

# --- 2. ゲーム状態の初期化 ---
MAP_SIZE = 6
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    # 占領状況: 0=空き, 1=PlayerA, 2=PlayerB
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    # 地形パラメータ
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    # 資源とターン
    st.session_state.gold = {1: 100, 2: 100}
    st.session_state.turn = 1
    st.session_state.turn_count = 1
    st.session_state.history = []

# --- 3. ゲームロジック関数 ---
def handle_click(r, c):
    p = st.session_state.turn
    # 未占領地を占領するロジック
    if st.session_state.owner[r, c] == 0:
        cost = 50  # 占領コスト
        if st.session_state.gold[p] >= cost:
            st.session_state.owner[r, c] = p
            st.session_state.gold[p] -= cost
            st.session_state.history.append(f"Turn {st.session_state.turn_count}: P{p} が ({r},{c}) を占領")
            next_turn()
        else:
            st.toast("資金が足りません！", icon="⚠️")
    else:
        st.toast("既に占領されています", icon="🚫")

def next_turn():
    # ターン終了時に経済力に応じてゴールド加算
    for p in [1, 2]:
        # 自分の所有しているマスの経済合計を計算
        income = st.session_state.economy[st.session_state.owner == p].sum()
        st.session_state.gold[p] += int(income)
    
    # ターン交代
    st.session_state.turn = 2 if st.session_state.turn == 1 else 1
    st.session_state.turn_count += 1

# --- 4. CSS: 透明ボタンと画像レイヤーの融合 ---
st.markdown("""
<style>
    .tile-wrapper {
        position: relative;
        width: 100%;
        height: 110px;
        margin-bottom: 10px;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid rgba(255,255,255,0.1);
        transition: 0.3s;
    }
    /* 勢力カラーの枠線 */
    .owner-1 { border: 3px solid #3498db !important; box-shadow: 0 0 10px #3498db; }
    .owner-2 { border: 3px solid #e74c3c !important; box-shadow: 0 0 10px #e74c3c; }

    .tile-bg {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover;
        background-position: center;
        z-index: 1;
    }
    .tile-info {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 2;
        background: rgba(0,0,0,0.3);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        pointer-events: none;
    }
    .status-text { font-size: 0.7rem; font-weight: bold; text-shadow: 1px 1px 2px black; }
    
    /* 透明ボタンを最前面へ */
    .tile-wrapper div.stButton > button {
        position: absolute;
        top: 0; left: 0; width: 100% !important; height: 110px !important;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10;
    }
    .tile-wrapper div.stButton > button:hover {
        background: rgba(255,255,255,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. メインUI ---
st.title("⚔️ Strategic Conquest 6x6")

# ステータスバー
s_col1, s_col2, s_col3 = st.columns(3)
with s_col1:
    st.metric("Turn", st.session_state.turn_count)
with s_col2:
    st.metric("Player A Gold", f"{st.session_state.gold[1]}G", delta=int(st.session_state.economy[st.session_state.owner == 1].sum()))
with s_col3:
    st.metric("Player B Gold", f"{st.session_state.gold[2]}G", delta=int(st.session_state.economy[st.session_state.owner == 2].sum()))

st.divider()

# サイドバー：操作と履歴
with st.sidebar:
    st.header("🎮 Game Control")
    p_color = "🔵" if st.session_state.turn == 1 else "🔴"
    st.subheader(f"Next: Player {p_color}")
    if st.button("パス (ターン終了)"):
        next_turn()
        st.rerun()
    
    st.divider()
    st.write("📜 ログ")
    for log in reversed(st.session_state.history[-5:]):
        st.caption(log)

# 画像アセット
images = {
    "mountain": {"icon": "⛰️", "img": get_base64_image("mount.png")},
    "field": {"icon": "🌾", "img": get_base64_image("field.png")},
    "forest": {"icon": "🌲", "img": get_base64_image("forest.png")}
}

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形・パラメータ
        def_v = st.session_state.defense[r,c]
        eco_v = st.session_state.economy[r,c]
        owner = st.session_state.owner[r,c]
        
        if def_v > 160: t_type = "mountain"
        elif eco_v > 35: t_type = "field"
        else: t_type = "forest"
        
        tile = images[t_type]
        owner_class = f"owner-{owner}" if owner > 0 else ""

        with cols[c]:
            # HTML構造（背景+情報）
            st.markdown(f"""
                <div class="tile-wrapper {owner_class}">
                    <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                    <div class="tile-info">
                        <div style="font-size:1.2rem;">{tile['icon']}</div>
                        <div class="status-text">🛡️ {def_v}</div>
                        <div class="status-text">💰 {eco_v}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 透明ボタン
            st.button("", key=f"b_{r}_{c}", on_click=handle_click, args=(r, c))