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

# --- 2. ユニット・地形データ ---
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}

MAP_SIZE = 6

# --- 3. ゲーム状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 150, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 50, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.unit_type = np.full((MAP_SIZE, MAP_SIZE), None) # 配置ユニット名
    st.session_state.moved = np.zeros((MAP_SIZE, MAP_SIZE), dtype=bool)
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.gold = {1: 300, 2: 300} # 初期資金
    st.session_state.turn = 1
    st.session_state.phase = "拡大"
    st.session_state.winner = None
    st.session_state.history = ["ゲーム開始：拡大フェーズで首都を決めてください。"]
    st.session_state.selected = None

# --- 4. ロジック関数 ---

def next_phase():
    if st.session_state.winner: return
    phases = ["拡大", "配置", "侵攻"]
    current_idx = phases.index(st.session_state.phase)
    
    if current_idx < 2:
        st.session_state.phase = phases[current_idx + 1]
    else:
        # 結果フェーズ (資金回収とリセット)
        p = st.session_state.turn
        income = int(st.session_state.economy[st.session_state.owner == p].sum())
        st.session_state.gold[p] += income
        st.session_state.moved.fill(False)
        st.session_state.turn = 3 - p
        # 次のターンへ：首都があれば配置から、なければ拡大から
        st.session_state.phase = "配置" if st.session_state.capitals[st.session_state.turn] else "拡大"
        st.session_state.history.append(f"ターン交代: P{st.session_state.turn} (収入 {income}G)")

def handle_click(r, c):
    p = st.session_state.turn
    phase = st.session_state.phase
    owner = st.session_state.owner[r, c]

    if phase == "拡大":
        if st.session_state.capitals[p] is None:
            if owner == 0:
                st.session_state.capitals[p] = (r, c)
                st.session_state.owner[r, c] = p
                st.session_state.defense[r, c] += 200 # 首都ボーナス
                st.session_state.history.append(f"P{p}: ({r},{c}) に首都を建設！")
            else: st.toast("そこは占領されています")
        else:
            if owner == 0 and st.session_state.gold[p] >= 30:
                st.session_state.owner[r, c] = p
                st.session_state.gold[p] -= 30
                st.session_state.history.append(f"拡大: ({r},{c}) を占領")
            elif owner == 0: st.toast("資金不足(30G)")

    elif phase == "配置":
        if owner == p:
            # ユニット選択はUI側で行うので、ここでは選択されたユニットを配置
            u_name = st.session_state.selected_unit_to_buy
            cost = UNITS[u_name]["cost"]
            if st.session_state.gold[p] >= cost:
                st.session_state.unit_type[r, c] = u_name
                st.session_state.gold[p] -= cost
                st.session_state.defense[r, c] += 20 # 防御強化
                st.toast(f"{u_name} を配置完了！")
            else: st.toast("資金が足りません")
        else: st.toast("自分の領土を選んでください")

    elif phase == "侵攻":
        if st.session_state.selected is None:
            if owner == p and st.session_state.unit_type[r, c] is not None and not st.session_state.moved[r, c]:
                st.session_state.selected = (r, c)
                st.toast(f"選択: {st.session_state.unit_type[r, c]} (移動先を選んでください)")
            else: st.toast("動かせる部隊がいません")
        else:
            sr, sc = st.session_state.selected
            if abs(sr - r) <= 1 and abs(sc - c) <= 1 and not (sr == r and sc == c):
                # 戦闘または移動
                attacker_unit = st.session_state.unit_type[sr, sc]
                if owner != p:
                    # 攻撃
                    atk_power = UNITS[attacker_unit]["atk"] + np.random.randint(1, 100)
                    if atk_power > st.session_state.defense[r, c]:
                        # 勝利判定
                        if (r, c) == st.session_state.capitals[3-p]:
                            st.session_state.winner = p
                        # 占領成功
                        st.session_state.owner[r, c] = p
                        st.session_state.unit_type[r, c] = attacker_unit
                        st.session_state.unit_type[sr, sc] = None
                        st.session_state.history.append(f"侵攻成功! ({r},{c}) を奪取")
                    else:
                        st.session_state.history.append(f"侵攻失敗... ({r},{c}) の守りは固い")
                else:
                    # 移動
                    if st.session_state.unit_type[r, c] is None:
                        st.session_state.unit_type[r, c] = attacker_unit
                        st.session_state.unit_type[sr, sc] = None
                    else: st.toast("移動先に既に部隊がいます")
                
                st.session_state.moved[r, c] = True
                st.session_state.selected = None
            else:
                st.session_state.selected = None
                st.toast("隣接マス以外は移動できません")

# --- 5. CSS ---
st.markdown("""
<style>
    .tile-wrapper { position: relative; width: 100%; height: 110px; margin-bottom: 8px; border-radius: 10px; overflow: hidden; border: 2px solid #555; }
    .owner-1 { border-color: #3498db !important; box-shadow: 0 0 10px #3498db; }
    .owner-2 { border-color: #e74c3c !important; box-shadow: 0 0 10px #e74c3c; }
    .moved { filter: grayscale(1) brightness(0.6); }
    .tile-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; z-index: 1; }
    .tile-info { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; background: rgba(0,0,0,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; pointer-events: none; }
    .cap-mark { position: absolute; top: 2px; left: 5px; font-size: 1.4rem; z-index: 3; }
    .unit-tag { background: white; color: black; padding: 0 4px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; margin-top: 2px; }
    .tile-wrapper div.stButton > button { position: absolute; top: 0; left: 0; width: 100% !important; height: 110px !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 10; }
</style>
""", unsafe_allow_html=True)

# --- 6. メインUI ---
if st.session_state.winner:
    st.title(f"🏆 Player {'A' if st.session_state.winner==1 else 'B'} 勝利！！")
    st.balloons()
    if st.button("再挑戦"):
        st.session_state.clear()
        st.rerun()
else:
    st.title("🛡️ Kingdom Conquest Full")
    
    # 統計
    p = st.session_state.turn
    c1, c2, c3 = st.columns(3)
    c1.metric("Turn", f"Player {'A' if p==1 else 'B'}")
    c2.warning(f"Phase: {st.session_state.phase}")
    c3.metric("Gold", f"{st.session_state.gold[p]}G")

    # フェーズ操作
    if st.session_state.phase == "配置":
        st.session_state.selected_unit_to_buy = st.selectbox("購入ユニット選択", list(UNITS.keys()))
        st.caption(f"コスト: {UNITS[st.session_state.selected_unit_to_buy]['cost']}G")

    if st.button(f"【{st.session_state.phase}】終了して次へ"):
        next_phase()
        st.rerun()

    # 画像アセット
    images = {
        "mountain": {"icon": "⛰️", "img": get_base64_image("mount.png")},
        "field": {"icon": "🌾", "img": get_base64_image("field.png")},
        "forest": {"icon": "🌲", "img": get_base64_image("forest.png")}
    }

    # マップ生成
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r, c]
            def_v = st.session_state.defense[r, c]
            eco_v = st.session_state.economy[r, c]
            utype = st.session_state.unit_type[r, c]
            is_moved = st.session_state.moved[r, c]
            is_cap = (r, c) == st.session_state.capitals[1] or (r, c) == st.session_state.capitals[2]
            
            # 地形判定 (山岳を追加)
            if def_v > 150: t_key = "mountain"
            elif eco_v > 35: t_key = "field"
            else: t_key = "forest"
            tile = images[t_key]
            
            w_class = f"owner-{owner}" if owner > 0 else ""
            if is_moved: w_class += " moved"

            with cols[c]:
                st.markdown(f"""
                    <div class="tile-wrapper {w_class}">
                        <div class="tile-bg" style="background-image: url('{tile['img']}');"></div>
                        {"<div class='cap-mark'>🏰</div>" if is_cap else ""}
                        <div class="tile-info">
                            <div style="font-size:1.1rem;">{tile['icon']}</div>
                            <div style="font-size:0.6rem;">🛡️{def_v} 💰{eco_v}</div>
                            {f"<div class='unit-tag'>{UNITS[utype]['icon']} {utype}</div>" if utype else ""}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.button("", key=f"t_{r}_{c}", on_click=handle_click, args=(r, c))

    with st.sidebar:
        st.write("📜 ログ")
        for log in reversed(st.session_state.history[-8:]):
            st.caption(log)