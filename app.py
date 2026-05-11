import streamlit as st
import base64
import os

# --- 1. 画像読み込み（48KBならそのままでOK） ---
def get_base64_image(file_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_name)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

# --- 2. 設定 ---
MAP_SIZE = 6
TILE_DEFS = {
    "mountain": {"icon": "⛰️", "file": "mount.png"},
    "field": {"icon": "🌾", "file": "field.png"},
    "forest": {"icon": "🌲", "file": "forest.png"}
}

# --- 3. 最強の強制上書きCSS ---
# ボタンの内部にある「aria-label（ボタンのテキスト）」を直接監視する仕組みです
st.markdown("""
<style>
    /* 全てのボタンの基本設定 */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: #333 !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        position: relative !important;
    }

    /* 文字を浮かび上がらせ、背景より優先する */
    div.stButton p {
        color: white !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px #000 !important;
        z-index: 10 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ 6x6 World Tactical Map")

# 画像ロード
images = {k: get_base64_image(v['file']) for k, v in TILE_DEFS.items()}

for r in range(MAP_SIZE):
    cols = st.columns(MAP_SIZE)
    for c in range(MAP_SIZE):
        # 地形決定
        t_key = "mountain" if (r + c) % 3 == 0 else "field" if (r + c) % 3 == 1 else "forest"
        conf = TILE_DEFS[t_key]
        img_data = images[t_key]
        
        # 🟢 【解決策】aria-labelを使った属性セレクタ
        # Streamlitのボタンは「表示テキスト」がaria-label属性に入ります。
        # これをCSSセレクタとして使うことで、階層に関係なく100%特定できます。
        label_text = f"btn_{r}_{c}"
        
        if img_data:
            st.markdown(f"""
                <style>
                div.stButton > button[aria-label="{label_text}"] {{
                    background-image: url("{img_data}") !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        # ボタンの表示テキストをCSSで狙い撃ちしやすいユニークなものにする
        cols[c].button(label_text, key=f"key_{r}_{c}")