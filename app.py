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

# --- 2. ゲーム状態の初期化 ---
MAP_SIZE = 6
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 150, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 40, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.gold = {1: 150, 2: 150}
    st.session_state.turn = 1
    st.session_state.phase = "準備" # 準備 -> 拡大 -> 内政 -> 戦闘
    st.session_state.history = ["ゲーム開始！"]

# --- 3. ゲームロジック ---

def next_phase():
    phases = ["準備", "拡大", "内政", "戦闘"]
    current_idx = phases.index(st.session_state.phase)
    
    if current_idx < 3:
        st.session_state.phase = phases[current_idx + 1]
    else:
        # ターン終了処理
        income = int(st.session_state.economy[st.session_state.owner == st.session_state.turn].sum())
        st.session_state.gold[st.session_state.turn] += income
        st.session_state.turn = 3 - st.session_state.turn
        st.session_state.phase = "準備"
        st.session_state.history.append(f"P{st.session_state.turn}のターン開始 (収入: {income}G)")

def handle_tile_click(r, c):
    phase = st.session_state.phase
    p = st.session_state.turn
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        if owner == 0 and st.session_state.gold[p] >= 50:
            st.session_state.owner[r, c] = p
            st.session_state.gold[p] -= 50
            st.session_state.history.append(f"拡大: ({r},{c}) を占領")
        elif owner != 0: st.toast("そこは既に占領されています")
        else: st.toast("資金不足です")

    elif phase == "内政":
        if owner == p and st.session_state.gold[p] >= 30:
            st.session_state.economy[r, c] += 10
            st.session_state.gold[p] -= 30
            st.toast(f"({r},{c}) の経済を強化！")
        elif owner != p: st.toast("自分の領土ではありません")

    elif phase == "戦闘":
        if owner != 0 and owner != p:
            power = np.random.randint(30, 100)
            target_def = st.session_state.defense[r, c]
            if power > target_def:
                st.session_state.owner[r, c] = p
                st.session_state.history.append(f"戦闘: ({r},{c}) を奪取！")
            else:
                st.session_state.history.append(f"戦闘: ({r},{c}) への攻撃失敗")
            next_phase() # 戦闘は1回のみでフェーズ終了
        elif owner == p: st.toast("自分の領土です")

# --- 4. CSS ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 100px; border-radius: 10px; overflow: hidden; border: 2px solid #444; }
    .owner-1 { border-color: #3498db; box-shadow: 0 0 10px #3498db; }
    .owner-2 { border-color: #e74c3c; box-shadow: 0 0 10px #e74c3c; }
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.4); color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none; }
    .tile-wrapper div.stButton > button { position: absolute; top: 0; left: 0; width: 100% !important; height: 100px !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 10; }
</style>
""", unsafe_allow_html=True)

# --- 5. UI構築 ---
st.title("⚔️ 4-Phase Strategy Map")

# ヘッダー情報
p_color = "🔵 Player A" if st.session_state.turn == 1 else "🔴 Player B"
c1, c2, c3 = st.columns(3)
c1.metric("Current Turn", p_color)
c2.metric("Phase", st.session_state.phase)
c3.metric("Gold", f"{st.session_state.gold[st.session_state.turn]}G")

# フェーズ進行ボタン
if st.button(f"【{st.session_state.phase}】フェーズを終了して次へ ➔"):
    next_phase()
    st.rerun()

st.divider()

# 画像ロード
images = {
    "mountain": {"icon": "⛰️", "img": get_base64_image("mount.png")},
    "field": {"icon": "🌾", "img": get_base64_image("field.png")},
    "forest": {"icon": "🌲", "img": get_base64_image("forest.png")}
}

# マップ描画
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r, c]
        def_v = st.session_state.defense[r, c]
        eco_v = st.session_state.economy[r, c]
        
        t_type = "mountain" if def_v > 120 else "field" if eco_v > 25 else "forest"
        tile = images[t_type]
        
        with cols[c]:
            st.markdown(f"""
                <div class="tile-wrapper owner-{owner}">
                    <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                    <div class="tile-info">
                        <div style="font-size:1.2rem;">{tile['icon']}</div>
                        <div style="font-size:0.7rem;">🛡️{def_v} 💰{eco_v}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.button("", key=f"b_{r}_{c}", on_click=handle_tile_click, args=(r, c))

# 履歴表示
with st.expander("📝 戦績ログ"):
    for log in reversed(st.session_state.history):
        st.write(log)