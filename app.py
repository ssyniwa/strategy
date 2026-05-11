import streamlit as st
import base64
import os

# --- 1. 画像読み込み ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

# --- 2. CSS：ボタンを「完全に透明」にする ---
# 画像はHTML側で表示するので、ボタンは「当たり判定」だけ残して消します
st.markdown("""
<style>
    /* ボタンの親要素を画像コンテナにする */
    .tile-container {
        position: relative;
        width: 100%;
        height: 80px;
        margin-bottom: 10px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.4);
    }
    
    /* ボタン本体を透明にして、タイルの上に被せる */
    .tile-container div.stButton > button {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        color: transparent !important; /* ボタンの文字も見えなくする */
        z-index: 10;
    }
    
    /* ホバー時に少し明るくして「押せる感」を出す */
    .tile-container div.stButton > button:hover {
        background-color: rgba(255,255,255,0.1) !important;
    }

    /* 背景画像と文字のレイヤー */
    .tile-bg {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1;
    }
    .tile-label {
        color: white;
        font-weight: bold;
        text-shadow: 2px 2px 4px black;
        z-index: 2;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. マップ描画 ---
st.title("⚔️ Tactical Map: Functional Edition")

images = {
    "mountain": get_base64_image("mount.png"),
    "field": get_base64_image("field.png"),
    "forest": get_base64_image("forest.png")
}

def handle_click(r, c):
    st.toast(f"座標 ({r}, {c}) がクリックされました！")

for r in range(6):
    cols = st.columns(6)
    for c in range(6):
        t_key = "mountain" if (r+c) % 3 == 0 else "field" if (r+c) % 3 == 1 else "forest"
        img = images[t_key]
        
        # コンテナの中に「背景」と「透明ボタン」を同居させる
        with cols[c]:
            st.markdown(f"""
                <div class="tile-container">
                    <div class="tile-bg" style="background-image: url('{img}');">
                        <span class="tile-label">{"⛰️" if t_key=="mountain" else "🌾" if t_key=="field" else "🌲"}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # この透明ボタンがクリックを検知する
            st.button("", key=f"btn_{r}_{c}", on_click=handle_click, args=(r, c))