"""
Amazon US product analytics dashboard.
Run from project root: streamlit run source/dashboard.py
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Đường dẫn dữ liệu (cùng repo)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "amazon_crawl" / "amazon_products_US_20260321_231510.csv"

USECOLS = [
    "asin",
    "title",
    "current_price",
    "search_price",
    "original_price",
    "search_original_price",
    "search_rating",
    "search_reviews",
    "main_category_name",
    "search_is_prime",
    "search_is_best_seller",
    "search_is_amazon_choice",
    "link",
    "image_url",
    "brand_info",
]


def _infer_brand(brand_info: object, title: object) -> str:
    if pd.notna(brand_info) and str(brand_info).strip():
        s = str(brand_info).strip()
        m = re.match(r"(?i)^visit the (.+?) store$", s)
        if m:
            return m.group(1).strip()
    t = str(title or "").strip()
    if t:
        return t.split()[0][:48]
    return "Khác"


@st.cache_data(show_spinner=False)
def load_products(csv_path: str) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    df = pd.read_csv(path, usecols=USECOLS, low_memory=False)
    price = df["search_price"].combine_first(df["current_price"])
    orig = df["search_original_price"].combine_first(df["original_price"])
    df["price_usd"] = pd.to_numeric(price, errors="coerce")
    df["list_price_usd"] = pd.to_numeric(orig, errors="coerce")
    df["rating"] = pd.to_numeric(df["search_rating"], errors="coerce")
    df["reviews"] = pd.to_numeric(df["search_reviews"], errors="coerce")
    df["category"] = df["main_category_name"].fillna("Không xác định")
    for c in ("search_is_prime", "search_is_best_seller", "search_is_amazon_choice"):
        df[c] = df[c].fillna(False).astype(bool)
    df["discount_pct"] = (
        (df["list_price_usd"] - df["price_usd"]) / df["list_price_usd"] * 100
    ).where(df["list_price_usd"] > 0)
    df["discount_pct"] = df["discount_pct"].clip(lower=0, upper=100)
    df["savings_usd"] = (df["list_price_usd"] - df["price_usd"]).where(
        df["list_price_usd"] > df["price_usd"]
    )
    df["brand"] = [_infer_brand(bi, ti) for bi, ti in zip(df["brand_info"], df["title"])]
    return df


def main() -> None:
    st.set_page_config(
        page_title="Amazon US · Product insights",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        /* --- Layout polish (lightweight, no extra deps) --- */
        .block-container { padding-top: 1.2rem; padding-bottom: 2.25rem; }
        section[data-testid="stSidebar"] > div { padding-top: 1.0rem; }
        div[data-testid="stMetricValue"] { font-size: 1.85rem; }
        div[data-testid="stMetricLabel"] { opacity: 0.8; }
        /* reduce top whitespace before tabs */
        div[data-testid="stTabs"] { margin-top: 0.35rem; }
        /* make plots/tables feel like cards */
        div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {
          border: 1px solid rgba(120,120,120,0.20);
          border-radius: 14px;
          padding: 12px 12px 6px 12px;
          background: rgba(250,250,250,0.35);
        }
        /* nicer caption */
        .stCaption { opacity: 0.85; }
        div[data-testid="stMetricValue"] { font-size: 1.85rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ==============================
    # Header (đẹp mắt + gọn)
    # ==============================
    left, right = st.columns([3.2, 1.1], vertical_alignment="bottom")
    with left:
        st.title("Amazon US · Laptop & phụ kiện")
        st.caption(
            "Bộ lọc theo giá, đánh giá và ngành hàng. Dùng dữ liệu crawl để demo dashboard."
        )
    with right:
        st.caption("Phiên bản: `demo`")

    with st.sidebar:
        st.header("Bộ lọc dữ liệu")
        csv_path = st.text_input("Tệp dữ liệu CSV", value=str(DEFAULT_CSV))
        try:
            df = load_products(csv_path)
        except Exception as e:
            st.error(f"Không thể đọc tệp: {e}")
            st.stop()

        st.success(f"**{len(df):,}** bản ghi đã nạp")

        price_min = float(df["price_usd"].min(skipna=True) or 0)
        price_max = float(df["price_usd"].max(skipna=True) or 1)
        if price_min >= price_max:
            price_max = price_min + 1

        p_low, p_high = st.slider(
            "Giá bán, USD",
            min_value=price_min,
            max_value=price_max,
            value=(price_min, price_max),
        )
        r_low, r_high = st.slider("Số sao trung bình", 0.0, 5.0, (3.0, 5.0), 0.1)
        min_reviews = st.number_input("Số lượng đánh giá tối thiểu", 0, 100_000, 0, 10)

        cats = sorted(df["category"].dropna().unique().tolist())
        sel_cats = st.multiselect("Ngành hàng", options=cats, default=[])

        only_prime = st.toggle("Chỉ sản phẩm Prime", value=False)
        only_bestseller = st.toggle("Chỉ Best Seller", value=False)

        st.divider()
        st.caption("Gợi ý: menu ⋮ (góc phải) → Settings → Theme.")

    q = st.text_input("Tìm theo tên sản phẩm", placeholder="Ví dụ: MacBook, HP, sleeve")

    f = df.copy()
    f = f[f["price_usd"].between(p_low, p_high, inclusive="both")]
    f = f[f["rating"].between(r_low, r_high, inclusive="both")]
    f = f[f["reviews"].fillna(0) >= min_reviews]
    if sel_cats:
        f = f[f["category"].isin(sel_cats)]
    if only_prime:
        f = f[f["search_is_prime"]]
    if only_bestseller:
        f = f[f["search_is_best_seller"]]
    if q.strip():
        f = f[f["title"].astype(str).str.contains(q.strip(), case=False, na=False)]

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("SKU sau lọc", f"{len(f):,}")
    with c2:
        st.metric(
            "Giá bán trung bình",
            f"${f['price_usd'].mean():,.0f}" if len(f) else "—",
        )
    with c3:
        st.metric(
            "Điểm đánh giá TB",
            f"{f['rating'].mean():.2f}" if len(f) and f["rating"].notna().any() else "—",
        )
    with c4:
        st.metric(
            "Đủ điều kiện Prime",
            f"{int(f['search_is_prime'].sum()):,}" if len(f) else "—",
        )
    with c5:
        avg_disc = f["discount_pct"].mean()
        st.metric(
            "Chiết khấu so niêm yết TB",
            f"{avg_disc:.0f}%" if len(f) and pd.notna(avg_disc) else "—",
        )

    # ==============================
    # Tabs (TEAM TODO)
    # ==============================
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Tab 1", "Tab 2", "Tab 3", "Tab 4", "Tab 5"]
    )

    with tab1:
        # TEAM: Dán code Tab 1 tại đây
        # - Ví dụ: biểu đồ tổng quan, KPI cards, phân bố giá
        st.info("Tab 1 đang để trống.")

    with tab2:
        # TEAM: Dán code Tab 2 tại đây
        # - Ví dụ: bảng dữ liệu + export, drill-down theo SKU
        st.info("Tab 2 đang để trống.")

    with tab3:
        # TEAM: Dán code Tab 3 tại đây
        # - Ví dụ: ranking / gợi ý sản phẩm / scoring
        st.info("Tab 3 đang để trống.")

    with tab4:
        # TEAM: Dán code Tab 4 tại đây
        # - Ví dụ: phân tích khuyến mãi / chiết khấu / price ladder
        st.info("Tab 4 đang để trống.")

    with tab5:
        # TEAM: Dán code Tab 5 tại đây
        # - Ví dụ: brand / Prime / badge analysis
        st.info("Tab 5 đang để trống.")


if __name__ == "__main__":
    main()
