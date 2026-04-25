"""
Navigation component — Hover sidebar.

Sidebar thu gọn (chỉ icon) → mở rộng khi hover chuột.
Click handling: hidden st.button được trigger bằng JavaScript.
"""

import streamlit as st
import streamlit.components.v1 as components

TAB_CONFIG = [
    {"label": "Tổng quan",     "icon": "bi-house-fill"},
    {"label": "Danh mục",      "icon": "bi-box-fill"},
    {"label": "Định giá",      "icon": "bi-tag-fill"},
    {"label": "Đánh giá",      "icon": "bi-star-fill"},
    {"label": "Vận chuyển",    "icon": "bi-truck-front-fill"},
    {"label": "Độ hoàn thiện", "icon": "bi-ui-checks-grid"},
    {"label": "Nhãn & Uy tín", "icon": "bi-patch-check-fill"},
    {"label": "Nổi bật",       "icon": "bi-bar-chart-fill", "icon_style": "font-size: 24px;"},
    {"label": "Dự báo",        "icon": "bi-cpu-fill"},
]

TAB_LABELS = [t["label"] for t in TAB_CONFIG]
_BTN_PREFIX = "nav_btn_"

def render_navigation() -> str:
    """Render the hover sidebar and return the active tab label."""

    if "active_tab" not in st.session_state:
        st.session_state.active_tab = TAB_LABELS[0]

    active = st.session_state.active_tab

    items_html = ""
    for cfg in TAB_CONFIG:
        label = cfg["label"]
        icon  = cfg["icon"]
        icon_style = f' style="{cfg["icon_style"]}"' if "icon_style" in cfg else ""
        is_active = "active" if label == active else ""
        items_html += f"""
        <div class="nav-item {is_active}" title="{label}"
             onclick="triggerBtn('{_BTN_PREFIX}{label}')">
          <i class="bi {icon} nav-icon"{icon_style}></i>
          <span class="nav-text">{label}</span>
        </div>"""

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Montserrat:wght@700;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; overflow: hidden; }}

  .hover-sidebar {{
    width: 62px;
    background: linear-gradient(180deg, #fff9f0 0%, #fff3e0 100%);
    border: 1px solid rgba(255,153,0,0.30);
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(228,121,17,0.12);
    padding: 14px 6px;
    transition: width 0.32s cubic-bezier(0.25,0.46,0.45,0.94),
                box-shadow 0.32s ease;
    overflow: hidden;
    white-space: nowrap;
    position: relative;
    z-index: 9999;
    height: 100%;
  }}

  .hover-sidebar:hover {{
    width: 220px;
    box-shadow: 8px 0 36px rgba(228,121,17,0.22), 0 4px 20px rgba(228,121,17,0.12);
  }}

  .sidebar-title {{
    display: flex;
    align-items: center;
    padding: 4px 3px 12px 3px; 
    border-bottom: 2px solid rgba(255,153,0,0.25);
    margin-bottom: 10px;
    overflow: hidden;
  }}
  .sidebar-title .title-icon {{
    font-size: 22px;
    color: #E47911;
    flex-shrink: 0;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .sidebar-title .title-text {{
    font-family: 'Montserrat', sans-serif;
    font-size: 0.80rem;
    font-weight: 800;
    color: #5f3710;
    letter-spacing: 0.3px;
    opacity: 0;
    transition: opacity 0.22s ease 0.08s, margin-left 0.22s ease;
    white-space: nowrap;
    overflow: hidden;
    margin-left: 0px;
  }}
  .hover-sidebar:hover .title-text {{
    opacity: 1;
    margin-left: 12px;
  }}

  .nav-item {{
    display: flex;
    align-items: center;
    padding: 0 3px; 
    border-radius: 8px;
    cursor: pointer;
    margin: 2px 0;
    transition: background 0.2s ease, padding 0.28s ease;
    border-left: 3px solid transparent;
    overflow: hidden;
  }}
  .nav-item:hover {{
    background: #FEF3C7;
  }}
  .nav-item.active {{
    background: #F97316;
    border-left: none;
    box-shadow: 0 4px 14px rgba(245,158,11,0.35);
  }}

  .nav-icon {{
    font-size: 22px;
    flex-shrink: 0;
    color: #9A3412;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s ease;
  }}
  .nav-item.active .nav-icon {{
    color: #ffffff;
  }}

  .nav-text {{
    font-family: 'Manrope', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    color: #9A3412;
    opacity: 0;
    max-width: 0;
    overflow: hidden;
    transition: opacity 0.22s ease 0.06s, max-width 0.28s ease, margin-left 0.28s ease;
    white-space: nowrap;
    margin-left: 0px;
  }}
  .nav-item.active .nav-text {{
    color: #ffffff;
  }}
  .hover-sidebar:hover .nav-text {{
    opacity: 1;
    max-width: 160px;
    margin-left: 12px;
  }}
</style>
</head>
<body>
<div class="hover-sidebar">
  <div class="sidebar-title">
    <i class="bi bi-grid-3x3-gap-fill title-icon"></i>
    <span class="title-text">Bảng Điều Khiển</span>
  </div>
  {items_html}
</div>
<script>
function triggerBtn(btnKey) {{
  // Walk up to parent Streamlit document and find the hidden button
  const parentDoc = window.parent.document;
  const buttons = parentDoc.querySelectorAll('[data-testid="stButton"] button');
  for (const btn of buttons) {{
    if (btn.getAttribute('aria-label') === btnKey ||
        btn.innerText.trim() === btnKey) {{
      btn.click();
      return;
    }}
  }}
  // Fallback: try matching by key attribute pattern
  const allBtns = parentDoc.querySelectorAll('button');
  for (const btn of allBtns) {{
    if (btn.innerText.trim() === btnKey.replace('{_BTN_PREFIX}', '')) {{
      btn.click();
      return;
    }}
  }}
}}
</script>
</body>
</html>
"""

    components.html(html_code, height=520, scrolling=False)

    for cfg in TAB_CONFIG:
        label = cfg["label"]
        btn_key = f"{_BTN_PREFIX}{label}"
        if st.button(label, key=btn_key, help=label):
            st.session_state.active_tab = label
            st.rerun()

    return st.session_state.active_tab
