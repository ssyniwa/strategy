import streamlit as st
import numpy as np

# --- ページ設定 ---
st.set_page_config(page_title="本格戦略陣地取り", layout="wide")

# --- 定数設定 ---
MAP_SIZE = 5
INCOME_PER_TERRITORY = 100

# ユニットデータ (名前: [必要資金, 攻撃力, 防御力])
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "def": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "def": 100, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "def": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "def": 400, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "def": 800, "icon": "💣"},
}

# --- セッション状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.money = {1: 0, 2: 0}
    st.session_state.turn = 1
    st.session_state.phase = "EXPANSION"  # EXPANSION (拡大) or BATTLE (戦闘)

# --- ヘルパー関数 ---
def next_turn():
    # 全てのマスが埋まったかチェック
    if np.all(st.session_state.owner != 0) and st.session_state.phase == "EXPANSION":
        st.session_state.phase = "BATTLE"
        st.toast("全てのマップが埋まりました！戦闘フェーズ開始！")
    
    # ターン交代
    st.session_state.turn = 2 if st.session_state.turn == 1 else 1
    
    # 戦闘フェーズなら、ターン開始時に資金追加
    if st.session_state.phase == "BATTLE":
        territory_count = np.sum(st.session_state.owner == st.session_state.turn)
        income = territory_count * INCOME_PER_TERRITORY
        st.session_state.money[st.session_state.turn] += income

def handle_click(r, c, selected_unit_name=None):
    p = st.session_state.turn
    target_owner = st.session_state.owner[r, c]
    target_def = st.session_state.defense[r, c]

    # 【拡大フェーズ】空き地を埋める
    if st.session_state.phase == "EXPANSION":
        if target_owner == 0:
            st.session_state.owner[r, c] = p
            st.session_state.defense[r, c] = 100 # 初期防御力
            next_turn()
        else:
            st.error("空き地を選んでください")

    # 【戦闘フェーズ】ユニットを選んで攻撃
    elif st.session_state.phase == "BATTLE":
        unit = UNITS[selected_unit_name]
        
        if st.session_state.money[p] < unit["cost"]:
            st.error("資金が足りません！")
            return

        # 資金消費
        st.session_state.money[p] -= unit["cost"]

        if target_owner == p:
            # 自陣なら防御力アップ（補給）
            st.session_state.defense[r, c] += unit["def"]
            st.success(f"{selected_unit_name}を配置！防御力が {unit['def']} 上昇。")
        else:
            # 敵陣なら攻撃
            if unit["atk"] > target_def:
                st.session_state.owner[r, c] = p
                st.session_state.defense[r, c] = unit["atk"] - target_def
                st.success(f"奪取成功！ {selected_unit_name}が占領しました。")
            else:
                st.session_state.defense[r, c] -= unit["atk"]
                st.warning(f"攻撃失敗！敵の防御力を {unit['atk']} 削りました。")
        
        next_turn()

# --- UI構築 ---
st.title("⚔️ 戦略陣地取り Web App")

# ステータス表示
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("ターン", "プレイヤーA (🔵)" if st.session_state.turn == 1 else "プレイヤーB (🔴)")
with c2:
    phase_name = "空き地拡大期" if st.session_state.phase == "EXPANSION" else "総力戦期"
    st.metric("フェーズ", phase_name)
with c3:
    m = st.session_state.money[st.session_state.turn]
    st.metric("所持資金", f"${m}")

# ユニット選択（戦闘フェーズのみ）
selected_unit = None
if st.session_state.phase == "BATTLE":
    st.write("### 派遣する部隊を選択してください")
    cols_unit = st.columns(len(UNITS))
    unit_names = list(UNITS.keys())
    # ラジオボタンでユニットを選択
    selected_unit = st.radio("部隊選択:", unit_names, horizontal=True)
    u_info = UNITS[selected_unit]
    st.info(f"選択中: {selected_unit} (コスト:{u_info['cost']} / 攻撃:{u_info['atk']} / 防御:{u_info['def']})")

# マップ描画
st.write("### マップ")
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r, c]
        df = st.session_state.defense[r, c]
        
        icon = "⬜"
        if owner == 1: icon = "🔵"
        if owner == 2: icon = "🔴"
        
        label = f"{icon}\n({df})" if df > 0 else icon
        cols[c].button(label, key=f"btn-{r}-{c}", on_click=handle_click, args=(r, c, selected_unit))

# リセット
if st.sidebar.button("ゲームリセット"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()