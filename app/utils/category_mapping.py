"""
Category Mapping Utility
Maps raw crawl_category keys from the CSV to human-readable Vietnamese display names.
Used by tab_uu_dai.py and potentially other tabs for consistent category labeling.
"""

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


def map_category(raw_key: str) -> str:
    """Map a single raw category key to its display name."""
    return CATEGORY_MAP.get(raw_key, raw_key)


def add_display_column(df, source_col="crawl_category", target_col="display_category"):
    """
    Add a 'display_category' column to a DataFrame by mapping crawl_category values.
    Does NOT modify the original crawl_category column — safe for cross-tab usage.
    """
    df[target_col] = df[source_col].map(CATEGORY_MAP).fillna(df[source_col])
    return df
