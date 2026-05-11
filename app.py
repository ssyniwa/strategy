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
            # 48KB程度なら png のままでもブラウザは処理可能です
            return f"data:image/png;base64,{data}"
    return None

# --- 2. ゲーム状態の初期化 ---
MAP_SIZE = 6
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.turn = 1 # 1: Player A, 2: Player B

# --- 3. 画面レイアウト用の最強CSS ---
st.markdown("""
<style>
    /* タイル全体のコンテナ */
    .tile-wrapper {
        position: relative;
        width: 100%;
        height: 100px;
        margin-bottom: 5px;
        border-radius: 10px;
        overflow: hidden;
        border: 2px solid rgba(255,255,255,0.1);
        transition: transform 0.2s;
    }
    .tile-wrapper:hover {
        transform: scale(1.02);
        border-color: rgba(255,255,255,0.5);
    }

    /* 背景画像レイヤー */
    .tile-bg {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover;
        background-position: center;
        z-index: 1;
    }

    /* 情報表示レイヤー（アイコン、防御、経済） */
    .tile-info {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 2;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(0,0,0,0.2); /* 画像を見やすくするための薄い膜 */
        color: white;
        font-size: 0.8rem;
        pointer-events: none; /* クリックを透過させる */
    }
    .tile-icon { font-size: 1.5rem; margin-bottom: 2px; }
    .status-line { font-weight: bold; text-shadow: 1px 1px 2px black; }

    /* 🔴🔵 占領状態のオーバーレイ */
    .owner-overlay {
        position: absolute;
        top: 5px; right: 5px;
        font-size: 1.2rem;
        z-index: 3;
    }

    /* 透明なStreamlitボタンを一番上に被せる */
    .tile-wrapper div.stButton > button {
        position: absolute;
        top: 0; left: 0;
        width: 100% !important;
        height: 100px !important;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10; /* 最前面でクリックを奪う */
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. ロジック関数 ---
def capture_tile(r, c):
    # 空き地なら現在のプレイヤーが占領
    if st.session_state.owner[r, c] == 0:
        st.session_state.owner[r, c] = st.session_state.turn
        # ターン交代
        st.session_state.turn = 3 - st.session_state.turn

# --- 5. メイン画面描画 ---
st.title("⚔️ Tactical World Conquest")

# サイドバー：ステータス
st.sidebar.header("📊 Game Status")
current_p = "Player A 🔵" if st.session_state.turn == 1 else "Player B 🔴"
st.sidebar.subheader(f"Next: {current_p}")
if st.sidebar.button("Map Reset"):
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.rerun()

# 画像アセット読み込み
TILE_DATA = {
    "mountain": {"icon": "⛰️", "img": get_base64_image("mount.png")},
    "field": {"icon": "🌾", "img": get_base64_image("field.png")},
    "forest": {"icon": "🌲", "img": get_base64_image("forest.png")}
}

# マップ生成
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形判定
        def_val = st.session_state.defense[r,c]
        eco_val = st.session_state.economy[r,c]
        if def_val > 160: t_type = "mountain"
        elif eco_val > 35: t_type = "field"
        else: t_type = "forest"
        
        tile = TILE_DATA[t_type]
        owner = st.session_state.owner[r,c]
        owner_mark = "🔵" if owner == 1 else "🔴" if owner == 2 else ""

        with cols[c]:
            # HTMLで見た目を作る
            st.markdown(f"""
                <div class="tile-wrapper">
                    <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                    <div class="owner-overlay">{owner_mark}</div>
                    <div class="tile-info">
                        <div class="tile-icon">{tile['icon']}</div>
                        <div class="status-line">🛡️{def_val}</div>
                        <div class="status-line">💰{eco_val}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # その上に透明なボタンを設置してクリックイベントを拾う
            st.button("", key=f"btn_{r}_{c}", on_click=capture_tile, args=(r, c))