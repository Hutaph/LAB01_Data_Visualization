"""
`tab_du_bao` - Streamlit tab for product performance forecasting.
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import plotly.graph_objects as go
import sys

from predictor.feature_engineering import DiscountFeatureEngineer, OutlierClipper
from predictor import MODELS_DIR


# ── CSS ─────────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* block container — DO NOT override padding-top; main.css handles it */

/* form reset */
[data-testid="stForm"] { border:none!important; padding:0!important; background:transparent!important; }

/* ── tab title row ── */
.fc-title-row {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 10px;
    border-bottom: 2px solid rgba(249,115,22,.12);
    margin-bottom: 14px;
}
.fc-title {
    font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 800;
    background: linear-gradient(90deg, #9A3412, #F97316);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -.4px;
}
.fc-sub  { font-size: 12px; color: #a8a29e; font-weight: 500; margin-left: 10px; }
.fc-badge {
    font-size: 11px; font-weight: 700; white-space: nowrap;
    background: #fff7ed; color: #c2410c;
    border: 1px solid #fed7aa; border-radius: 20px; padding: 4px 13px;
}

/* ── model selector label override ── */
.fc-model-label {
    font-size: 10px; font-weight: 700; color: #78716c;
    text-transform: uppercase; letter-spacing: .6px;
    margin-bottom: 4px;
}

/* ── model selectbox label ── */
div[data-testid="stSelectbox"] > label {
    font-size: 11px !important; font-weight: 700 !important;
    color: #78716c !important; text-transform: uppercase !important;
    letter-spacing: .6px !important;
}

/* ── form widget labels (no uppercase) ── */
[data-testid="stForm"] label {
    font-size: 11.5px !important; font-weight: 600 !important;
    color: #44403c !important; text-transform: none !important;
    letter-spacing: 0 !important;
}

/* ── section heading inside form ── */
.sec { font-size: 10px; font-weight: 700; color: #F97316;
    text-transform: uppercase; letter-spacing: .8px;
    margin: 14px 0 7px; padding-bottom: 5px;
    border-bottom: 1px solid rgba(249,115,22,.15); }
.sec.first { margin-top: 0; }

/* ── submit button ── */
[data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] .stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg,#F97316,#EA580C) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; padding: 11px 0 !important;
    font-size: 13px !important; font-weight: 700 !important;
    margin-top: 12px !important; letter-spacing: .3px !important;
    box-shadow: 0 2px 8px rgba(249,115,22,.35) !important;
    transition: all .2s !important; cursor: pointer !important;
}
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stForm"] .stButton > button:hover {
    background: linear-gradient(135deg,#EA580C,#C2410C) !important;
    box-shadow: 0 4px 14px rgba(249,115,22,.45) !important;
    transform: translateY(-1px) !important;
}

/* ── metric card ── */
.mc {
    background: linear-gradient(135deg,#fff7ed,#ffffff);
    border: 1px solid #fed7aa; border-left: 5px solid #F97316;
    border-radius: 14px; padding: 20px 22px; margin-bottom: 12px;
}
.mc-lbl { font-size: 10.5px; font-weight: 700; color: #a8a29e;
    text-transform: uppercase; letter-spacing: .6px; margin-bottom: 8px; }
.mc-val { font-family: 'Inter',sans-serif; font-size: 44px; font-weight: 800;
    color: #1c1917; line-height: 1; letter-spacing: -1.5px; }
.mc-unit { font-size: 16px; font-weight: 500; color: #a8a29e; margin-left: 6px; }
.mc-badge { display:inline-flex; align-items:center; margin-top:12px;
    font-size:12px; font-weight:700; padding:5px 14px; border-radius:20px; gap:5px; }
.b-hi { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.b-md { background:#fef9c3; color:#92400e; border:1px solid #fde68a; }
.b-lo { background:#fee2e2; color:#b91c1c; border:1px solid #fecaca; }

/* ── KPI strip ── */
.kpi-row { display:flex; gap:10px; margin-bottom:12px; }
.kpi { flex:1; background:#f9fafb; border:1px solid #e5e7eb;
    border-radius:10px; padding:10px 12px; text-align:center; }
.kpi-l { font-size:10px; font-weight:700; color:#9ca3af;
    text-transform:uppercase; letter-spacing:.5px; margin-bottom:4px; }
.kpi-v { font-size:18px; font-weight:800; color:#111827; }

/* ── chip row ── */
.chips { display:flex; flex-wrap:wrap; gap:7px; margin-bottom:12px; }
.chip { display:inline-flex; align-items:center; gap:5px;
    background:#f9fafb; border:1px solid #e5e7eb;
    border-radius:8px; padding:5px 10px;
    font-size:11px; font-weight:600; color:#6b7280; }
.chip b { color:#111827; }

/* ── placeholder ── */
.ph {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    height:360px;
    background: repeating-linear-gradient(-45deg,#fafafa,#fafafa 8px,#f3f4f6 8px,#f3f4f6 16px);
    border:1px dashed #d1d5db; border-radius:14px;
    color:#9ca3af; font-size:13px; line-height:1.8; text-align:center; padding:24px;
}
.ph .ico { font-size:38px; margin-bottom:10px; }
.ph b { color:#6b7280; }
</style>
"""


def render(df):
    PIPELINE_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "sales_prediction_pipeline.joblib"

    # ── Discover models ────────────────────────────────────────────────────
    try:
        model_options = [p.name for p in sorted(MODELS_DIR.glob("*.pkl"))
                         if p.name != "feature_names.pkl"]
    except Exception:
        model_options = []

    if not model_options:
        st.error("Không tìm thấy mô hình (.pkl) trong thư mục models.")
        return

    default_name  = "gradient_boosting_model.pkl"
    default_index = model_options.index(default_name) if default_name in model_options else 0

    # ── CSS ────────────────────────────────────────────────────────────────
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Title row ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="fc-title-row">'
        '  <div style="display:flex;align-items:baseline;">'
        '    <span class="fc-title">Dự Báo Hiệu Suất Sản Phẩm</span>'
        '    <span class="fc-sub">Advanced ML Predictive Model</span>'
        '  </div>'
        '  <span class="fc-badge">🤖 AI Forecast Engine</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Model selector (right-aligned, above result column) ───────────────
    _, modcol = st.columns([5, 7])
    with modcol:
        mcol_left, mcol_right = st.columns([2, 5])
        with mcol_right:
            selected_model_name = st.selectbox(
                "Mô hình AI",
                options=model_options,
                index=default_index,
                key="model_selector",
                format_func=lambda s: s.replace("_", " ").replace(".pkl", "").title(),
            )

    # ── Load artifacts ─────────────────────────────────────────────────────
    try:
        for _m in ("main", "__main__"):
            mod = sys.modules.get(_m)
            if mod is not None:
                for _cls in (DiscountFeatureEngineer, OutlierClipper):
                    if not hasattr(mod, _cls.__name__):
                        setattr(mod, _cls.__name__, _cls)

        if not PIPELINE_PATH.exists():
            st.error(f"Không tìm thấy pipeline: {PIPELINE_PATH}")
            return

        processor = joblib.load(PIPELINE_PATH)
        model     = joblib.load(MODELS_DIR / selected_model_name)

        # category options from OHE
        try:
            cat_transformer = processor.named_steps["preprocessor"].named_transformers_["cat_path"]
            ohe = cat_transformer.named_steps["onehot"]
            cat_options = sorted(ohe.categories_[0].tolist())
        except Exception:
            cat_options = ["electronics", "home", "fashion"]

        # feature names for importance chart
        try:
            raw_feat_names = list(processor.named_steps["preprocessor"].get_feature_names_out())
            display_feat   = [c.split("__")[-1] for c in raw_feat_names]
        except Exception:
            raw_feat_names, display_feat = [], []

    except Exception as e:
        st.error(f"Lỗi load model: {e}")
        return

    # ══════════════════════════════════════════════════════════════════════
    # Layout: form (left 5) | result (right 7)
    # ══════════════════════════════════════════════════════════════════════
    col_form, col_res = st.columns([5, 7], gap="large")

    # ── LEFT: form ─────────────────────────────────────────────────────────
    with col_form:
        with st.form("predict_form", clear_on_submit=False):

            st.markdown('<div class="sec first">① Giá &amp; Cạnh Tranh</div>', unsafe_allow_html=True)
            ca, cb = st.columns(2)
            with ca:
                f_price      = st.number_input("Giá hiện tại ($)",        value=25.0,  format="%.2f", step=0.5)
            with cb:
                f_orig_price = st.number_input("Giá gốc ($)",             value=30.0,  format="%.2f", step=0.5)
            cc, cd = st.columns(2)
            with cc:
                f_lowest     = st.number_input("Giá chào thấp nhất ($)",  value=20.0,  format="%.2f", step=0.5)
            with cd:
                f_ship       = st.number_input("Phí vận chuyển ($)",      value=0.0,   format="%.2f", step=0.5)
            f_offers = st.number_input("Số nhà bán cạnh tranh", value=1, min_value=0, step=1)

            st.markdown('<div class="sec">② Đánh Giá</div>', unsafe_allow_html=True)
            f_rating  = st.slider("Điểm đánh giá (0–5)", 0.0, 5.0, 4.2, step=0.1)
            f_reviews = st.number_input("Số lượt đánh giá",     value=100, min_value=0, step=1)

            st.markdown('<div class="sec">③ Danh Mục &amp; Đặc Tính</div>', unsafe_allow_html=True)
            f_cat = st.selectbox("Danh mục sản phẩm", cat_options,
                                 format_func=lambda s: s.replace("_", " ").title())
            ce, cf = st.columns(2)
            with ce:
                f_prime  = st.checkbox("Prime",             value=True)
                f_choice = st.checkbox("Amazon's Choice",   value=False)
            with cf:
                f_climate = st.checkbox("Climate Friendly", value=False)
                f_vars    = st.checkbox("Có biến thể",      value=True)

            submitted = st.form_submit_button("🔮  Dự Đoán Doanh Số", use_container_width=True)

    # ── RIGHT: result ──────────────────────────────────────────────────────
    with col_res:
        if not submitted:
            st.markdown(
                '<div class="ph"><div class="ico">🎯</div>'
                'Nhập thông số sản phẩm ở cột bên trái<br>'
                'rồi nhấn <b>Dự Đoán Doanh Số</b> để xem kết quả.</div>',
                unsafe_allow_html=True,
            )
        else:
            try:
                f_discount      = f_orig_price - f_price
                f_discount_rate = (f_discount / f_orig_price) if f_orig_price > 0 else 0.0

                raw_input = pd.DataFrame([{
                    "price":               f_price,
                    "original_price":      f_orig_price,
                    "reviews":             f_reviews,
                    "number_of_offers":    f_offers,
                    "delivery_fee":        f_ship,
                    "discount":            f_discount,
                    "lowest_offer_price":  f_lowest,
                    "rating":              f_rating,
                    "discount_rate":       f_discount_rate,
                    "crawl_category":      f_cat,
                    "is_prime":            int(f_prime),
                    "is_amazon_choice":    int(f_choice),
                    "is_climate_friendly": int(f_climate),
                    "has_variations":      int(f_vars),
                }])

                X_arr    = processor.transform(raw_input)
                X_final  = pd.DataFrame(X_arr, columns=[str(i) for i in range(X_arr.shape[1])])
                raw_pred = model.predict(X_final)[0]
                final_val = int(max(0, round(np.expm1(raw_pred))))

                if final_val > 200:
                    badge_txt, badge_cls = "🚀 Tiềm năng cao", "b-hi"
                elif final_val > 50:
                    badge_txt, badge_cls = "⚖️ Ổn định",       "b-md"
                else:
                    badge_txt, badge_cls = "⚠️ Cần tối ưu",    "b-lo"

                # Metric card
                st.markdown(
                    f'<div class="mc">'
                    f'  <div class="mc-lbl">Dự đoán doanh số / tháng</div>'
                    f'  <div class="mc-val">{final_val:,}<span class="mc-unit">đơn</span></div>'
                    f'  <span class="mc-badge {badge_cls}">{badge_txt}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # KPI strip
                st.markdown(
                    f'<div class="kpi-row">'
                    f'<div class="kpi"><div class="kpi-l">Discount</div>'
                    f'<div class="kpi-v">{f_discount_rate*100:.1f}%</div></div>'
                    f'<div class="kpi"><div class="kpi-l">Rating</div>'
                    f'<div class="kpi-v">⭐ {f_rating:.1f}</div></div>'
                    f'<div class="kpi"><div class="kpi-l">Reviews</div>'
                    f'<div class="kpi-v">{f_reviews:,}</div></div>'
                    f'<div class="kpi"><div class="kpi-l">Đối thủ</div>'
                    f'<div class="kpi-v">{f_offers}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Chips
                model_lbl = selected_model_name.replace("_"," ").replace(".pkl","").title()
                cat_lbl   = f_cat.replace("_"," ").title()
                extras    = "".join(
                    f'<span class="chip">{t}</span>'
                    for t in (["🏆 Choice"] if f_choice else [])
                           + (["🌿 Climate"] if f_climate else [])
                           + (["🎨 Biến thể"] if f_vars else [])
                )
                st.markdown(
                    f'<div class="chips">'
                    f'<span class="chip">📦 <b>{cat_lbl}</b></span>'
                    f'<span class="chip">{"✅" if f_prime else "❌"} Prime</span>'
                    f'<span class="chip">🤖 <b>{model_lbl}</b></span>'
                    f'{extras}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Feature importance chart
                if hasattr(model, "feature_importances_"):
                    names = display_feat if display_feat else [f"F{i}" for i in range(len(model.feature_importances_))]
                    feat_df = (
                        pd.DataFrame({"Feature": names, "Importance": model.feature_importances_})
                        .sort_values("Importance", ascending=True)
                        .tail(10)
                    )
                    n = len(feat_df)
                    colors = [f"rgba(249,115,22,{0.4 + 0.06*i})" for i in range(n)]
                    fig = go.Figure(go.Bar(
                        x=feat_df["Importance"], y=feat_df["Feature"],
                        orientation="h",
                        marker=dict(color=colors, line=dict(width=0)),
                        text=[f"{v:.3f}" for v in feat_df["Importance"]],
                        textposition="outside",
                        textfont=dict(size=10, color="#6b7280"),
                    ))
                    fig.update_layout(
                        title=dict(text="Top 10 Features ảnh hưởng đến dự báo",
                                   font=dict(size=12, color="#44403c"), x=0),
                        yaxis=dict(tickfont=dict(size=10, color="#44403c"), gridcolor="rgba(0,0,0,0)"),
                        xaxis=dict(tickfont=dict(size=10),
                                   title=dict(text="Importance", font=dict(size=11)),
                                   gridcolor="rgba(0,0,0,.04)", zeroline=False),
                        margin=dict(l=10, r=55, t=36, b=10),
                        height=285,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Lỗi dự báo: {e}")

    # ── Technical expander ─────────────────────────────────────────────────
    with st.expander("⚙️ Thông tin kỹ thuật"):
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Loại mô hình:**", type(model).__name__)
            st.write("**Pipeline:**", PIPELINE_PATH.name)
        with c2:
            st.write("**Số features:**", len(raw_feat_names) if raw_feat_names else "N/A")
            st.write("**Cat options:**", ", ".join(cat_options))