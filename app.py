import streamlit as st
import numpy as np
import base64
from io import BytesIO
import google.generativeai as genai
# --- 1. 基本設定 ---
MAP_SIZE = 6
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
def image_generation(prompt):
    # 画像生成モデル（Gemini 3 Flash Image / Nano Banana 2相当）の呼び出し
    # ※現在のSDK仕様に基づいた疑似コードです
    model = genai.GenerativeModel('gemini-3-flash')
    response = model.generate_content(
        prompt,
        # 画像生成用のパラメータ設定
    )
    return response.images # 生成された画像を取得
# --- 2. 背景画像生成ロジック ---
def generate_world_map_bg():
    """地形分布をプロンプト化して画像を生成し、Base64で返す"""
    # 地形の統計をとってプロンプトを構成
    mountains = np.sum(st.session_state.defense > 160)
    fields = np.sum(st.session_state.economy > 35)
    forests = (MAP_SIZE * MAP_SIZE) - mountains - fields
    
    prompt = (
        f"A beautiful bird's-eye view fantasy world map, "
        f"top-down perspective, high quality illustration. "
        f"The landscape consists of {mountains} rocky mountains, "
        f"{fields} golden wheat fields, and {forests} deep green forests. "
        f"Faded parchment style, artistic, epic game map background."
    )
    
    # 画像生成ツールの呼び出し (内部的にNano Banana 2を使用)
    try:
        # 実際には生成された画像オブジェクトが返ってくると仮定
        generated_images = image_generation(prompt)
        if generated_images:
            img = generated_images[0]
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
    except:
        return "" # 失敗時は背景なし
    return ""

# --- 3. セッション初期化 ---
if 'owner' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 200, 2: 200}
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None
    # 初回起動時に背景を生成
    st.session_state.bg_image = generate_world_map_bg()

# --- 4. CSS設定 (背景画像と文字色) ---
bg_css = f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.6)), url("{st.session_state.bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stButton > button {{
        width: 100% !important; height: 100px !important;
        border-radius: 8px !important;
        background-color: rgba(255, 255, 255, 0.8) !important; /* ボタンを半透明に */
        border: 1px solid #ccc !important;
    }}
    /* 文字色制御 */
    button:has(p:contains("🔵")) p {{ color: #1E88E5 !important; font-weight: 900 !important; }}
    button:has(p:contains("🔴")) p {{ color: #E53935 !important; font-weight: 900 !important; }}
    button:has(p:contains("🟡")) p {{ color: #D4AF37 !important; }}
    button:has(p:contains("⬛")) p {{ color: #666666 !important; }}
</style>
"""
st.markdown(bg_css, unsafe_allow_html=True)

# --- 5. ロジック (on_cell_click 等は前回のまま引き継ぎ) ---
def handle_battle(start_pos, end_pos):
    atk_p = st.session_state.turn
    def_p = 3 - atk_p
    unit = st.session_state.units[start_pos]
    target_unit = st.session_state.units.get(end_pos)
    target_def = st.session_state.defense[end_pos]
    victory = False
    if target_unit:
        if unit["atk"] > target_unit["atk"]: victory = True
        else: del st.session_state.units[start_pos]
    else:
        if unit["atk"] > target_def: victory = True
        else:
            st.session_state.defense[end_pos] -= unit["atk"]
            st.session_state.moved_units.append(start_pos)
    if victory:
        st.session_state.owner[end_pos] = atk_p
        st.session_state.units[end_pos] = unit
        st.session_state.defense[end_pos] = max(20, unit["atk"] // 2)
        del st.session_state.units[start_pos]
        st.session_state.moved_units.append(end_pos)
        if end_pos == st.session_state.capitals[def_p]:
            st.session_state.winner = atk_p
            st.session_state.phase = "GAME_OVER"

def on_cell_click(r, c, mode=None, unit_name=None):
    if st.session_state.winner: return
    p = st.session_state.turn
    if st.session_state.phase == "1_EXPANSION":
        if st.session_state.owner[r,c] == 0:
            st.session_state.owner[r,c] = p
            if st.session_state.capitals[p] is None: st.session_state.capitals[p] = (r, c)
            if np.all(st.session_state.owner != 0): st.session_state.phase = "2_PLACEMENT"
            st.session_state.turn = 3 - p
    elif st.session_state.phase == "2_PLACEMENT":
        if st.session_state.owner[r,c] == p:
            if mode == "部隊配置" and unit_name:
                u_data = UNITS[unit_name]
                if st.session_state.money[p] >= u_data["cost"]:
                    st.session_state.money[p] -= u_data["cost"]
                    st.session_state.units[(r,c)] = u_data.copy()
            elif mode == "防御増強":
                if st.session_state.money[p] >= 50:
                    st.session_state.money[p] -= 50
                    st.session_state.defense[r,c] += 100
    elif st.session_state.phase == "3_INVASION":
        if (r, c) in st.session_state.moved_units: return
        if st.session_state.selected_pos is None:
            if (r,c) in st.session_state.units and st.session_state.owner[r,c] == p:
                st.session_state.selected_pos = (r,c)
        else:
            start_pos = st.session_state.selected_pos
            if abs(r - start_pos[0]) + abs(c - start_pos[1]) == 1:
                if st.session_state.owner[r,c] == p:
                    if (r,c) not in st.session_state.units:
                        st.session_state.units[(r,c)] = st.session_state.units[start_pos]
                        del st.session_state.units[start_pos]
                        st.session_state.moved_units.append((r, c))
                else: handle_battle(start_pos, (r,c))
            st.session_state.selected_pos = None

# --- 6. メインUI ---
st.title("🗺️ ワールド・タクティクス (6x6)")

if st.session_state.winner:
    st.balloons(); st.success(f"PLAYER {st.session_state.winner} WIN!"); st.stop()

# サイドバー
p = st.session_state.turn
st.sidebar.header(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("資金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("コマンド", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("ユニット", list(UNITS.keys()))
    if st.sidebar.button("配置完了"):
        st.session_state.turn = 2 if st.session_state.turn == 1 else 1
        st.session_state.phase = "3_INVASION" if st.session_state.turn == 1 else "2_PLACEMENT"
        st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    if st.sidebar.button("進軍完了"):
        st.session_state.turn = 2 if st.session_state.turn == 1 else 1
        if st.session_state.turn == 1: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("次ターンへ"):
        for i in [1, 2]: st.session_state.money[i] += np.sum(st.session_state.economy[st.session_state.owner == i])
        st.session_state.turn = 1; st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ描画 (6x6)
for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        owner = st.session_state.owner[r,c]
        unit = st.session_state.units.get((r,c))
        def_v, eco_v = st.session_state.defense[r,c], st.session_state.economy[r,c]
        
        status_emoji = "⚪"
        if owner == 1: status_emoji = "🔵"
        elif owner == 2: status_emoji = "🔴"
        if st.session_state.selected_pos == (r,c): status_emoji = "🟡"
        elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": status_emoji = "⬛"

        t_icon = "⛰️" if def_v > 160 else "🌾" if eco_v > 35 else "🌲"
        cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
        u_icon = unit["icon"] if unit else ""
        
        label = f"{status_emoji}{t_icon}{cap}\n🛡️{def_v} 💰{eco_v}\n{u_icon}"
        cols[c].button(label, key=f"bt_{r}_{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))