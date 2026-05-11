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

# --- 2. 初期設定 ---
MAP_SIZE = 6
if 'owner' not in st.session_state:
    st.session_state.owner = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)
    st.session_state.defense = np.random.randint(50, 201, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.economy = np.random.randint(10, 51, size=(MAP_SIZE, MAP_SIZE))
    st.session_state.turn = 1

# --- 3. 基礎CSS（透明化とレイアウト） ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: rgba(0,0,0,0.4) !important;
        border: 1px solid white !important;
        color: white !important;
        background-size: cover !important;
        background-position: center !important;
    }
    div.stButton p {
        text-shadow: 2px 2px 4px black !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. メイン描画 ---
st.title("⚔️ $6 \\times 6$ World Tactics")

# 画像データの準備
images = {
    "mountain": get_base64_image("mount.png"),
    "field": get_base64_image("field.png"),
    "forest": get_base64_image("forest.png")
}

def on_click(r, c):
    if st.session_state.owner[r,c] == 0:
        st.session_state.owner[r,c] = st.session_state.turn
        st.session_state.turn = 3 - st.session_state.turn

# JavaScriptによる画像注入用のスクリプトを溜めるリスト
js_code = ""

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        d, e = st.session_state.defense[r,c], st.session_state.economy[r,c]
        t_key = "mountain" if d > 160 else "field" if e > 35 else "forest"
        img_b64 = images[t_key]
        
        # ボタンのキー
        b_key = f"tile_{r}_{c}"
        
        # 🟢 JavaScriptで「background-image」を直接セットする命令を作成
        if img_b64:
            js_code += f"""
            var btn = window.parent.document.querySelector('button[key="{b_key}"]');
            if (btn) {{
                btn.style.backgroundImage = 'url("{img_b64}")';
                btn.style.backgroundSize = 'cover';
            }}
            """
        
        owner_icon = "🔵" if st.session_state.owner[r,c] == 1 else "🔴" if st.session_state.owner[r,c] == 2 else "⚪"
        cols[c].button(f"{owner_icon}\n🛡️{d}\n💰{e}", key=b_key, on_click=on_click, args=(r,c))

# --- 5. JavaScriptの実行 ---
# StreamlitのコンポーネントとしてJSを流し込む
st.components.v1.html(f"<script>{js_code}</script>", height=0)

st.sidebar.write(f"現在のターン: {'🔵' if st.session_state.turn == 1 else '🔴'}")