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
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(40, 101, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 41, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int) # 部隊数
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool) # 行動済みフラグ
    st.session_state.capitals = {1: None, 2: None} # 首都座標
    st.session_state.gold = {1: 100, 2: 100}
    st.session_state.turn = 1
    st.session_state.phase = "拡大" # 拡大 -> 配置 -> 侵攻 -> 結果(自動)
    st.session_state.winner = None
    st.session_state.history = ["ゲーム開始：拡大フェーズ（首都を決めてください）"]

# --- 3. ロジック関数 ---

def next_phase():
    if st.session_state.winner: return
    
    phases = ["拡大", "配置", "侵攻"]
    idx = phases.index(st.session_state.phase)
    
    if idx < 2:
        st.session_state.phase = phases[idx + 1]
    else:
        # 結果フェーズ（資金回収とターン交代）
        p = st.session_state.turn
        income = int(st.session_state.economy[st.session_state.owner == p].sum())
        st.session_state.gold[p] += income
        st.session_state.moved.fill(False) # グレーアウト解除
        st.session_state.turn = 3 - p
        st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.session_state.history.append(f"ターン交代: P{st.session_state.turn} の番 (収入 {income}G)")

def handle_click(r, c):
    p = st.session_state.turn
    phase = st.session_state.phase
    owner = st.session_state.owner[r, c]

    # --- 拡大フェーズ：首都決めと陣取り ---
    if phase == "拡大":
        if st.session_state.capitals[p] is None:
            if owner == 0:
                st.session_state.capitals[p] = (r, c)
                st.session_state.owner[r, c] = p
                st.session_state.defense[r, c] += 100 # 首都防御ボーナス
                st.session_state.history.append(f"P{p}: ({r},{c}) に首都を建設")
            else: st.toast("そこは占領されています")
        else:
            if owner == 0 and st.session_state.gold[p] >= 30:
                st.session_state.owner[r, c] = p
                st.session_state.gold[p] -= 30
                st.session_state.history.append(f"拡大: ({r},{c}) を領土化")
            elif owner == 0: st.toast("資金不足(30G)")

    # --- 配置フェーズ：部隊購入と防御強化 ---
    elif phase == "配置":
        if owner == p:
            if st.session_state.gold[p] >= 40:
                st.session_state.units[r, c] += 1
                st.session_state.defense[r, c] += 10
                st.session_state.gold[p] -= 40
                st.toast(f"({r},{c}) に部隊を配置（防御+10）")
            else: st.toast("資金不足(40G)")
        else: st.toast("自領を選んでください")

    # --- 侵攻フェーズ：隣接マス奪取 ---
    elif phase == "侵攻":
        # 1. 自分の部隊を選択（未行動であること）
        if 'selected' not in st.session_state or st.session_state.selected is None:
            if owner == p and st.session_state.units[r, c] > 0 and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
                st.toast(f"選択: ({r},{c}) の部隊。移動先を選んでください。")
            else: st.toast("動かせる部隊がいません（未行動の自軍部隊を選んでください）")
        # 2. 移動/攻撃先を選択
        else:
            sr, sc = st.session_state.selected
            if abs(sr - r) <= 1 and abs(sc - c) <= 1 and not (sr == r and sc == c):
                # 攻撃ロジック
                if owner != p:
                    power = (st.session_state.units[sr, sc] * 50) + np.random.randint(1, 100)
                    if power > st.session_state.defense[r, c]:
                        # 勝利判定
                        if (r, c) == st.session_state.capitals[3-p]:
                            st.session_state.winner = p
                        st.session_state.owner[r, c] = p
                        st.session_state.units[r, c] = st.session_state.units[sr, sc]
                        st.session_state.units[sr, sc] = 0
                        st.session_state.history.append(f"侵攻成功！ ({r},{c}) を奪取")
                    else:
                        st.session_state.history.append(f"侵攻失敗... ({r},{c}) の守りは固い")
                else: # 自領内移動
                    st.session_state.units[r, c] += st.session_state.units[sr, sc]
                    st.session_state.units[sr, sc] = 0
                
                st.session_state.moved[r, c] = True # グレーアウト化
                st.session_state.selected = None
            else:
                st.session_state.selected = None
                st.toast("隣接するマスしか選べません。選択解除。")

# --- 4. CSS (グレーアウト・勢力色) ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 110px; margin-bottom: 8px; border-radius: 12px; overflow: hidden; border: 2px solid #555; }
    .owner-1 { border-color: #3498db !important; box-shadow: 0 0 10px #3498db; }
    .owner-2 { border-color: #e74c3c !important; box-shadow: 0 0 10px #e74c3c; }
    .moved { filter: grayscale(1) brightness(0.7); } /* グレーアウト */
    
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.3); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; pointer-events: none; }
    .capital-mark { position: absolute; top: 2px; left: 5px; font-size: 1.5rem; z-index: 3; }
    
    .tile-wrapper div.stButton > button { position: absolute; top: 0; left: 0; width: 100% !important; height: 110px !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 10; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# --- 5. メインUI ---
if st.session_state.winner:
    st.balloons()
    st.title(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} の勝利！！")
    if st.button("もう一度遊ぶ"):
        st.session_state.clear()
        st.rerun()
else:
    st.title("🛡️ Kingdom Conquest")
    p = st.session_state.turn
    
    # ステータス
    c1, c2, c3 = st.columns(3)
    c1.metric("Turn", f"Player {'A' if p==1 else 'B'}")
    c2.info(f"フェーズ: **{st.session_state.phase}**")
    c3.metric("Gold", f"{st.session_state.gold[p]}G")

    if st.button(f"【{st.session_state.phase}】フェーズを終了する ➔"):
        next_phase()
        st.rerun()

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
            owner = st.session_state.owner[r, c]
            def_v = st.session_state.defense[r, c]
            eco_v = st.session_state.economy[r, c]
            unit_v = st.session_state.units[r, c]
            is_moved = st.session_state.moved[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            t_key = "mountain" if def_v > 130 else "field" if eco_v > 30 else "forest"
            tile = images[t_key]
            
            # クラス設定
            wrapper_class = f"owner-{owner}" if owner > 0 else ""
            if is_moved: wrapper_class += " moved"

            with cols[c]:
                st.markdown(f"""
                    <div class="tile-wrapper {wrapper_class}">
                        <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                        {"<div class='capital-mark'>🏰</div>" if is_cap else ""}
                        <div class="tile-info">
                            <div style="font-size:1.2rem;">{tile['icon']}</div>
                            <div style="font-size:0.7rem;">🛡️{def_v} 💰{eco_v}</div>
                            {f"<div style='background:white; color:black; padding:0 4px; border-radius:4px; font-weight:bold;'>⚔️{unit_v}</div>" if unit_v > 0 else ""}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.button("", key=f"t_{r}_{c}", on_click=handle_click, args=(r, c))

    with st.sidebar:
        st.write("📜 戦況履歴")
        for log in reversed(st.session_state.history[-10:]):
            st.caption(log)