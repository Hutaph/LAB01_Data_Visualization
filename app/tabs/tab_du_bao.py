import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
import plotly.graph_objects as go

def render(df):
    # Setup Paths
    MODEL_PATH = Path(__file__).resolve().parents[1] / "services" / "models" / "best_gradient_boosting_model.pkl"

    # Custom CSS for polished Technical Dashboard / Clean Utility look
    st.markdown("""
        <style>
        .predict-header {
            background: linear-gradient(90deg, #F97316 0%, #FB923C 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }
        .stButton>button {
            width: 100%;
            background-color: #F97316;
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #EA580C;
            transform: translateY(-1px);
        }
        .input-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            margin-bottom: 1rem;
        }
        .result-card {
            background: #FFF7ED;
            padding: 2.5rem;
            border-radius: 16px;
            border: 2px solid #FDBA74;
            text-align: center;
            margin: 2rem 0;
            animation: fadeIn 0.5s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="az-header" style="margin-bottom: 24px;">
            <div class="az-header-logo-wrap">
                <span class="az-header-logo-fallback">🔮</span>
            </div>
            <div class="az-header-left">
                <div class="az-header-breadcrumb">DỰ BÁO <span>/</span> AI PREDICTION</div>
                <div class="az-title-line">Dự báo Hiệu suất Sản phẩm</div>
                <div class="az-subtitle">Ứng dụng máy học Gradient Boosting để tối ưu hóa chiến lược kinh doanh</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Load Model
    if not MODEL_PATH.exists():
        st.error("⚠️ Không tìm thấy tệp mô hình tại: `app/services/models/best_gradient_boosting_model.pkl`")
        return

    try:
        model = joblib.load(MODEL_PATH)
        feature_names = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else []
        # DEBUG: Save feature names to json for inspection
        import json
        dump_path = Path(__file__).resolve().parent / "features_dump.json"
        with open(dump_path, "w") as f:
            json.dump(feature_names, f)
    except Exception as e:
        st.error(f"❌ Lỗi khi tải mô hình: {e}")
        return

    # Dynamically extract categories from feature names
    # Cat features usually start with 'cat_' or 'category_'
    model_categories = {}
    for f in feature_names:
        if f.startswith("cat_"):
            clean_name = f.replace("cat_", "").replace("_", " ").title()
            model_categories[f.replace("cat_", "")] = clean_name
        elif f.startswith("category_"):
            clean_name = f.replace("category_", "").replace("_", " ").title()
            model_categories[f.replace("category_", "")] = clean_name
            
    if not model_categories:
        # Fallback if names are different or not prefixed
        model_categories = {"electronics": "Điện tử", "home": "Nhà cửa", "fashion": "Thời trang"}

    # Layout: main.css forces the first column of st.columns to 70px.
    # To avoid squashing our content, we ALWAYS add a 70px dummy column at the start of any st.columns call.
    
    # Main content columns
    dummy_main, col_main = st.columns([1, 20])
    
    with col_main:
        # Split into Input and Result
        # Again, we add a dummy column at the start to satisfy the CSS rule
        dummy_split, col_input, col_result = st.columns([0.1, 1.2, 1], gap="medium")

        with col_input:
            st.markdown("#### 📋 Thông số sản phẩm")
            with st.form("prediction_form", border=False):
                st.markdown("<p style='font-weight:700; color:#7B341E; margin-bottom:5px;'>📊 Chỉ số tài chính & Hiệu suất</p>", unsafe_allow_html=True)
                f_price = st.number_input("Giá bán hiện tại ($)", min_value=0.0, value=25.0, step=0.1)
                f_orig_price = st.number_input("Giá niêm yết (Original) ($)", min_value=0.0, value=30.0, step=0.1)
                f_rating = st.slider("Điểm đánh giá (Rating)", 0.0, 5.0, 4.2, 0.1)
                f_reviews = st.number_input("Số lượt đánh giá", min_value=0, value=120)
                f_offers = st.number_input("Số nhà cung cấp", min_value=1, value=1)
                
                st.markdown("<p style='font-weight:700; color:#7B341E; margin-top:15px; margin-bottom:5px;'>🏷️ Phân loại & Đặc tính</p>", unsafe_allow_html=True)
                f_cat = st.selectbox("Danh mục", options=list(model_categories.keys()), format_func=lambda x: model_categories[x])
                
                # Checkboxes for binary features
                c1, c2 = st.columns([1, 1]) # This will also be affected by CSS if we are not careful
                # Wait, inside a form we can't easily add dummy columns for every small split
                # Let's just use single column for check boxes or careful layout
                f_prime = st.checkbox("Sẵn có Prime", value=True)
                f_choice = st.checkbox("Amazon's Choice", value=False)
                f_climate = st.checkbox("Climate Choice", value=False)
                f_vars = st.checkbox("Có biến thể", value=True)

                submit = st.form_submit_button("🚀 THỰC HIỆN DỰ BÁO")

        with col_result:
            if not submit:
                st.markdown("""
                    <div class="az-tab-placeholder" style="min-height: 520px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: rgba(255,255,255,0.3); border: 2px dashed rgba(123,75,23,0.15); border-radius: 12px;">
                        <div style="font-size: 4rem; margin-bottom: 20px; opacity: 0.5;">🤖</div>
                        <div style="font-family: 'Montserrat'; font-weight: 700; color: #7B341E; opacity: 0.7;">Hệ thống AI sẵn sàng</div>
                        <div style="font-size: 0.9rem; color: #7B341E; opacity: 0.5; margin-top: 10px;">Nhấn nút dự báo để bắt đầu mô phỏng</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # PREPROCESSING
                def safe_log(val):
                    return np.log1p(max(0, val))

                # derived features
                discount_amount = f_orig_price - f_price if f_orig_price > f_price else 0.0
                discount_rate = discount_amount / f_orig_price if f_orig_price > 0 else 0.0

                input_dict = {f: 0.0 for f in feature_names}
                
                # Basic values to map (Order matters for substring matching!)
                mapping_values = {
                    'original': f_orig_price,
                    'lowest': f_price * 0.95,
                    'delivery': 5.99, # fallback average delivery cost
                    'discount_rate': discount_rate,
                    'discount': discount_amount,
                    'price': f_price,
                    'rating': f_rating,
                    'review': f_reviews,
                    'offer': f_offers,
                }
                
                binary_values = {
                    'choice': f_choice,
                    'prime': f_prime,
                    'variation': f_vars,
                    'climate': f_climate,
                }
                
                for f in feature_names:
                    f_lower = f.lower()
                    
                    # 1. Map Categories
                    if f_lower.startswith('cat_') or f_lower.startswith('category_'):
                        if str(f_cat).lower() in f_lower:
                            input_dict[f] = 1.0
                        continue
                        
                    # 2. Map Binary features
                    matched_binary = False
                    for key, val in binary_values.items():
                        if key in f_lower:
                            input_dict[f] = 1.0 if val else 0.0
                            matched_binary = True
                            break
                    if matched_binary:
                        continue
                        
                    # 3. Map Numeric features
                    for key, val in mapping_values.items():
                        if key in f_lower:
                            # Check if the feature name suggests it was log-transformed
                            if 'log' in f_lower:
                                input_dict[f] = safe_log(val)
                            else:
                                input_dict[f] = float(val)
                            break

                try:
                    X_input = pd.DataFrame([input_dict])[feature_names]
                    raw_pred = model.predict(X_input)[0]
                    
                    is_classifier = hasattr(model, "classes_")

                    if is_classifier:
                        # Classification target! 0 might mean 'Low', 1 means 'Medium', etc.
                        pred_class = int(raw_pred)
                        if pred_class == 0:
                            final_sales_text = "Thấp (0 - 50)"
                            kpi_color = "#9CA3AF" # Grey
                        elif pred_class == 1:
                            final_sales_text = "Trung bình (50 - 500)"
                            kpi_color = "#F59E0B" # Yellow
                        elif pred_class == 2:
                            final_sales_text = "Cao (500 - 5000)"
                            kpi_color = "#3B82F6" # Blue
                        else:
                            final_sales_text = f"Rất Cao (Nhóm {pred_class})"
                            kpi_color = "#F97316" # Orange

                        st.markdown(f"""
                            <div class="az-kpi-card" style="border-left-width: 10px; border-left-color: {kpi_color}; padding: 45px 25px; text-align: center; margin-bottom: 25px;">
                                <div class="az-kpi-title" style="font-size: 1rem; color: #475569; font-weight: 700;">PHÂN QUYỀN DOANH SỐ (CLASS TIER)</div>
                                <div class="az-kpi-value" style="font-size: 3rem; color: {kpi_color}; line-height: 1.2; margin-top: 10px;">{final_sales_text}</div>
                                <div style="font-size: 0.85rem; margin-top: 25px; color: #64748B; background: #F8FAFC; padding: 12px; border-radius: 8px; font-weight: 500;">
                                    Mô hình được huấn luyện theo dạng phân lớp (Classification). Raw Class Pred: {raw_pred}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Regression target
                        
                        st.markdown(f"""
                            <div style="font-size: 0.85rem; margin-top: 10px; color: #64748B; background: #F8FAFC; padding: 12px; border-radius: 8px; font-weight: 500; margin-bottom: 15px; border: 1px solid #E2E8F0;">
                                Raw Predictive Output (Giá trị nguyên bản): <strong style="color: #0F172A;">{raw_pred:.4f}</strong>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("⚙️ Giải mã Output (Inverse Target Transform)", expanded=True):
                            st.markdown("Số âm (VD: -2.3, +1.4) là 100% bằng chứng: biến mục tiêu Doanh Số đã bị chuẩn hóa `StandardScaler` (hoặc `RobustScaler`) trước khi đưa vào train. Hãy nhập thông số bên dưới để đảo ngược quy trình thu hồi lại Doanh số thực:")
                            use_target_scaler = st.checkbox("Khôi phục Z-Score (Inverse Transform)", value=True)
                            
                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                target_mean = st.number_input("Target Mean (Giá trị trung bình `mean_`)", value=4.5, step=0.1)
                            with col_s2:
                                target_std = st.number_input("Target Std (Độ lệch chuẩn `scale_`)", value=2.0, step=0.1)
                            
                            apply_expm = st.checkbox("Khôi phục hệ Log (np.expm1)", value=True, help="Nếu target ban đầu trước khi Scale là log(sales + 1)")
                        
                        # Apply Transformations
                        calculated_pred = raw_pred
                        
                        if use_target_scaler:
                            calculated_pred = (calculated_pred * target_std) + target_mean
                            
                        if apply_expm:
                            calculated_pred = np.expm1(calculated_pred) if calculated_pred < 25 else calculated_pred
                            
                        final_sales_disp = max(0, int(calculated_pred))
                        
                        # UI Presentation
                        st.markdown(f"""
                            <div class="az-kpi-card" style="border-left-width: 10px; padding: 45px 25px; text-align: center; margin-bottom: 25px; margin-top: 25px">
                                <div class="az-kpi-title" style="font-size: 1rem; color: #64748B; font-weight: 700;">DOANH SỐ DỰ KIẾN (ĐƠN VỊ/THÁNG)</div>
                                <div class="az-kpi-value" style="font-size: 5rem; color: #146EB4; line-height: 1;">{int(final_sales_disp):,}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with st.expander("🔍 Chi tiết Dữ liệu đầu vào (Debug)", expanded=False):
                        st.json(input_dict)
                    
                    if not is_classifier and final_sales_disp > 200:
                        st.success("💎 **Tiềm năng rất lớn:** Sản phẩm có các chỉ số vượt trội. Hãy đảm bảo chuỗi cung ứng ổn định.")
                    elif not is_classifier and final_sales_disp > 50:
                        st.info("📈 **Tiềm năng ổn định:** Sản phẩm có sức bán khá. Có thể đẩy mạnh Marketing để tăng trưởng.")
                    elif not is_classifier:
                        st.warning("⚖️ **Cần tối ưu:** Doanh số dự báo thấp. Hãy thử điều chỉnh giá hoặc cải thiện điểm Rating.")

                    # Visualizing Feature Impact
                    if hasattr(model, 'feature_importances_'):
                        imp_data = pd.DataFrame({'f': feature_names, 'v': model.feature_importances_}).sort_values('v', ascending=False).head(8)
                        fig = go.Figure(go.Bar(x=imp_data['v'], y=imp_data['f'], orientation='h', marker_color='#146EB4'))
                        fig.update_layout(
                            title=dict(text='MỨC ĐỘ ẢNH HƯỞNG CỦA CÁC ĐẶC TRƯNG', font=dict(family="Inter", size=13, color="#64748B")),
                            template='plotly_white', height=330, margin=dict(l=10, r=10, t=50, b=10),
                            xaxis=dict(showgrid=False, showticklabels=False),
                            yaxis=dict(autorange="reversed", tickfont=dict(color="#0F172A", family="Inter")),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Lỗi tính toán AI: {e}")

    # Tech Info Expander
    with st.expander("🛠️ Chi tiết kỹ thuật của mô hình AI"):
        st.write(f"**Kiểu mô hình:** `{type(model).__name__}`")
        st.write(f"**Số lượng đặc trưng đầu vào:** `{len(feature_names)}`")
        st.dataframe(pd.DataFrame({"Đặc trưng": feature_names}), height=200)
