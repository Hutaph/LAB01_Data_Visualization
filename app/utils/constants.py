CATEGORY_MAP = {
    "automotive_accessories": "Phụ kiện Ô tô",
    "baby_products": "Sản phẩm Trẻ em",
    "beauty_makeup": "Trang điểm",
    "beauty_skincare": "Chăm sóc Da",
    "electronics_gaming_consoles": "Máy chơi Game",
    "electronics_headphones": "Tai nghe",
    "electronics_keyboards": "Bàn phím",
    "electronics_laptops": "Laptop",
    "electronics_monitors": "Màn hình",
    "electronics_networking": "Thiết bị Mạng",
    "electronics_smartphones": "Điện thoại",
    "electronics_storage_ssd": "Ổ cứng SSD",
    "electronics_tablets": "Máy tính bảng",
    "fashion_bags": "Túi xách",
    "fashion_mens": "Thời trang Nam",
    "fashion_shoes": "Giày dép",
    "fashion_womens": "Thời trang Nữ",
    "health_personal_care": "Chăm sóc Cá nhân",
    "health_supplements": "Thực phẩm CN",
    "home_air_quality": "Máy lọc Không khí",
    "home_cleaning": "Vệ sinh Nhà cửa",
    "home_furniture": "Nội thất",
    "home_kitchen_appliances": "Đồ gia dụng",
    "office_stationery": "Văn phòng phẩm",
    "office_supplies": "Thiết bị VP",
    "pet_supplies": "Thú cưng",
    "sports_fitness": "Thể hình",
    "sports_outdoors": "Thể thao",
    "tools_home_improvement": "Dụng cụ Sửa chữa",
    "toys_games": "Đồ chơi",
}
FEATURE_MAP = {
    # Boolean / Flag Features
    "is_amazon_choice": "Amazon's Choice",
    "is_prime": "Amazon Prime",
    "is_climate_friendly": "Climate Pledge Friendly",
    "is_bestseller": "Sản phẩm Bán chạy",
    "has_variations": "Có biến thể/phiên bản", 
    "has_video": "Có Video sản phẩm",
    "has_aplus_content": "Nội dung A+",
    "has_brand_story": "Câu chuyện thương hiệu",
    
    # Content & Quality Features
    "key_features": "Đặc điểm nổi bật", 
    "full_description": "Mô tả đầy đủ",
    "technical_details": "Chi tiết kỹ thuật",
    "product_details": "Thông số sản phẩm",
    "aplus_images": "Hình ảnh A+",
    "customer_feedback_summary": "Tóm tắt phản hồi",
    "top_reviews_global": "Đánh giá toàn cầu",
    
    # Quantitative Features
    "rating": "Điểm đánh giá",
    "reviews": "Số lượt đánh giá",
    "number_of_offers": "Số lượng Nhà bán",
    "lowest_offer_price": "Giá chào thấp nhất",
    "current_price": "Giá hiện tại",
    "unit_price": "Đơn giá",
    "unit_count": "Số lượng đơn vị",
    "min_order_quantity": "Số lượng đặt tối thiểu",
    "discount": "Mức giảm giá ($)",
    "discount_rate": "Tỷ lệ giảm giá (%)",
    "delivery_fee": "Phí vận chuyển",
    "delivery_info": "Thông tin giao hàng",
    "availability": "Trạng thái kho",
    "condition": "Tình trạng SP",
    "estimated_delivery_date": "Ngày giao dự kiến",
    
    # Identification
    "title": "Têu đề sản phẩm",
    "product_name": "Tên sản phẩm",
    
    # Prices & Quantitative
    "original_price": "Giá niêm yết (Gốc)",
    "detailed_rating": "Điểm đánh giá chi tiết",
    "top_reviews": "Đánh giá nổi bật",
    "country": "Quốc gia/Khu vực",
    "currency": "Đơn vị tiền tệ",
    
    # Media & Assets
    "main_image_url": "Hình ảnh chính (URL)",
    "additional_image_urls": "Hình ảnh bổ sung",
    "product_videos": "Video giới thiệu SP",
    "user_videos": "Video đánh giá từ khách",
    "video_thumbnail": "Ảnh đại diện Video",
    
    # Meta / Organizational Features
    "main_category": "Danh mục chính",
    "category_hierarchy": "Cấp bậc danh mục",
    "brand_info": "Thông tin thương hiệu",
    "variation_dimensions": "Thuộc tính biến thể",
    "variants": "Thông tin biến thể",
    "all_variants": "Danh sách biến thể",
    "is_best_seller": "Sản phẩm Bán chạy (Gốc)",
}

def add_display_column(df, source_col="crawl_category", target_col="display_category"):
    """
    Add a 'display_category' column to a DataFrame by mapping crawl_category values.
    Does NOT modify the original crawl_category column — safe for cross-tab usage.
    """
    df[target_col] = df[source_col].map(CATEGORY_MAP).fillna(df[source_col])
    return df