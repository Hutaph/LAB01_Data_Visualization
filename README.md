# 🛒 Amazon Commerce Lens: E-Commerce Data Analytics Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://amazon-commerce-lens.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

Phân tích chuyên sâu dữ liệu thị trường Amazon (US) dựa trên tập dữ liệu thực tế hơn 9.000 sản phẩm. Dashboard cung cấp các góc nhìn đa chiều về chiến lược định giá, tác động của nhãn uy tín và các mô hình dự báo hiệu suất kinh doanh.

## 🚀 Tính năng chính

Dashboard được tổ chức thành 6 phân mục phân tích chiến lược:
- **📊 Tổng quan thị trường:** Báo cáo tổng hợp hiệu suất kinh doanh đa danh mục.
- **💰 Chiến lược định giá:** Tương quan giữa giá bán và hiệu quả kinh doanh thực tế.
- **🏷️ Nhãn Uy Tín (Amazon's Choice):** Đánh giá tác động của nhãn uy tín đến tâm lý mua hàng và doanh số.
- **🎁 Chương trình Ưu đãi:** Hiệu quả của các chiến dịch giảm giá và khuyến mãi.
- **⭐ Đánh giá khách hàng:** Phân tích mức độ tín nhiệm qua Rating và Review.
- **🔮 Dự báo hiệu suất:** Ứng dụng Machine Learning để dự báo tiềm năng tăng trưởng sản phẩm.

## 🛠️ Công nghệ sử dụng

- **Ngôn ngữ:** Python 3.12
- **Dashboard:** Streamlit, HTML5/CSS3 Custom Styling
- **Trực quan hóa:** Chart.js (via JavaScript injection), Plotly, Seaborn
- **Dữ liệu & ML:** Pandas, NumPy, Scikit-learn, Joblib
- **Thu thập:** Amazon Scraper API (Omkar Cloud)

## 📂 Cấu trúc dự án

```text
├── app/                  # Mã nguồn Dashboard Streamlit
│   ├── tabs/             # Các tệp phân tích theo từng Tab
│   ├── services/         # Logic xử lý dữ liệu và ML Models
│   └── styles/           # Custom CSS UI/UX
├── data/                 # Dữ liệu CSV (Raw & Processed)
├── notebook/             # Quy trình EDA và huấn luyện mô hình
├── source/               # Pipeline thu thập dữ liệu (Crawling)
└── requirements.txt      # Danh sách thư viện phụ thuộc
```

## 📊 Nguồn dữ liệu

Dữ liệu được nhóm tự thu thập độc lập qua REST API của **Amazon Scraper API** với cấu hình:
- **Phạm vi:** 30 danh mục sản phẩm chủ đạo tại thị trường Hoa Kỳ.
- **Quy mô:** 9.180 sản phẩm với 58 trường thông tin (Price, Rating, Sales Volume, Amazon's Choice, v.v.).
- **Tỷ lệ làm giàu (Enrich):** 97,1% sản phẩm có metadata chi tiết.

## ⚙️ Cài đặt & Sử dụng

1. **Clone repository:**
   ```bash
   git clone https://github.com/Hutaph/LAB01_Data_Visualization.git
   cd LAB01_Data_Visualization
   ```

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Chạy dashboard:**
   ```bash
   streamlit run app/app.py
   ```

---
© 2026 - [Hutaph](https://github.com/Hutaph) | LAB01 Data Visualization