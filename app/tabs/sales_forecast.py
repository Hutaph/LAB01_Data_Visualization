import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import plotly.graph_objects as go
import sys

from predictor.feature_engineering import DiscountFeatureEngineer, OutlierClipper
from predictor import MODELS_DIR

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --pr: #F97316;
    --dk: #9A3412;
    --bg: #FEF3E2;
    --card: #FFFFFF;
    --t1: #1C1917;
    --t2: #78716C;
    --t3: #A8A29E;
    --bd: #E7E5E4;
    --r: 8px;
    --fn: 'Inter', sans-serif;
}

* { font-family: var(--fn) !important; }

.main-box { background: var(--bg); min-height: 100vh; }

.fb {
    display: flex; align-items: flex-end; gap: 24px;
    background: #fff; border: 1px solid var(--bd); border-radius: 10px;
    padding: 12px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.06); flex-shrink: 0; flex-wrap: wrap;
    margin-bottom: 14px; width: 100%;
    margin-top: 14px;
}
.fb-item { display: flex; flex-direction: column; gap: 6px; }
.fb-item label {
    display: block; font-size: 11px; font-weight: 700; color: var(--t2);
    text-transform: uppercase; letter-spacing: .5px; margin: 0;
}

div[data-testid="stSelectbox"] label, 
div[data-testid="stNumberInput"] label,
div[data-testid="stSlider"] label,
div[data-testid="stCheckbox"] label p {
    font-size: 10.5px !important; font-weight: 700 !important;
    color: var(--t2) !important; text-transform: uppercase !important;
    letter-spacing: .4px !important;
    margin-bottom: 6px !important;
    line-height: 1.4 !important;
}

[data-testid="stForm"] {
    background: #fff !important;
    border: 1px solid var(--bd) !important;
    border-radius: 12px !important;
    padding: 24px 28px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.04) !important;
}

.sec {
    font-size: 10.5px; font-weight: 800; color: var(--dk);
    text-transform: uppercase; letter-spacing: 0.8px;
    margin: 24px 0 10px; padding-bottom: 0;
    border: none !important;
}
.sec.first { margin-top: 0; }

.mc {
    background: var(--card);
    border: 1px solid var(--bd); border-left: 5px solid var(--pr);
    border-radius: 10px; padding: 22px; margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.mc-lbl { font-size: 10px; font-weight: 700; color: var(--t2);
    text-transform: uppercase; letter-spacing: .6px; margin-bottom: 8px; }
.mc-val { font-size: 40px; font-weight: 800;
    color: var(--t1); line-height: 1; letter-spacing: -1px; }
.mc-unit { font-size: 14px; font-weight: 500; color: var(--t3); margin-left: 4px; }

.kpi-row { display:flex; gap:10px; margin-bottom:14px; }
.kpi { flex:1; background:#fff; border: 1px solid var(--bd);
    border-radius:8px; padding:10px; text-align:center; }
.kpi-l { font-size:9px; font-weight:700; color:var(--t3);
    text-transform: uppercase; letter-spacing:.5px; margin-bottom:4px; }
.kpi-v { font-size:16px; font-weight:800; color:var(--t1); }

.ph {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    height:380px; background: #fff;
    border: 2px dashed #f0f0f0; border-radius: 12px;
    color: var(--t2); text-align: center; padding: 24px;
}
.ph .ico { font-size:44px; margin-bottom:12px; filter: grayscale(0.5); }
.ph b { color: var(--t1); font-weight: 700; }

div.stButton > button {
    background: linear-gradient(135deg, var(--pr), #EA580C) !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 0.7rem 1rem !important;
    width: 100% !important;
    box-shadow: 0 4px 10px rgba(249,115,22,0.2) !important;
    transition: all 0.2s !important;
}
div.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 15px rgba(249,115,22,0.3) !important;
}
</style>
"""

def render(df):
    PIPELINE_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "sales_prediction_pipeline.joblib"

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

    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="fb">'
        '  <div style="display:flex; flex-direction:column; align-items:flex-start; justify-content:center;">'
        '    <div style="font-size:16px; font-weight:800; color:var(--dk);">DỰ BÁO HIỆU SUẤT SẢN PHẨM</div>'
        '    <div style="font-size:11px; color:var(--t2); font-weight:500;">Sử dụng Machine Learning để tối ưu doanh số</div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('<div style="margin-bottom:20px;"></div>', unsafe_allow_html=True)

    col_form, col_res = st.columns([5, 7], gap="large")

    with col_form:
        st.markdown('<div class="sec first" style="margin-bottom:12px;">CẤU HÌNH MÔ HÌNH AI</div>', unsafe_allow_html=True)
        selected_model_name = st.selectbox(
            "Mô hình dự báo",
            options=model_options,
            index=default_index,
            key="model_selector",
            format_func=lambda s: s.replace("_", " ").replace(".pkl", "").title(),
            label_visibility="collapsed"
        )
        st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)

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

        try:
            cat_transformer = processor.named_steps["preprocessor"].named_transformers_["cat_path"]
            ohe = cat_transformer.named_steps["onehot"]
            cat_options = sorted(ohe.categories_[0].tolist())
        except Exception:
            cat_options = ["electronics", "home", "fashion"]

        try:
            raw_feat_names = list(processor.named_steps["preprocessor"].get_feature_names_out())
            display_feat   = [c.split("__")[-1] for c in raw_feat_names]
        except Exception:
            raw_feat_names, display_feat = [], []

    except Exception as e:
        st.error(f"Lỗi load model: {e}")
        return

    with col_form:
        with st.form("predict_form", clear_on_submit=False):

            st.markdown('<div class="sec first">CHIẾN LƯỢC GIÁ & CẠNH TRANH</div>', unsafe_allow_html=True)
            ca, cb = st.columns(2)
            with ca:
                f_price      = st.number_input("Giá hiện tại ($)",        value=25.0,  format="%.2f", step=0.5)
            with cb:
                f_orig_price = st.number_input("Giá gốc ($)",             value=30.0,  format="%.2f", step=0.5)
            
            cc, cd = st.columns(2)
            with cc:
                f_lowest     = st.number_input("Giá thấp nhất ($)",  value=20.0,  format="%.2f", step=0.5)
            with cd:
                f_offers     = st.number_input("Số đối thủ",         value=1, min_value=0, step=1)
            
            f_ship       = st.number_input("Phí vận chuyển ($)",      value=0.0,   format="%.2f", step=0.5)

            st.markdown('<div class="sec">ĐÁNH GIÁ & UY TÍN</div>', unsafe_allow_html=True)
            f_rating  = st.slider("Điểm đánh giá (Rating)", 0.0, 5.0, 4.2, step=0.1)
            f_reviews = st.number_input("Số lượt đánh giá (Reviews)", value=100, min_value=0, step=1)

            st.markdown('<div class="sec">PHÂN LOẠI & ĐẶC TÍNH</div>', unsafe_allow_html=True)
            f_cat = st.selectbox("Danh mục sản phẩm", cat_options,
                                 format_func=lambda s: s.replace("_", " ").title())
            
            chk_col1, chk_col2 = st.columns(2)
            with chk_col1:
                f_prime  = st.checkbox("Hỗ trợ Prime",      value=True)
                f_choice = st.checkbox("Amazon's Choice",   value=False)
            with chk_col2:
                f_climate = st.checkbox("Climate Friendly", value=False)
                f_vars    = st.checkbox("Có biến thể",      value=True)

            st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("THỰC HIỆN DỰ BÁO")

    with col_res:
        if not submitted:
            st.markdown(
                '<div class="ph">'
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
                    badge_txt, badge_cls = "Tiềm năng cao", "b-hi"
                elif final_val > 50:
                    badge_txt, badge_cls = "Ổn định",       "b-md"
                else:
                    badge_txt, badge_cls = "Cần tối ưu",    "b-lo"

                st.markdown(
                    f'<div class="mc">'
                    f'  <div class="mc-lbl">Dự đoán doanh số / tháng</div>'
                    f'  <div class="mc-val">{final_val:,}<span class="mc-unit">đơn</span></div>'
                    f'  <span class="mc-badge {badge_cls}">{badge_txt}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f'<div class="kpi-row">'
                    f'<div class="kpi"><div class="kpi-l">Discount</div>'
                    f'<div class="kpi-v">{f_discount_rate*100:.1f}%</div></div>'
                    f'<div class="kpi"><div class="kpi-l">Rating</div>'
                    f'<div class="kpi-v">{f_rating:.1f}</div></div>'
                    f'<div class="kpi"><div class="kpi-l">Reviews</div>'
                    f'<div class="kpi-v">{f_reviews:,}</div></div>'
                    f'<div class="kpi"><div class="kpi-l">Đối thủ</div>'
                    f'<div class="kpi-v">{f_offers}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                model_lbl = selected_model_name.replace("_"," ").replace(".pkl","").title()
                cat_lbl   = f_cat.replace("_"," ").title()
                extras    = "".join(
                    f'<span class="chip">{t}</span>'
                    for t in (["Choice"] if f_choice else [])
                           + (["Climate Friendly"] if f_climate else [])
                           + (["Có biến thể"] if f_vars else [])
                )
                st.markdown(
                    f'<div class="chips">'
                    f'<span class="chip"><b>{cat_lbl}</b></span>'
                    f'<span class="chip">{"Hỗ trợ" if f_prime else "Không"} Prime</span>'
                    f'<span class="chip">Model: <b>{model_lbl}</b></span>'
                    f'{extras}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

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