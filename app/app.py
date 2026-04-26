import sys 
import os
from pathlib import Path
import streamlit as st
import joblib

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)


dump_path = Path(__file__).resolve().parent / "features_dump.json"
models_dir = Path(__file__).resolve().parent / "services" / "models"
best_model = models_dir / "gradient_boosting_model.pkl"

dump = []
if best_model.exists():
    try:
        m = joblib.load(best_model)
        dump = list(m.feature_names_in_) if hasattr(m, "feature_names_in_") else list(getattr(m, "feature_names_", []))
    except Exception as e:
        # keep dump as empty list; print warning to stdout for debugging
        print("Warning: failed to load model for features dump:", e)

from components.header import render_header
from components.navigation import render_navigation
from services.data_loader import COLOR_SEQUENCE, load_data
from tabs.market_overview import render as render_overview
from tabs.trust_signals import render as render_trust_signals
from tabs.price_strategy import render as render_price_strategy
from tabs.brand_power import render as render_brand_power
from tabs.deal_impact import render as render_deal_impact
from tabs.sales_forecast import render as render_sales_forecast
from tabs.listing_quality import render as render_listing_quality
from utils.css import inject_css

amazon_icon_path = Path(__file__).resolve().parent / "data" / "Amazon_icon.png"

st.set_page_config(
    layout="wide",
    page_title="Phân tích Dữ liệu Thương mại Điện tử Amazon",
    page_icon=str(amazon_icon_path) if amazon_icon_path.exists() else "🛒",
    initial_sidebar_state="collapsed",
)

inject_css("styles/main.css")

if "_layout_rerun_done" not in st.session_state:
    st.session_state["_layout_rerun_done"] = True
    st.rerun()

@st.cache_data(show_spinner=False)
def _build_metrics(df):
    category_col = "crawl_category" if "crawl_category" in df.columns else "category"
    total_products = int(df["asin"].nunique()) if "asin" in df.columns else int(len(df))
    total_records = int(len(df))
    total_categories = (
        int(df[category_col].nunique()) if category_col in df.columns else 0
    )
    best_seller_pct = (
        float(df["is_best_seller"].mean() * 100)
        if "is_best_seller" in df.columns and len(df)
        else 0.0
    )
    return {
        "total_products": total_products,
        "total_records": total_records,
        "total_categories": total_categories,
        "best_seller_pct": best_seller_pct,
        "category_col": category_col,
    }

TAB_RENDERERS = {
    "Tổng quan Thị trường": lambda state, df: render_overview(state),
    "Chiến lược Giá cả":   lambda state, df: render_price_strategy(df),
    "Chỉ số Tín nhiệm":    lambda state, df: render_trust_signals(df),
    "Chiến lược Ưu đãi": lambda state, df: render_deal_impact(df),
    "Chất lượng Niêm yết": lambda state, df: render_listing_quality(df),
    "Vị thế Thương hiệu":  lambda state, df: render_brand_power(df),
    "Dự báo Kinh doanh":   lambda state, df: render_sales_forecast(df),
}

def route_tab(active_tab: str, state: dict, df):
    """Render the content for the currently selected tab."""
    renderer = TAB_RENDERERS.get(active_tab)
    if renderer:
        renderer(state, df)
    else:
        st.warning(f"Tab '{active_tab}' không tồn tại.")

with st.spinner("Đang tải dữ liệu Amazon..."):
    DF, META = load_data()

METRICS = _build_metrics(DF)
STATE = {"df": DF, "meta": META, "metrics": METRICS, "color_sequence": COLOR_SEQUENCE}

_, col_header = st.columns([1, 15], gap="small")
with col_header:
    render_header(STATE)

col_nav, col_content = st.columns([1, 15], gap="small")

with col_nav:
    render_navigation()

with col_content:
    active_tab = st.session_state.get("active_tab", "Tổng quan Thị trường")
    route_tab(active_tab, STATE, DF)
