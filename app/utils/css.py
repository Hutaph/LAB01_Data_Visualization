from pathlib import Path

import streamlit as st

def inject_css(css_path: str = "styles/main.css"):
    css_file = Path(css_path)
    if not css_file.is_absolute():
        app_dir = Path(__file__).resolve().parents[1]
        css_file = app_dir / css_path

    with css_file.open("r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
