import streamlit as st
from pathlib import Path
import base64

def _load_logo_base64() -> str | None:
    logo_path = Path(__file__).resolve().parents[1] / "data" / "Amazon_icon.png"
    if not logo_path.exists():
        return None
    try:
        return base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    except Exception:
        return None

def render_header(state):
    meta = state.get("meta", {})
    source_name = Path(meta.get("path", "data/Processed/data_tmp.csv")).name
    updated_at = meta.get("file_time", "Không rõ")
    logo_b64 = _load_logo_base64()

    if logo_b64:
        logo_html = (
            '<img class="az-header-logo-img" src="data:image/png;base64,'
            f'{logo_b64}" alt="Amazon logo" />'
        )
    else:
        logo_html = '<div class="az-header-logo-fallback">🛒</div>'

    st.markdown(
        f"""
        <div class="az-header">
            <div class="az-header-logo-wrap">{logo_html}</div>
            <div class="az-header-left">
                <div class="az-title-line">Phân tích Dữ liệu Thương mại Điện tử Amazon</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
