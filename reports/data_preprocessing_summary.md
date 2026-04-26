# 3.4 Tiền xử lý dữ liệu

Quy trình tiền xử lý dữ liệu được thực hiện nghiêm ngặt để đảm bảo chất lượng cho các mô hình học máy. Dữ liệu thô ban đầu gồm **9.180 dòng** và **58 đặc trưng**.

### 1. Kiểm tra tính nhất quán của dữ liệu và chuẩn hóa tên cột/đơn vị đo
- **Chuẩn hóa giá trị giả (Placeholders)**: Đưa các chuỗi văn bản rỗng hoặc mang ý nghĩa "trống" như `[]`, `{}`, `missing value`, `N/A`, `nan` về giá trị `NaN` thực thụ để hệ thống dễ dàng nhận diện và xử lý.
- **Ép kiểu dữ liệu**: Chuyển các cột cần thiết (`price`, `original_price`, `rating`, `reviews`, `number_of_offers`, `lowest_offer_price`) sang định dạng số (Numerical) đề phòng lỗi dữ liệu bị dính chuỗi văn bản.
- **Kiểm tra Logic nghiệp vụ**: Kiểm soát tính logic của dữ liệu bằng cách đảm bảo giá sản phẩm (`price`) và lượt đánh giá (`reviews`) không mang giá trị âm (<0); điểm đánh giá (`rating`) phải nằm đúng trong khoảng từ 1.0 đến 5.0. Nếu vi phạm, gán về giá trị `NaN`.
- **Nhất quán biến Boolean**: Đảm bảo các cờ hiệu (ví dụ: `is_prime`, `is_amazon_choice`, `is_climate_friendly`, `has_variations`) chỉ chứa giá trị `True/False` hợp lệ, sau đó biến đổi đồng loạt sang số nguyên `0/1`.
- **Xử lý trùng lặp**: Xác định các bản ghi lặp lại dựa theo mã định danh duy nhất của Amazon (`asin`). Xóa bỏ các dòng thừa (chỉ giữ lại bản ghi đầu tiên) và sau đó loại bỏ hoàn toàn cột `asin` vì không có giá trị dự báo.

### 2. Xử lý giá trị thiếu
- **Thống kê tỉ lệ thiếu**: Phân tích và trực quan hóa tỉ lệ khuyết thiếu cho từng đặc trưng, chia làm 3 nhóm (nghiêm trọng, trung bình, chất lượng tốt) để định hướng xử lý.
- **Chiến lược loại bỏ**: 
  - Xóa bỏ toàn bộ 13 cột có tỉ lệ khuyết thiếu nghiêm trọng ($\ge 85\%$) như `customer_feedback_summary`, `min_order_quantity`, `unit_price`, `has_aplus_content`,... vì việc cố gắng điền số liệu sẽ làm sai lệch bản chất dữ liệu.
  - Loại bỏ thêm 31 đặc trưng không mang giá trị dự báo (dữ liệu dư thừa, URL, JSON cấu trúc phức tạp).
- **Chiến lược điền giá trị thiếu (Thay thế)**:
  - **`original_price`** (thiếu 55.53%): Thiếu thông tin giá gốc đồng nghĩa với việc sản phẩm không được giảm giá. Do đó, thay thế giá trị thiếu bằng giá hiện tại (`price`).
  - **`sales_volume`**: Điền chuỗi mặc định `"0 bought in past month"` để định danh chính xác các sản phẩm chưa có lượt bán.
  - **`delivery_info`**: Điền chuỗi mặc định `"No delivery information"`.
- **Chiến lược loại bỏ dòng**: Đối với `price` và `rating` (nhóm chất lượng tốt, tỉ lệ thiếu <3%), trực tiếp xóa các bản ghi bị khuyết để loại bỏ hoàn toàn nhiễu, đảm bảo chất lượng dữ liệu huấn luyện.

### 3. Xử lý ngoại lai
- **Tiêu chí phát hiện**: Các giá trị cực biên nằm ngoài khoảng phân phối Percentile 1% và 99% của tập dữ liệu.
- **Quyết định xử lý**: Không xóa bỏ các dòng dữ liệu để tránh làm mất thông tin, thay vào đó áp dụng phương pháp **Outlier Clipping (Winsorization)** trong Pipeline. Các giá trị nằm ngoài khoảng [1%, 99%] sẽ bị giới hạn (clip) bằng đúng giá trị tại ngưỡng Percentile 1% hoặc 99% tương ứng. Quyết định này giúp loại bỏ nhiễu từ các giá trị quá dị biệt một cách hiệu quả.

### 4. Chuyển đổi kiểu dữ liệu
- **Đặc trưng Số**: Áp dụng phép biến đổi Logarit (`np.log1p`) cho các biến bị lệch phải nặng (như `price`, `reviews`) để thu hẹp khoảng cách giữa các giá trị cực lớn, đưa phân phối về dạng gần chuẩn. Đồng thời áp dụng Chuẩn hóa (`StandardScaler`) để đưa tất cả các biến về cùng một thang đo (Mean = 0, Std = 1).
- **Biến Phân loại (Categorical)**: Sử dụng phương pháp `One-Hot Encoding` (bỏ qua giá trị chưa biết) để chuyển đổi đặc trưng `crawl_category` thành các cột định danh (0/1) riêng biệt.
- **Biến Boolean**: Các biến như `is_prime`, `is_amazon_choice`... đã được chuyển đổi sang số nguyên `0/1` từ bước tiền xử lý và chỉ cần cho đi qua nguyên trạng (passthrough) trong Pipeline.

### 5. Tạo biến mới phục vụ phân tích
Làm giàu dữ liệu bằng cách trích xuất (Feature Engineering) các đặc trưng số học từ tập dữ liệu thô:
- **Mức giảm giá (`discount`)**: Số tiền được giảm, tính bằng hiệu số giữa Giá gốc (`original_price`) trừ đi Giá hiện tại (`price`).
- **Tỉ lệ giảm giá (`discount_rate`)**: Tính tỉ lệ phần trăm giảm giá so với giá niêm yết ban đầu.
- **Sản lượng bán (`sales_volume_num`)**: Dùng biểu thức chính quy (Regex) trích xuất con số cụ thể từ các chuỗi mô tả sản lượng mua hàng (ví dụ: chuyển đổi `"1K+ bought in past month"` thành giá trị số nguyên `1000`).
- **Chi phí vận chuyển (`delivery_fee`)**: Trích xuất chi phí giao hàng dạng số định lượng từ chuỗi mô tả `delivery_info` (ví dụ: `"$11.50 delivery Mon..."` -> `11.50`).
