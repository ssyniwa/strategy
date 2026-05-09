import streamlit as st
import numpy as np

st.set_page_config(page_title="戦略陣地取り", layout="wide")

# --- 設定 ---
MAP_SIZE = 5
INITIAL_ATTACK = 10  # 1回クリックで送り込む部隊の基本攻撃力

# --- セッション状態（データ保持） ---
if 'owner' not in st.session_state:
    # 0: 空き地, 1: プレイヤーA, 2: プレイヤーB
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    # 各マスの現在の防御力（戦力）
    st.session_state.power = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.turn = 1

def handle_click(r, c):
    current_turn = st.session_state.turn
    current_owner = st.session_state.owner[r, c]
    current_power = st.session_state.power[r, c]

    # 1. 自分の陣地、または空き地の場合：戦力を増強
    if current_owner == 0 or current_owner == current_turn:
        st.session_state.owner[r, c] = current_turn
        st.session_state.power[r, c] += INITIAL_ATTACK
        next_turn()
    
    # 2. 相手の陣地の場合：攻撃を仕掛ける
    else:
        if INITIAL_ATTACK > current_power:
            # 相手の戦力を上回ったので奪取成功
            st.session_state.owner[r, c] = current_turn
            st.session_state.power[r, c] = INITIAL_ATTACK - current_power
            st.success(f"地点 ({r}, {c}) を奪取しました！")
            next_turn()
        else:
            # 相手の戦力が高いので、戦力を削るだけで終了
            st.session_state.power[r, c] -= INITIAL_ATTACK
            st.error(f"攻撃失敗！相手の戦力を {INITIAL_ATTACK} 削りました。")
            next_turn()

def next_turn():
    st.session_state.turn = 2 if st.session_state.turn == 1 else 1

# --- 画面UI ---
st.title("⚔️ 陣地奪取タクティクス")
st.sidebar.info(f"あなたの攻撃力: **{INITIAL_ATTACK}**")
st.sidebar.write(f"現在のターン: **{'プレイヤーA (🔵)' if st.session_state.turn == 1 else 'プレイヤーB (🔴)'}**")

# CSSでボタンと文字の見た目を調整
st.markdown("""
<style>
    .stButton>button { height: 80px; width: 100%; border-radius: 5px; font-weight: bold; }
    .power-label { font-size: 12px; color: #555; }
</style>
""", unsafe_allow_html=True)

# グリッド描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r, c]
        power = st.session_state.power[r, c]
        
        # 見た目の設定
        color = "⚪"
        if owner == 1: color = "🔵"
        if owner == 2: color = "🔴"
        
        button_label = f"{color}\n({power})" if power > 0 else "－"
        
        # ボタン配置
        cols[c].button(button_label, key=f"cell-{r}-{c}", on_click=handle_click, args=(r, c))

if st.button("ゲームリセット"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()