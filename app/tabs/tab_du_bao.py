import streamlit as st
import pandas as pd
import joblib
import os
from pathlib import Path

def render(df):
    st.header("🔮 Mô Hình Học Máy Dự Báo Doanh Số")
    st.markdown("""
    Tab này ứng dụng mô hình **Gradient Boosting Regressor** để dự báo số lượng bán ra tiềm năng của một sản phẩm Amazon 
    dựa trên các đặc tính kỹ thuật và chỉ số hiệu suất.
    """)

    # Đường dẫn tới model
    model_path = Path(__file__).resolve().parents[1] / "services" / "models" / "best_gradient_boosting_model.pkl"
    
    if not model_path.exists():
        st.error(f"⚠️ Không tìm thấy tệp mô hình tại: `app/services/models/best_gradient_boosting_model.pkl`")
        st.info("Vui lòng đảm bảo tệp mô hình đã được tải lên đúng thư mục.")
        return

    try:
        model = joblib.load(model_path)
    except Exception as e:
        st.error(f"❌ Lỗi khi tải mô hình: {e}")
        return

    # Xác định các đặc trưng (features) mà mô hình yêu cầu
    # Nếu là mô hình scikit-learn, ta có thể lấy qua feature_names_in_
    if hasattr(model, "feature_names_in_"):
        feature_names = model.feature_names_in_
    else:
        # Danh sách dự phòng dựa trên phân tích dữ liệu Amazon
        feature_names = ['price', 'rating', 'reviews', 'is_best_seller', 'is_amazon_choice', 'is_prime']

    st.subheader("🛠️ Nhập thông số sản phẩm cần dự báo")
    
    with st.expander("Hướng dẫn sử dụng", expanded=True):
        st.write("""
        1. Nhập các thông số thực tế hoặc dự kiến của sản phẩm.
        2. Nhấn nút **'Bắt đầu dự báo'**.
        3. Kết quả sẽ hiển thị số lượng sản phẩm dự kiến bán được trong một tháng.
        """)

    # Tạo form nhập liệu
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        
        input_values = {}
        
        with col1:
            st.markdown("### 📊 Chỉ số hiệu suất")
            # Kiểm tra xem feature nào có trong model để hiển thị input tương ứng
            if any(f in feature_names for f in ['price', 'current_price', 'price_clean']):
                f_name = next(f for f in feature_names if f in ['price', 'current_price', 'price_clean'])
                input_values[f_name] = st.number_input("Giá bán ($)", min_value=0.0, value=49.99, step=0.1)
            
            if any(f in feature_names for f in ['rating', 'rating_clean', 'rating_val']):
                f_name = next(f for f in feature_names if f in ['rating', 'rating_clean', 'rating_val'])
                input_values[f_name] = st.slider("Điểm đánh giá (Rating)", 0.0, 5.0, 4.5, 0.1)
                
            if 'reviews' in feature_names:
                input_values['reviews'] = st.number_input("Số lượt đánh giá (Reviews)", min_value=0, value=500, step=10)

        with col2:
            st.markdown("### 🏆 Nhãn & Đặc tính")
            if 'is_best_seller' in feature_names:
                input_values['is_best_seller'] = st.checkbox("Sản phẩm Best Seller", value=False)
            
            if 'is_amazon_choice' in feature_names:
                input_values['is_amazon_choice'] = st.checkbox("Nhãn Amazon's Choice", value=False)
                
            if 'is_prime' in feature_names:
                input_values['is_prime'] = st.checkbox("Có Prime (Giao nhanh)", value=True)
            
            if 'has_variations' in feature_names:
                input_values['has_variations'] = st.checkbox("Có nhiều biến thể", value=False)

        # Xử lý các feature còn lại nếu có (ví dụ các feature encoding cho category)
        for f in feature_names:
            if f not in input_values:
                # Nếu không có input, ta mặc định là 0 hoặc giá trị trung bình từ dataset nếu có thể
                input_values[f] = 0.0

        submit = st.form_submit_button("🔍 Bắt đầu dự báo", use_container_width=True)

    if submit:
        # Chuyển đổi input thành DataFrame đúng thứ tự feature của model
        try:
            X_input = pd.DataFrame([input_values])[feature_names]
            
            # Thực hiện dự báo
            prediction = model.predict(X_input)[0]
            
            # Hiển thị kết quả
            st.markdown("---")
            st.markdown(f"""
            <div style="background-color: #FFF7ED; padding: 20px; border-radius: 10px; border-left: 5px solid #F97316; text-align: center;">
                <h2 style="color: #9A3412; margin-bottom: 10px;">KẾT QUẢ DỰ BÁO</h2>
                <p style="font-size: 1.2rem; color: #1C1917;">Sản phẩm này dự kiến đạt được:</p>
                <h1 style="color: #F97316; font-size: 3rem; margin: 10px 0;">{int(max(0, prediction)):,}</h1>
                <p style="font-size: 1.1rem; color: #78716C;">lượt bán ra mỗi tháng</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Thêm phân tích context
            st.write("")
            with st.expander("📈 Phân tích từ mô hình", expanded=True):
                st.write(f"Mô hình ước tính dựa trên dữ liệu lịch sử của hơn {len(df):,} sản phẩm tương tự.")
                if prediction > df['sales_volume_num'].mean():
                    st.success("✨ Đây là mức doanh số **CAO** hơn mức trung bình của thị trường.")
                else:
                    st.warning("📉 Đây là mức doanh số **THẤP** hơn mức trung bình của thị trường.")
                
        except Exception as e:
            st.error(f"Lỗi khi thực hiện dự báo: {e}")
            st.info("Có thể do mô hình yêu cầu các đặc trưng (features) khác với danh sách hiện tại.")

    # Hiển thị độ quan trọng của các đặc trưng nếu có
    if hasattr(model, 'feature_importances_'):
        st.markdown("---")
        st.subheader("📊 Các yếu tố ảnh hưởng nhất (Feature Importance)")
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False).head(5)
        
        st.bar_chart(importance_df.set_index('Feature'), color="#F97316")
        st.caption("Biểu đồ thể hiện mức độ đóng góp của từng yếu tố vào kết quả dự báo của mô hình.")
