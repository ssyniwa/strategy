import streamlit as st
import base64
import os

def get_test_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

st.title("Image Test")
img = get_test_img("mount.png") # 同じフォルダにmount.pngがある前提

if img:
    st.write("✅ Pythonは画像を認識しています")
    st.markdown(f"""
        <style>
        div.stButton > button {{
            background-image: url("{img}") !important;
            height: 200px !important;
            width: 200px !important;
            color: white !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    st.button("TEST BUTTON", key="test")
else:
    st.error("❌ mount.png が見つかりません。app.pyと同じフォルダに置いてください。")