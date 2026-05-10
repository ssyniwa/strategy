import streamlit as st
import numpy as np
import base64
from io import BytesIO
import google.generativeai as genai

# --- 1. 基本設定と定数 ---
MAP_SIZE = 6
UNITS = {
    "剣士団": {"cost": 100, "atk": 100, "icon": "⚔️"},
    "槍兵団": {"cost": 200, "atk": 200, "icon": "🔱"},
    "騎兵団": {"cost": 400, "atk": 400, "icon": "🐎"},
    "銃兵団": {"cost": 600, "atk": 600, "icon": "🔫"},
    "砲兵団": {"cost": 800, "atk": 800, "icon": "💣"},
}
def generate_map_background(prompt_text):
    # Nano Banana 2 (Gemini 3 Flash Image) モデルを指定
    # ※API上の正式な識別子は 'gemini-3-flash-image' または 'imagen-3' です
    model = genai.GenerativeModel('gemini-3-flash')
    
    # 画像生成リクエスト
    # 注意: モデルによって引数名が 'prompt' や 'content' と異なる場合があります
    response = model.generate_content(
        prompt_text,
        generation_config={
            "candidate_count": 1,
            # 画像生成に特化したパラメータをここに追加
        }
    )
    
    # 応答から画像データを抽出
    if response.candidates[0].content.parts[0].inline_data:
        return response.candidates[0].content.parts[0].inline_data.data
    return None
# --- 2. Gemini API 背景生成ロジック ---
def generate_world_map_bg():
    """地形分布をプロンプト化してImagen(Nano Banana 2)で画像を生成"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return ""
        
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # 地形分布の解析
        mountains = np.sum(st.session_state.defense > 160)
        fields = np.sum(st.session_state.economy > 35)
        forests = (MAP_SIZE * MAP_SIZE) - mountains - fields
        
        # 内部ツール(image_generation)を利用した背景生成のシミュレーション命令
        # 実際の実装では Imagen モデルを指定して呼び出します
        prompt = (
            f"Fantasy world map background, high angle top-down view, "
            f"cinematic lighting, parchment texture. Features: {mountains} rocky peaks, "
            f"{fields} golden plains, {forests} dark forests. Artistic and atmospheric."
        )
        
        # 注意: モデル名は環境に応じて 'gemini-3-flash' 等に調整
        # ここでは提供された生成機能を利用するインターフェースとして記述
        images = generate_map_background(prompt)

        if images:
            img = images[0]
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
    except Exception:
        return "" # 失敗時は無地
    return ""

# --- 3. セッション状態の初期化 ---
if 'owner' not in st.session_state:
    st.session_state.phase = "1_EXPANSION"
    st.session_state.turn = 1
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.units = {}
    st.session_state.capitals = {1: None, 2: None}
    st.session_state.money = {1: 300, 2: 300} # 広くなったので少し多めに
    st.session_state.battle_reports = []
    st.session_state.selected_pos = None
    st.session_state.moved_units = []
    st.session_state.winner = None
    # 起動時に一度だけ画像を生成
    st.session_state.bg_image = generate_world_map_bg()

# --- 4. ロジック関数 ---
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

# --- 5. UI設定とCSS ---
st.set_page_config(layout="wide", page_title="Fantasy War 6x6")

bg_url = st.session_state.bg_image
st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7)), url("{bg_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stButton > button {{
        width: 100% !important; height: 100px !important;
        border-radius: 8px !important;
        background-color: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(2px);
        border: 1px solid #999 !important;
    }}
    /* テキストカラー制御 */
    button:has(p:contains("🔵")) p {{ color: #0D47A1 !important; font-weight: 900 !important; }}
    button:has(p:contains("🔴")) p {{ color: #B71C1C !important; font-weight: 900 !important; }}
    button:has(p:contains("🟡")) p {{ color: #FBC02D !important; font-weight: 900 !important; }}
    button:has(p:contains("⬛")) p {{ color: #424242 !important; font-weight: 400 !important; }}
    .stButton p {{ font-size: 13px !important; text-shadow: none !important; }}
</style>
""", unsafe_allow_html=True)

# --- 6. メイン描画 ---
st.title("🛡️ Fantasy Strategy $6 \\times 6$")

if st.session_state.winner:
    st.balloons()
    st.success(f"🎊 PLAYER {st.session_state.winner} の完全勝利！")
    if st.button("再戦する"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# サイドバー
p = st.session_state.turn
st.sidebar.header(f"Turn: P{'A 🔵' if p==1 else 'B 🔴'}")
st.sidebar.metric("所持金", f"${st.session_state.money[p]}")

mode, selected_u = None, None
if st.session_state.phase == "1_EXPANSION":
    st.sidebar.info("拡大フェーズ: 未占領の土地(⚪)をクリックして領土を広げてください。")
elif st.session_state.phase == "2_PLACEMENT":
    mode = st.sidebar.radio("行動選択", ["部隊配置", "防御増強"])
    if mode == "部隊配置": selected_u = st.sidebar.selectbox("ユニット選択", list(UNITS.keys()))
    if st.sidebar.button("ターンを終了"):
        st.session_state.turn = 3 - p
        if st.session_state.turn == 1:
            st.session_state.phase = "3_INVASION"
            st.session_state.moved_units = []
        st.rerun()
elif st.session_state.phase == "3_INVASION":
    st.sidebar.warning("進軍フェーズ: 隣接する敵陣をクリックで攻撃！")
    if st.sidebar.button("進軍を完了"):
        st.session_state.turn = 3 - p
        if st.session_state.turn == 1: st.session_state.phase = "5_RESULT"
        st.rerun()
elif st.session_state.phase == "5_RESULT":
    if st.sidebar.button("次ターンの資金を回収"):
        for i in [1, 2]:
            income = np.sum(st.session_state.economy[st.session_state.owner == i])
            st.session_state.money[i] += int(income)
        st.session_state.turn = 1
        st.session_state.phase = "2_PLACEMENT"
        st.rerun()

# マップ描画コンテナ
map_container = st.container()
with map_container:
    for r in range(MAP_SIZE):
        cols = st.columns(MAP_SIZE)
        for c in range(MAP_SIZE):
            owner = st.session_state.owner[r,c]
            unit = st.session_state.units.get((r,c))
            def_v, eco_v = st.session_state.defense[r,c], st.session_state.economy[r,c]
            
            # アイコンとステータス
            status = "🔵" if owner == 1 else "🔴" if owner == 2 else "⚪"
            if st.session_state.selected_pos == (r,c): status = "🟡"
            elif (r,c) in st.session_state.moved_units and st.session_state.phase == "3_INVASION": status = "⬛"

            t_icon = "⛰️" if def_v > 160 else "🌾" if eco_v > 35 else "🌲"
            cap = "🏰" if (r,c) in st.session_state.capitals.values() else ""
            u_icon = unit["icon"] if unit else ""
            
            label = f"{status}{t_icon}{cap}\nDef:{def_v}\nEco:{eco_v}\n{u_icon}"
            cols[c].button(label, key=f"btn_{r}_{c}", on_click=on_cell_click, args=(r,c, mode, selected_u))