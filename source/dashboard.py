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
        div[data-testid="stMetricValue"] { font-size: 1.85rem; }
        .block-container { padding-top: 1.2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Amazon US · Laptop & phụ kiện")
    st.caption(
        "Bộ lọc theo giá, đánh giá và ngành hàng. Biểu đồ tương tác và xuất danh sách đã lọc."
    )

    with st.sidebar:
        st.header("Bộ lọc")
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
        st.caption("Giao diện: menu ⋮ ở góc phải → Settings → Theme.")

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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Tổng quan",
            "Danh sách",
            "Ưu tiên",
            "Khuyến mãi",
            "Thương hiệu",
            "Prime & nhãn",
        ]
    )

    with tab1:
        if len(f) < 2:
            st.warning("Không đủ dữ liệu. Hãy nới bộ lọc ở cột bên trái.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                fig_hist = px.histogram(
                    f.dropna(subset=["price_usd"]),
                    x="price_usd",
                    nbins=40,
                    color_discrete_sequence=["#6366f1"],
                    title="Phân bố giá bán, USD",
                )
                fig_hist.update_layout(
                    bargap=0.05,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col_b:
                sub = f.dropna(subset=["price_usd", "rating", "reviews"])
                if len(sub):
                    fig_sc = px.scatter(
                        sub,
                        x="price_usd",
                        y="rating",
                        size="reviews",
                        color="category",
                        hover_data=["title"],
                        title="Giá bán và số sao · kích thước điểm theo số đánh giá",
                        opacity=0.65,
                    )
                    fig_sc.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        legend_title_text="Ngành hàng",
                    )
                    st.plotly_chart(fig_sc, use_container_width=True)
                else:
                    st.info("Không đủ bản ghi có đủ giá và điểm sao để hiển thị biểu đồ.")

            top_cat = (
                f.groupby("category", dropna=False)
                .size()
                .reset_index(name="n")
                .sort_values("n", ascending=False)
                .head(15)
            )
            fig_bar = px.bar(
                top_cat,
                x="n",
                y="category",
                orientation="h",
                color_discrete_sequence=["#14b8a6"],
                title="15 ngành hàng phổ biến nhất",
            )
            fig_bar.update_layout(
                yaxis={"categoryorder": "total ascending"},
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        show_cols = [
            "title",
            "price_usd",
            "list_price_usd",
            "discount_pct",
            "rating",
            "reviews",
            "category",
            "search_is_prime",
            "search_is_best_seller",
            "link",
        ]
        disp = f[show_cols].copy()
        disp = disp.rename(
            columns={
                "title": "Tên sản phẩm",
                "price_usd": "Giá bán",
                "list_price_usd": "Giá niêm yết",
                "discount_pct": "Chiết khấu",
                "rating": "Số sao",
                "reviews": "Số đánh giá",
                "category": "Ngành hàng",
                "search_is_prime": "Prime",
                "search_is_best_seller": "Best Seller",
                "link": "Liên kết",
            }
        )
        st.dataframe(
            disp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Liên kết": st.column_config.LinkColumn("Liên kết"),
                "Giá bán": st.column_config.NumberColumn(format="$%.2f"),
                "Giá niêm yết": st.column_config.NumberColumn(format="$%.2f"),
                "Chiết khấu": st.column_config.NumberColumn(format="%.0f%%"),
            },
        )
        csv_bytes = f[show_cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Tải CSV",
            data=csv_bytes,
            file_name="amazon_filtered.csv",
            mime="text/csv",
        )

    with tab3:
        st.subheader("Gợi ý theo điểm ưu tiên")
        st.caption(
            "Xếp hạng nội bộ từ số sao, số đánh giá và giá bán. Chỉ dùng để so sánh trong cùng tập dữ liệu đã lọc."
        )
        work = f.dropna(subset=["price_usd", "rating"]).copy()
        work = work[work["price_usd"] > 0]
        if len(work):
            work["_score"] = (
                work["rating"] * np.log1p(work["reviews"].fillna(0)) / np.sqrt(work["price_usd"])
            )
            top = work.nlargest(12, "_score")[
                ["title", "price_usd", "rating", "reviews", "link", "image_url"]
            ]
            for _, row in top.iterrows():
                ic, tx = st.columns([1, 5])
                with ic:
                    if pd.notna(row.get("image_url")) and str(row["image_url"]).startswith("http"):
                        st.image(str(row["image_url"]), width=72)
                    else:
                        st.write("—")
                with tx:
                    st.markdown(f"**{row['title'][:120]}…**" if len(str(row["title"])) > 120 else f"**{row['title']}**")
                    st.markdown(
                        f"${row['price_usd']:.2f} · {row['rating']:.1f} sao · {int(row['reviews'] or 0):,} đánh giá"
                    )
                    st.link_button("Xem trên Amazon", str(row["link"]))
        else:
            st.info("Không có bản ghi đủ giá bán và số sao.")

    with tab4:
        st.subheader("Chiết khấu so với giá niêm yết")
        st.caption(
            "Hiển thị SKU có đủ giá niêm yết và giá bán, với mức chiết khấu từ ngưỡng bạn chọn."
        )
        min_disc = st.slider("Chiết khấu tối thiểu", 5, 80, 15, 5, key="deal_min_disc")
        deals = f[
            f["discount_pct"].notna()
            & (f["discount_pct"] >= min_disc)
            & (f["list_price_usd"].notna())
        ].copy()
        deals = deals.sort_values("discount_pct", ascending=False)
        st.metric("SKU đạt ngưỡng", f"{len(deals):,}")
        if len(deals):
            top_d = deals.head(20)[
                [
                    "title",
                    "price_usd",
                    "list_price_usd",
                    "discount_pct",
                    "savings_usd",
                    "rating",
                    "reviews",
                    "link",
                ]
            ]
            st.dataframe(
                top_d.rename(
                    columns={
                        "price_usd": "Giá",
                        "list_price_usd": "Niêm yết",
                        "discount_pct": "Giảm %",
                        "savings_usd": "Tiết kiệm $",
                        "rating": "Rating",
                        "reviews": "Reviews",
                        "link": "Link",
                    }
                ),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Link": st.column_config.LinkColumn("Link"),
                    "Giá": st.column_config.NumberColumn(format="$%.2f"),
                    "Niêm yết": st.column_config.NumberColumn(format="$%.2f"),
                    "Giảm %": st.column_config.NumberColumn(format="%.0f%%"),
                    "Tiết kiệm $": st.column_config.NumberColumn(format="$%.2f"),
                },
            )
            fig_deal = px.bar(
                deals.head(25).iloc[::-1],
                x="discount_pct",
                y="title",
                orientation="h",
                color="savings_usd",
                color_continuous_scale="Turbo",
                title="Top 25 deal (theo % giảm) — màu = tiết kiệm $",
                hover_data=["price_usd", "list_price_usd", "rating"],
            )
            fig_deal.update_layout(
                yaxis={"title": None, "tickmode": "linear"},
                height=max(420, min(900, 24 * len(deals.head(25)))),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_deal.update_yaxes(tickfont={"size": 9})
            st.plotly_chart(fig_deal, use_container_width=True)
        else:
            st.info("Không có deal nào — hạ ngưỡng % hoặc nới bộ lọc sidebar.")

    with tab5:
        st.subheader("Thương hiệu (suy ra từ brand_info / chữ đầu tiêu đề)")
        top_n = st.slider("Số thương hiệu hiển thị", 5, 40, 15, 1, key="brand_top_n")
        bdf = (
            f.groupby("brand", dropna=False)
            .agg(
                n=("asin", "count"),
                avg_price=("price_usd", "mean"),
                avg_rating=("rating", "mean"),
            )
            .reset_index()
            .query("n >= 1")
            .sort_values("n", ascending=False)
            .head(top_n)
        )
        if len(bdf):
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                fig_bn = px.bar(
                    bdf.sort_values("n"),
                    x="n",
                    y="brand",
                    orientation="h",
                    color_discrete_sequence=["#8b5cf6"],
                    title="Số sản phẩm theo brand",
                )
                fig_bn.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis={"categoryorder": "total ascending"},
                )
                st.plotly_chart(fig_bn, use_container_width=True)
            with c_b2:
                bpr = bdf.dropna(subset=["avg_price"])
                if len(bpr):
                    fig_bp = px.bar(
                        bpr.sort_values("avg_price"),
                        x="avg_price",
                        y="brand",
                        orientation="h",
                        color="avg_rating",
                        color_continuous_scale="RdYlGn",
                        range_color=[3, 5],
                        title="Giá TB (USD) — màu = rating TB",
                    )
                    fig_bp.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        yaxis={"categoryorder": "total ascending"},
                    )
                    st.plotly_chart(fig_bp, use_container_width=True)
            st.dataframe(
                bdf.rename(
                    columns={
                        "brand": "Brand",
                        "n": "Số SP",
                        "avg_price": "Giá TB",
                        "avg_rating": "Rating TB",
                    }
                ),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Giá TB": st.column_config.NumberColumn(format="$%.2f"),
                    "Rating TB": st.column_config.NumberColumn(format="%.2f"),
                },
            )
        else:
            st.info("Không có dữ liệu brand sau lọc.")

    with tab6:
        st.subheader("So sánh Prime & huy hiệu Amazon")
        st.caption("Dựa trên cờ crawl: Prime, Best seller, Amazon's Choice.")
        if len(f) == 0:
            st.warning("Không có dòng sau lọc.")
        else:
            seg = f.assign(
                prime_label=f["search_is_prime"].map({True: "Prime", False: "Không Prime"})
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                fig_box = px.box(
                    seg.dropna(subset=["price_usd"]),
                    x="prime_label",
                    y="price_usd",
                    color="prime_label",
                    points="outliers",
                    title="Phân bố giá: Prime vs không Prime",
                )
                fig_box.update_layout(
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_box, use_container_width=True)
            with col_p2:
                pm = (
                    seg.groupby("prime_label", dropna=False)
                    .agg(avg_rating=("rating", "mean"), n=("asin", "count"))
                    .reset_index()
                )
                fig_pr = px.bar(
                    pm,
                    x="prime_label",
                    y="avg_rating",
                    color="prime_label",
                    text="n",
                    title="Rating trung bình theo nhóm Prime",
                )
                fig_pr.update_traces(texttemplate="n=%{text}", textposition="outside")
                fig_pr.update_layout(
                    showlegend=False,
                    yaxis_range=[0, 5.15],
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_pr, use_container_width=True)

            badge_rows = [
                ("Best seller", int(f["search_is_best_seller"].sum())),
                ("Amazon's Choice", int(f["search_is_amazon_choice"].sum())),
                ("Prime eligible", int(f["search_is_prime"].sum())),
            ]
            badf = pd.DataFrame(badge_rows, columns=["Huy hiệu", "Số sản phẩm"])
            fig_bg = px.bar(
                badf,
                x="Huy hiệu",
                y="Số sản phẩm",
                color="Huy hiệu",
                title="Số lượng sản phẩm có từng huy hiệu (trong tập đã lọc)",
            )
            fig_bg.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bg, use_container_width=True)

            cross = (
                f.groupby(
                    [
                        f["search_is_prime"].map({True: "Prime", False: "Không Prime"}),
                        f["search_is_best_seller"].map({True: "BS", False: "—"}),
                    ],
                    dropna=False,
                )
                .size()
                .reset_index(name="n")
            )
            cross.columns = ["Prime", "Best seller", "n"]
            st.markdown("**Giao Prime × Best seller** (nhanh thấy tỷ lệ chồng lấn)")
            st.dataframe(cross, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
