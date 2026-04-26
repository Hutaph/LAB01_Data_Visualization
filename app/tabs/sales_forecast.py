"""
Tab `tab_du_bao` (Streamlit) dùng để dự báo hiệu suất sản phẩm.

Phần UI được dựng ngay trong tab này. Tiền xử lý dữ liệu và gọi mô hình
được ủy quyền cho package `predictor` (processor/pipeline + model inference).
Luồng chính: lấy input 1 dòng từ người dùng → transform theo pipeline đã lưu
→ align feature theo model → predict và hiển thị kết quả.
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import plotly.graph_objects as go
import sys

from predictor.feature_engineering import DiscountFeatureEngineer, OutlierClipper
from predictor import MODELS_DIR, ensure_processor, transform_with_feature_names
from predictor.loader import load_processed_data

def render(df):
    # Đường dẫn cố định trong project
    DATA_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
    PROCESSOR_PATH = DATA_PROCESSED_DIR / "sales_prediction_pipeline.joblib"

    # Quét các model khả dụng để cho người dùng chọn
    try:
        model_files = sorted(MODELS_DIR.glob("*.pkl"))
        # Bỏ qua file metadata (không phải model)
        model_options = [p.name for p in model_files if p.name != "feature_names.pkl"]
    except Exception:
        model_files = []
        model_options = []

    if not model_options:
        st.error("Không tìm thấy mô hình (.pkl) trong thư mục models")
        return

    # Model mặc định (ưu tiên Gradient Boosting nếu có)
    default_name = "gradient_boosting_model.pkl"
    default_index = model_options.index(default_name) if default_name in model_options else 0

    # CSS + header
    st.markdown(
        """
        <style>
        /* Header */
        .tab-header-wrapper {
            margin-top: 25px;
            padding-bottom: 25px;
            margin-bottom: 35px;
            border-bottom: 2px solid rgba(249, 115, 22, 0.1);
        }
        .header-title-box {
            display: flex;
            flex-direction: column;
            line-height: 1.2;
            margin-bottom: 5px;
            margin-left: 45px;
        }
        .header-main-title {
            font-size: 26px;
            font-weight: 850;
            background: linear-gradient(90deg, #9A3412 0%, #EA580C 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }
        .header-sub-title {
            font-size: 15px;
            color: #6b7280;
            font-weight: 500;
            margin-top: 2px;
        }

        /* Buttons + labels */
        .stButton>button {
            width: 100%;
            background-color: #F97316 !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
            font-weight: 700 !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }
        .stButton>button:hover {
            background-color: #EA580C !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(234, 88, 12, 0.3);
        }
        .stNumberInput>div>label, .stSlider>label, .stSelectbox>label, .stCheckbox>label {
            font-weight: 700 !important;
            color: #1d2a39 !important;
        }

        /* Prediction result card */
        .custom-metric-container {
            background: #FFFAF5;
            border: 1px solid #efd9bd;
            border-left: 5px solid #F97316;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(19, 25, 33, 0.06);
        }
        .custom-metric-label {
            font-size: 14px;
            color: #6b7280;
            font-weight: 700;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .custom-metric-value {
            font-size: 38px;
            color: #1d2a39;
            font-weight: 800;
            line-height: 1;
            font-family: 'Montserrat', sans-serif;
        }
        .custom-metric-status {
            font-size: 13px;
            font-weight: 700;
            margin-top: 12px;
            display: inline-block;
            padding: 5px 12px;
            border-radius: 8px;
        }
        .status-high { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .status-mid { background: #fef08a; color: #854d0e; border: 1px solid #fde047; }
        .status-low { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
        <div class="header-container">
            <div class="header-title-box">
                <div class="header-main-title">Dự báo hiệu suất sản phẩm</div>
                <div class="header-sub-title">Advanced Machine Learning Predictive Model</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Thanh chọn model
    model_sel_col1, model_sel_col2 = st.columns([3, 1])
    with model_sel_col2:
        selected_model_name = st.selectbox(
            "Mô hình AI sử dụng",
            options=model_options,
            index=default_index,
            key="model_selector",
            format_func=lambda s: s.replace("_", " ").replace(".pkl", "").title()
        )
    
    # Đường kẻ ngăn cách
    st.markdown(
        """
        <div style="
            height: 2px; 
            background: linear-gradient(90deg, rgba(249, 115, 22, 0.3) 0%, rgba(249, 115, 22, 0) 100%); 
            margin-top: 15px; 
            margin-bottom: 30px; 
            border-radius: 2px;
        "></div>
        """,
        unsafe_allow_html=True
    )

    
    MODEL_PATH = MODELS_DIR / selected_model_name

    # Load model + processor
    if not MODEL_PATH.exists():
        st.error("Không tìm thấy model")
        return

    if not PROCESSOR_PATH.exists():
        st.error("Không tìm thấy processor")
        return

    try:
        # Một số object pickled có thể trỏ tới class theo module name cũ
        # (ví dụ lúc train/save ở file `main.py`). Đoạn này gắn class vào
        # `main`/`__main__` để tránh lỗi khi unpickle ở môi trường hiện tại.
        try:
            for _m in ("main", "__main__"):
                mod = sys.modules.get(_m)
                if mod is not None:
                    for _cls in (DiscountFeatureEngineer, OutlierClipper):
                        if not hasattr(mod, _cls.__name__):
                            setattr(mod, _cls.__name__, _cls)
        except Exception:
            pass

        model = joblib.load(MODEL_PATH)
        # Ưu tiên processor đã lưu; nếu lỗi thì build lại từ sample dữ liệu đã xử lý
        try:
            processor = joblib.load(PROCESSOR_PATH)
        except Exception:
            try:
                # Fit lại processor từ một mẫu dataframe
                sample_df, _ = load_processed_data()
                processor = ensure_processor(PROCESSOR_PATH, sample_df=sample_df)
            except Exception as _err:
                raise

        feature_names = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else []

        # Nếu có `features_dump.json` thì dùng để hiển thị/đề xuất danh mục đẹp hơn
        features_dump_path = Path(__file__).resolve().parents[1] / "features_dump.json"
        try:
            if features_dump_path.exists():
                import json
                with open(features_dump_path, "r", encoding="utf-8") as fh:
                    dump = json.load(fh)
                    # dump có thể là list feature names
                    if isinstance(dump, list) and len(dump) > 0:
                        dump_features = list(dump)
                    else:
                        dump_features = feature_names
            else:
                dump_features = feature_names
        except Exception:
            dump_features = feature_names
    except Exception as e:
        st.error(f"Lỗi load: {e}")
        return

    # Mapping danh mục (fallback)
    model_categories = {"electronics": "Điện tử", "home": "Nhà cửa", "fashion": "Thời trang"}

    # Lấy giá trị mặc định/median từ dữ liệu crawl (nếu có), để form nhìn "thật" hơn
    def load_medians():
        med = {
            "price": 25.0,
            "original_price": 30.0,
            "rating": 4.2,
            "reviews": 100,
            "offers": 1,
            "is_prime": True,
            "is_choice": False,
            "is_climate": False,
            "has_variation": True,
            "delivery_fee": 0.0,
            "category": list(model_categories.keys())[0] if model_categories else None,
        }
        try:
            crawl_dir = Path(__file__).resolve().parents[2] / "data" / "amazon_crawl"
            files = []
            if crawl_dir.exists():
                files = list(crawl_dir.glob("*.csv"))
            if not files:
                return med

            # Đọc ít cột + giới hạn số dòng để đảm bảo tốc độ
            usecols = [
                "current_price", "original_price", "rating", "reviews",
                "number_of_offers", "is_prime", "is_amazon_choice",
                "is_climate_friendly", "has_variations", "delivery_info", "main_category_name"
            ]
            dfs = []
            for f in files:
                try:
                    dfc = pd.read_csv(f, usecols=[c for c in usecols if c in pd.read_csv(f, nrows=0).columns], nrows=20000, low_memory=False)
                    dfs.append(dfc)
                except Exception:
                    continue
            if not dfs:
                return med
            samp = pd.concat(dfs, ignore_index=True, sort=False)

            # Median cho numeric
            if "current_price" in samp.columns:
                med["price"] = float(samp["current_price"].replace(["", "NA", "None"], np.nan).dropna().astype(float).median(skipna=True)) if samp["current_price"].notna().any() else med["price"]
            if "original_price" in samp.columns:
                try:
                    med["original_price"] = float(samp["original_price"].replace(["", "NA", "None"], np.nan).dropna().astype(float).median(skipna=True))
                except Exception:
                    pass
            if "rating" in samp.columns:
                try:
                    med["rating"] = float(samp["rating"].replace(["", "NA", "None"], np.nan).dropna().astype(float).median(skipna=True))
                except Exception:
                    pass
            if "reviews" in samp.columns:
                try:
                    med["reviews"] = int(samp["reviews"].replace(["", "NA", "None"], np.nan).dropna().astype(float).median(skipna=True))
                except Exception:
                    pass
            if "number_of_offers" in samp.columns:
                try:
                    med["offers"] = int(samp["number_of_offers"].replace(["", "NA", "None"], np.nan).dropna().astype(float).median(skipna=True))
                except Exception:
                    pass

            # Mode cho các cờ boolean
            if "is_prime" in samp.columns:
                try:
                    med["is_prime"] = bool(samp["is_prime"].dropna().astype(int).mode().iloc[0])
                except Exception:
                    pass
            if "is_amazon_choice" in samp.columns:
                try:
                    med["is_choice"] = bool(samp["is_amazon_choice"].dropna().astype(int).mode().iloc[0])
                except Exception:
                    pass
            if "is_climate_friendly" in samp.columns:
                try:
                    med["is_climate"] = bool(samp["is_climate_friendly"].dropna().astype(int).mode().iloc[0])
                except Exception:
                    pass
            if "has_variations" in samp.columns:
                try:
                    med["has_variation"] = bool(samp["has_variations"].dropna().astype(int).mode().iloc[0])
                except Exception:
                    pass

            # Rút phí vận chuyển từ `delivery_info` 
            if "delivery_info" in samp.columns:
                try:
                    import re
                    fees = []
                    for val in samp["delivery_info"].dropna().astype(str).head(5000):
                        m = re.search(r"\\$(\\d+(?:\\.\\d+)?)", val)
                        if m:
                            try:
                                fees.append(float(m.group(1)))
                            except Exception:
                                continue
                    if fees:
                        med["delivery_fee"] = float(pd.Series(fees).median())
                except Exception:
                    pass

            # Ưu tiên map về key ngắn (electronics/home/fashion) để đồng bộ
            if "main_category_name" in samp.columns and samp["main_category_name"].notna().any():
                try:
                    mode_cat = str(samp["main_category_name"].dropna().mode().iloc[0]).lower()
                    chosen = None
                    for k in model_categories:
                        if k in mode_cat or mode_cat in k:
                            chosen = k
                            break
                    if chosen is None:
                        # fallback: lấy key đầu tiên
                        chosen = list(model_categories.keys())[0]
                    med["category"] = chosen
                except Exception:
                    pass

            return med
        except Exception:
            return med

    medians = load_medians()

    # Ước lượng mean/std cho target (log1p + clip) từ dữ liệu crawl (nếu có)
    def compute_target_scaler():
        try:
            crawl_dir = Path(__file__).resolve().parents[2] / "data" / "amazon_crawl"
            files = list(crawl_dir.glob("*.csv"))
            if not files:
                return None, None

            import re
            vals = []
            for f in files:
                try:
                    dfc = pd.read_csv(f, usecols=lambda c: c in ['sales_volume', 'search_sales_volume'], nrows=50000, low_memory=False)
                except Exception:
                    try:
                        dfc = pd.read_csv(f, nrows=1000, low_memory=False)
                    except Exception:
                        continue
                # Tìm cột sales volume hợp lệ
                col = None
                for candidate in ['sales_volume', 'search_sales_volume']:
                    if candidate in dfc.columns:
                        col = candidate
                        break
                if col is None:
                    continue
                for v in dfc[col].fillna('0').astype(str).head(50000):
                    m = re.search(r"(\d+(?:\.\d+)?)\s*([kK]?)\+", v.lower())
                    if not m:
                        m2 = re.search(r"(\d{1,6})", v)
                        if m2:
                            vals.append(int(m2.group(1)))
                    else:
                        num = float(m.group(1))
                        if m.group(2) == 'k':
                            num *= 1000
                        vals.append(int(num))

            if not vals:
                return None, None
            arr = np.array(vals)
            logv = np.log1p(arr)
            low = np.quantile(logv, 0.01)
            high = np.quantile(logv, 0.99)
            clipped = np.clip(logv, low, high)
            return float(clipped.mean()), float(clipped.std())
        except Exception:
            return None, None

    target_mean, target_std = compute_target_scaler()

    # Layout: trái = input, phải = kết quả
    col_form, col_main = st.columns([1, 2], gap="large")

    # Trái: form nhập liệu 
    with col_form:
        with st.form("predict_form", clear_on_submit=False):

            st.markdown("<h5 style='color:#EA580C; margin-bottom: 0;'>1. Thông tin giá cả & Cạnh tranh</h5>", unsafe_allow_html=True)
            f_price = st.number_input("Giá hiện tại (USD)", value=float(medians.get("price", 25.0)), format="%.2f")
            f_orig_price = st.number_input("Giá gốc (USD)", value=float(medians.get("original_price", 30.0)), format="%.2f")
            f_lowest_offer_price = st.number_input("Giá chào thấp nhất (USD)", value=0.0, format="%.2f")
            f_delivery_fee = st.number_input("Phí vận chuyển (USD)", value=float(medians.get("delivery_fee", 0.0)), format="%.2f")
            f_offers = st.number_input("Số nhà bán cạnh tranh", value=int(medians.get("offers", 1)), min_value=0)

            st.markdown("<h5 style='color:#EA580C; margin-top: 10px; margin-bottom: 0;'>2. Đánh giá Sản phẩm</h5>", unsafe_allow_html=True)
            f_rating = st.slider("Điểm đánh giá (0-5)", 0.0, 5.0, float(medians.get("rating", 4.2)))
            f_reviews = st.number_input("Số lượt đánh giá (Reviews)", value=int(medians.get("reviews", 120)), min_value=0)

            st.markdown("<h5 style='color:#EA580C; margin-top: 10px; margin-bottom: 0;'>3. Phân loại & Đặc tính</h5>", unsafe_allow_html=True)
            # Danh mục: ưu tiên lấy từ feature dump / feature names nếu có
            try:
                fn = dump_features if 'dump_features' in locals() else feature_names
                cat_options = [c.replace('crawl_category_', '').replace('cat_', '') 
                               for c in fn if isinstance(c, str) and (c.startswith('cat_') or c.startswith('crawl_category_'))]
                if not cat_options:
                    cat_options = list(model_categories.keys())
            except Exception:
                cat_options = list(model_categories.keys())

            # Hiển thị label dễ đọc hơn
            def _fmt_cat(s):
                return s.replace('_', ' ').title()

            default_cat = medians.get('category', cat_options[0] if cat_options else list(model_categories.keys())[0])
            sel_index = 0
            if default_cat in cat_options:
                sel_index = cat_options.index(default_cat)

            f_cat = st.selectbox(
                "Danh mục (Category)",
                cat_options,
                index=sel_index,
                format_func=_fmt_cat,
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                f_prime = st.checkbox("Prime", bool(medians.get("is_prime", True)))
                f_choice = st.checkbox("Amazon's Choice", bool(medians.get("is_choice", False)))
            with col_c2:
                f_climate = st.checkbox("Climate friendly", bool(medians.get("is_climate", False)))
                f_vars = st.checkbox("Có biến thể", bool(medians.get("has_variation", True)))

            st.write("")
            submit = st.form_submit_button("Dự đoán", key="predict_btn")
        st.markdown('</div>', unsafe_allow_html=True)

    # Phải: kết quả / placeholder
    with col_main:
        if not submit:
            st.info("💡 Vui lòng nhập hoặc điều chỉnh các thông số sản phẩm ở cột bên trái và nhấn 'Dự đoán' để xem kết quả.")
        else:
            try:
                # Tính nhanh discount/discount_rate (đúng theo pipeline khi train)
                f_discount = f_orig_price - f_price
                f_discount_rate = (f_discount / f_orig_price) if f_orig_price > 0 else 0

                # Gom input về 1 dòng dataframe để đưa vào pipeline
                raw_input = pd.DataFrame([{
                    "rating": f_rating,
                    "is_amazon_choice": 1 if f_choice else 0,
                    "is_prime": 1 if f_prime else 0,
                    "has_variations": 1 if f_vars else 0,
                    "is_climate_friendly": 1 if f_climate else 0,
                    "crawl_category": f_cat,
                    "price": f_price,
                    "original_price": f_orig_price,
                    "reviews": f_reviews,
                    "number_of_offers": f_offers,
                    "lowest_offer_price": f_lowest_offer_price,
                    "delivery_fee": f_delivery_fee,
                    "discount": f_discount,
                    "discount_rate": f_discount_rate
                }])

                # Tiền xử lý bằng pipeline đã lưu (ưu tiên pipeline chuẩn trong `data/processed`)
                DATA_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
                PIPELINE_PATH = DATA_PROCESSED_DIR / "sales_prediction_pipeline.joblib"
                
                if PIPELINE_PATH.exists():
                    actual_processor = joblib.load(PIPELINE_PATH)
                else:
                    actual_processor = processor  # fallback nếu pipeline chuẩn không có

                # Transform input → feature matrix đã qua xử lý
                X_processed = transform_with_feature_names(actual_processor, raw_input)

                # Align feature theo danh sách đã lưu (nếu có)
                FEATURE_NAMES_PATH = MODELS_DIR / "feature_names.pkl"
                if FEATURE_NAMES_PATH.exists():
                    final_feature_names = joblib.load(FEATURE_NAMES_PATH)
                    
                    # Thiếu feature thì bù 0 để match shape lúc train
                    for col in final_feature_names:
                        if col not in X_processed.columns:
                            X_processed[col] = 0
                    
                    X_processed = X_processed[final_feature_names]
                else:
                    final_feature_names = X_processed.columns.tolist()

                # Predict.
                # Lưu ý: một số model được train trên output numpy array (cột dạng index),
                # nên đổi tên cột về "0..n-1" để tránh warning/khác biệt feature name.
                X_processed.columns = [str(i) for i in range(X_processed.shape[1])]
                raw_pred = model.predict(X_processed)[0]

                # Đưa về thang đo gốc (expm1). Nếu model cho giá trị âm ở biên thì clip về 0.
                final_val = np.expm1(raw_pred)
                final_val = int(max(0, round(final_val)))

                # Hiển thị kết quả
                st.markdown("### Kết quả Phân tích & Dự báo")
                
                # Layout kết quả chính
                res_col1, res_col2 = st.columns([1, 1])
                
                with res_col1:
                    if final_val > 200:
                        status_text = "Tiềm năng cao 🚀"
                        status_class = "status-high"
                    elif final_val > 50:
                        status_text = "Ổn định ⚖️"
                        status_class = "status-mid"
                    else:
                        status_text = "Cần tối ưu thêm ⚠️"
                        status_class = "status-low"

                    st.markdown(f"""
                        <div class="custom-metric-container">
                            <div class="custom-metric-label">Dự đoán Doanh số (Tháng)</div>
                            <div class="custom-metric-value">{final_val:,} <span style="font-size:20px; color:#9ca3af; font-weight:600;">đơn</span></div>
                            <div class="custom-metric-status {status_class}">{status_text}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with res_col2:
                    # Thông tin phụ
                    st.info(f"**Mô hình đang dùng:** {selected_model_name.replace('_', ' ').title()}\n\n**Đặc trưng quan trọng nhất:** Category, Reviews, Price")

                # Feature importance (nếu model hỗ trợ)
                if hasattr(model, 'feature_importances_'):
                    st.markdown("---")
                    st.markdown("**Mức độ ảnh hưởng của các chỉ số (Top 10 Features)**")
                    
                    importances = model.feature_importances_
                    feat_imp = pd.DataFrame({
                        'Feature': final_feature_names,
                        'Importance': importances
                    }).sort_values(by='Importance', ascending=False).head(10)

                    fig = go.Figure(go.Bar(
                        x=feat_imp['Importance'],
                        y=feat_imp['Feature'],
                        orientation='h',
                        marker=dict(color='rgba(249, 115, 22, 0.8)', line=dict(color='rgba(249, 115, 22, 1.0)', width=1))
                    ))
                    
                    fig.update_layout(
                        yaxis=dict(autorange="reversed"),
                        margin=dict(l=20, r=20, t=20, b=20),
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_title="Gia trị quan trọng",
                    )
                    st.plotly_chart(fig, width='stretch')

                # xem input sau khi transform
                with st.expander("🛠️ Xem dữ liệu xử lý (Debug)", expanded=False):
                    st.write("Dữ liệu đầu vào sau biến đổi (X_processed):")
                    st.dataframe(X_processed)

            except Exception as e:
                st.error(f"Lỗi predict: {e}")

    # Thông tin kỹ thuật (để debug/so sánh model)
    with st.expander("⚙️ Thông tin kỹ thuật", expanded=False):
        st.write("**Loại mô hình thuật toán:**", type(model).__name__)
        st.write("**Tổng số Input Feature:**", len(feature_names))