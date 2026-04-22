import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import plotly.graph_objects as go
import sys
from services.models.feature_engineering import DiscountFeatureEngineer, OutlierClipper

def render(df):
    # PATHS
    MODEL_PATH = Path(__file__).resolve().parents[1] / "services" / "models" / "best_gradient_boosting_model.pkl"
    PROCESSOR_PATH = Path(__file__).resolve().parents[1] / "services" / "models" / "sales_prediction_processor.joblib"

    # CSS
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            background-color: #F97316;
            color: white;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    # HEADER
    st.markdown("""
        <div class="az-title-line">Dự báo Hiệu suất Sản phẩm</div>
    """, unsafe_allow_html=True)

    # LOAD MODEL + PROCESSOR
    if not MODEL_PATH.exists():
        st.error("Không tìm thấy model")
        return

    if not PROCESSOR_PATH.exists():
        st.error("Không tìm thấy processor")
        return

    try:
        # Ensure pickled objects referencing a class defined under
        # a different top-level module (e.g. "main" when saved)
        # can still be unpickled here by exposing the class on
        # those module objects before loading.
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
        processor = joblib.load(PROCESSOR_PATH)

        feature_names = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else []

        # Try to load a features dump (created at app startup) for display
        features_dump_path = Path(__file__).resolve().parents[1] / "features_dump.json"
        try:
            if features_dump_path.exists():
                import json
                with open(features_dump_path, "r", encoding="utf-8") as fh:
                    dump = json.load(fh)
                    # if dump is a list, prefer it as feature names
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

    # CATEGORY fallback
    model_categories = {"electronics": "Điện tử", "home": "Nhà cửa", "fashion": "Thời trang"}

    # Compute median/default values from available crawled data
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

            # read a subset of columns and up to first 20000 rows for speed
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

            # numeric medians
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

            # booleans/modes
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

            # delivery fee extraction from delivery_info (simple regex)
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

            # category mapping: try to pick one matching our short keys
            if "main_category_name" in samp.columns and samp["main_category_name"].notna().any():
                try:
                    mode_cat = str(samp["main_category_name"].dropna().mode().iloc[0]).lower()
                    chosen = None
                    for k in model_categories:
                        if k in mode_cat or mode_cat in k:
                            chosen = k
                            break
                    if chosen is None:
                        # fallback to first mapping key
                        chosen = list(model_categories.keys())[0]
                    med["category"] = chosen
                except Exception:
                    pass

            return med
        except Exception:
            return med

    medians = load_medians()

    # Compute target scaler (mean, std) for sales_volume_num_log_clipped
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
                # find column
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

    # Layout: left column for inputs and right column for results
    # Increase left column share so input form balances with results
    col_form, col_main = st.columns([1, 2], gap="large")

    # ---- Left: Input form ----
    with col_form:
        st.markdown('<div class="az-kpi-card" style="padding:12px;">', unsafe_allow_html=True)
        with st.form("predict_form", clear_on_submit=False):
            f_price = st.number_input("Price", value=float(medians.get("price", 25.0)), format="%.2f")
            f_orig_price = st.number_input("Original Price", value=float(medians.get("original_price", 30.0)), format="%.2f")
            f_rating = st.slider("Rating", 0.0, 5.0, float(medians.get("rating", 4.2)))
            f_reviews = st.number_input("Reviews", value=int(medians.get("reviews", 120)), min_value=0)
            f_offers = st.number_input("Offers", value=int(medians.get("offers", 1)), min_value=0)
            f_delivery_fee = st.number_input("Delivery Fee ($)", value=float(medians.get("delivery_fee", 0.0)), format="%.2f")
            f_lowest_offer_price = st.number_input("Lowest Offer Price", value=0.0, format="%.2f")

            # Category selector populated from model/dump features if available
            try:
                fn = dump_features if 'dump_features' in locals() else feature_names
                cat_options = [c.replace('cat_', '') for c in fn if isinstance(c, str) and c.startswith('cat_')]
                if not cat_options:
                    cat_options = list(model_categories.keys())
            except Exception:
                cat_options = list(model_categories.keys())

            # display nicer labels for categories
            def _fmt_cat(s):
                return s.replace('_', ' ').title()

            default_cat = medians.get('category', cat_options[0] if cat_options else list(model_categories.keys())[0])
            sel_index = 0
            if default_cat in cat_options:
                sel_index = cat_options.index(default_cat)
            f_cat = st.selectbox(
                "Category",
                cat_options,
                index=sel_index,
                format_func=_fmt_cat,
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                f_prime = st.checkbox("Prime", bool(medians.get("is_prime", True)))
                f_choice = st.checkbox("Choice", bool(medians.get("is_choice", False)))
            with col_c2:
                f_climate = st.checkbox("Climate", bool(medians.get("is_climate", False)))
                f_vars = st.checkbox("Variation", bool(medians.get("has_variation", True)))

            st.write("")
            submit = st.form_submit_button("Predict", key="predict_btn")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Right: Results / placeholder ----
    with col_main:
        if not submit:
            st.info("Chờ input... Điền thông tin bên trái và nhấn Predict.")
        else:
            # RAW INPUT
            try:
                raw_input = pd.DataFrame([{
                "price": f_price,
                "original_price": f_orig_price,
                "rating": f_rating,
                "review_count": f_reviews,
                "offer_count": f_offers,
                "delivery_fee": f_delivery_fee,
                "lowest_offer_price": f_lowest_offer_price,
                "category": f_cat,
                "is_prime": f_prime,
                "is_choice": f_choice,
                "is_climate": f_climate,
                "has_variation": f_vars,
                }])
            except Exception as _e:
                st.error(f"Input construction error: {_e}")
                raw_input = pd.DataFrame([{
                    "price": medians.get("price", 25.0),
                    "original_price": medians.get("original_price", 30.0),
                    "rating": medians.get("rating", 4.2),
                    "review_count": medians.get("reviews", 0),
                    "offer_count": medians.get("offers", 1),
                    "delivery_fee": medians.get("delivery_fee", 0.0),
                    "lowest_offer_price": 0.0,
                    "sales_volume": 0,
                    "category": medians.get("category"),
                    "is_prime": medians.get("is_prime", True),
                    "is_choice": medians.get("is_choice", False),
                    "is_climate": medians.get("is_climate", False),
                    "has_variation": medians.get("has_variation", True),
                }])

            try:
                # PROCESS
                proc_input = raw_input.copy()
                col_map = {
                    "crawl_category": "category",
                    "has_variations": "has_variation",
                    "is_amazon_choice": "is_choice",
                    "is_climate_friendly": "is_climate",
                    "number_of_offers": "offer_count",
                    "reviews": "review_count",
                    "lowest_offer_price": "lowest_offer_price",
                }
                defaults = {
                    "delivery_fee": float(medians.get("delivery_fee", 0.0)),
                    "number_of_offers": int(medians.get("offers", 0)),
                    "reviews": int(medians.get("reviews", 0)),
                }
                for new_col, src_col in col_map.items():
                    if new_col not in proc_input.columns:
                        if src_col in proc_input.columns:
                            proc_input[new_col] = proc_input[src_col]
                        else:
                            proc_input[new_col] = defaults.get(new_col, np.nan)
                if "delivery_fee" not in proc_input.columns:
                    proc_input["delivery_fee"] = defaults["delivery_fee"]

                X_processed_array = processor.transform(proc_input)

                # convert processed output to DataFrame
                if isinstance(X_processed_array, np.ndarray):
                    arr = X_processed_array
                    if arr.ndim == 1:
                        arr = arr.reshape(1, -1)
                    ncols = arr.shape[1]
                    cols = None
                    if isinstance(feature_names, (list, tuple)) and len(feature_names) == ncols:
                        cols = list(feature_names)
                    else:
                        try:
                            if hasattr(processor, "get_feature_names_out"):
                                names_out = list(processor.get_feature_names_out())
                            else:
                                names_out = None
                            if names_out and len(names_out) == ncols:
                                cols = names_out
                        except Exception:
                            cols = None
                    if cols is None:
                        if isinstance(feature_names, (list, tuple)) and len(feature_names) >= 1:
                            if len(feature_names) >= ncols:
                                cols = list(feature_names)[:ncols]
                            else:
                                cols = list(feature_names) + [f"f_{i}" for i in range(len(feature_names), ncols)]
                        else:
                            cols = [f"f_{i}" for i in range(ncols)]
                    X_processed = pd.DataFrame(arr, columns=cols)
                else:
                    X_processed = X_processed_array

                # align to model columns
                if hasattr(model, "feature_names_in_"):
                    expected = list(model.feature_names_in_)
                    if not isinstance(X_processed, pd.DataFrame):
                        arr = np.asarray(X_processed)
                        if arr.ndim == 1:
                            arr = arr.reshape(1, -1)
                        X_processed = pd.DataFrame(arr, columns=[f"f_{i}" for i in range(arr.shape[1])])
                    missing = [c for c in expected if c not in X_processed.columns]
                    for c in missing:
                        X_processed[c] = 0
                    extras = [c for c in X_processed.columns if c not in expected]
                    if extras:
                        X_processed = X_processed.drop(columns=extras)
                    X_processed = X_processed[expected]

                # PREDICT
                raw_pred = model.predict(X_processed)[0]
                is_classifier = hasattr(model, "classes_")

                # Display results
                if is_classifier:
                    pred_class = int(raw_pred)
                    txt = "Thấp" if pred_class == 0 else ("Trung bình" if pred_class == 1 else "Cao")
                    st.success(f"Kết quả: {txt}")
                else:
                    st.write(f"Raw output: {raw_pred:.4f}")
                    use_log = st.checkbox("Inverse log (expm1)", True)
                    val = raw_pred
                    if use_log:
                        # model output appears to be standardized (target was scaled in preprocessing)
                        if target_mean is not None and target_std is not None:
                            # inverse standard scaling then inverse log
                            val_log = (val * target_std) + target_mean
                            val = np.expm1(val_log)
                        else:
                            # fallback: assume raw_pred is already log-scale
                            val = np.expm1(val)
                    final_val = int(max(0, round(val)))
                    st.metric("Sales dự đoán", f"{final_val:,}")
                    if final_val > 200:
                        st.success("Tiềm năng cao")
                    elif final_val > 50:
                        st.info("Ổn định")
                    else:
                        st.warning("Cần tối ưu")

                # RESULT LAYOUT: chart left, debug/model-info right
                col_chart, col_side = st.columns([3, 1])
                with col_chart:
                    if hasattr(model, 'feature_importances_'):
                        imp = pd.DataFrame({"f": feature_names, "v": model.feature_importances_}).sort_values("v", ascending=False).head(8)
                        fig = go.Figure(go.Bar(x=imp["v"], y=imp["f"], orientation='h'))
                        fig.update_layout(height=320, margin=dict(t=20, b=20, l=40, r=20))
                        st.plotly_chart(fig, use_container_width=True)
                with col_side:
                    with st.expander("DEBUG", expanded=False):
                        st.write("RAW INPUT")
                        st.dataframe(raw_input, height=120)
                        st.write("PROCESSED (head)")
                        try:
                            st.dataframe(X_processed.head(5), height=260)
                        except Exception:
                            st.dataframe(X_processed, height=260)
                        # session_state debug to diagnose repeated-submit issues
                        try:
                            st.write("session_state keys:")
                            st.write(list(st.session_state.keys()))
                        except Exception:
                            pass

                # Show full list of model features and category mapping
                with st.expander("Model features & categories", expanded=False):
                    try:
                        # feature names from model/dump
                        fn = dump_features if 'dump_features' in locals() else feature_names
                        st.write(f"Total features: {len(fn)}")
                        st.dataframe(pd.DataFrame({"feature": fn}))

                        # extract category dummies (common prefix 'cat_')
                        cats = [c for c in fn if c.startswith('cat_')]
                        if cats:
                            st.write("Detected category dummy columns:")
                            st.write(', '.join(cats))
                            # try to infer original category names
                            inferred = [c.replace('cat_', '') for c in cats]
                            st.write("Inferred categories (suffixes):")
                            st.write(', '.join(inferred))
                        else:
                            st.info("No category dummy columns detected in model features.")
                    except Exception as e:
                        st.write("Could not load feature list:", e)

            except Exception as e:
                st.error(f"Lỗi predict: {e}")

    # =========================
    # TECH INFO
    # =========================
    with st.expander("Model info"):
        st.write(type(model).__name__)
        st.write(len(feature_names))
        st.dataframe(pd.DataFrame({"features": feature_names}))