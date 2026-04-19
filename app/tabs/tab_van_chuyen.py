import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import re


def render(df_raw):
    df = df_raw.copy()

    # ══════════════════════════════════════════════════════════════
    # 1. PREPROCESSING
    # ══════════════════════════════════════════════════════════════

    # --- is_prime ---
    if "is_prime" not in df.columns:
        df["is_prime"] = False
    else:
        df["is_prime"] = df["is_prime"].fillna(False).astype(bool)

    # --- delivery_fee ---
    if "delivery_fee" not in df.columns:
        df["delivery_fee"] = 0.0
    else:
        df["delivery_fee"] = pd.to_numeric(df["delivery_fee"], errors="coerce").fillna(0.0)

    # --- sales_volume_num ---
    if "sales_volume_num" in df.columns:
        df["sales_volume_num"] = pd.to_numeric(df["sales_volume_num"], errors="coerce").fillna(0).astype(int)
    else:
        df["sales_volume_num"] = 0

    # --- price ---
    if "price" in df.columns:
        df["current_price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    else:
        df["current_price"] = 0.0

    # --- rating ---
    if "rating" in df.columns:
        df["rating_val"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    else:
        df["rating_val"] = 0.0

    # --- is_amazon_choice (proxy for distinguished products) ---
    if "is_amazon_choice" not in df.columns:
        df["is_amazon_choice"] = False
    else:
        df["is_amazon_choice"] = df["is_amazon_choice"].fillna(False).astype(bool)

    # --- crawl_category ---
    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"

    def group_category(cat):
        c = str(cat).lower()
        if c.startswith("electronics"): return "Hàng Điện Tử"
        if c.startswith("fashion"): return "Thời Trang"
        if c.startswith("home"): return "Gia Dụng & Nội Thất"
        if c.startswith("beauty"): return "Làm Đẹp"
        if c.startswith("health"): return "Sức Khỏe"
        if c.startswith("sports"): return "Thể Thao"
        if c.startswith("office"): return "Văn Phòng"
        if c.startswith("baby"): return "Trẻ Em"
        if c.startswith("pet"): return "Thú Cưng"
        if c.startswith("tools"): return "Cải Tạo Nhà"
        if c.startswith("toys"): return "Đồ Chơi"
        if c.startswith("automotive"): return "Phương Tiện"
        return "Khác"

    df["crawl_category"] = df["crawl_category"].fillna("Không rõ").apply(group_category)

    # --- Computed Features ---
    df["current_price"] = df["current_price"].clip(lower=0)
    df["delivery_fee"] = df["delivery_fee"].clip(lower=0)
    df["fee_ratio"] = (df["delivery_fee"] / df["current_price"].clip(lower=0.01)).clip(upper=5.0).round(4)
    df["revenue"] = (df["sales_volume_num"] * df["current_price"]).round(0)

    # --- Estimate delivery days from delivery_date_text ---
    def parse_est_days(text):
        if pd.isna(text):
            return None
        s = str(text)
        # Format: "Mon, Apr 13"
        m = re.search(r'\w+,\s*Apr\s+(\d+)', s)
        if m:
            return max(1, int(m.group(1)) - 6)
        # Format: "Apr 8 - 28"
        m2 = re.search(r'Apr\s+(\d+)\s*-\s*(\d+)', s)
        if m2:
            return max(1, round((int(m2.group(1)) + int(m2.group(2))) / 2.0 - 6))
        return None

    if "delivery_date_text" in df.columns:
        df["est_delivery_days"] = df["delivery_date_text"].apply(parse_est_days)
    else:
        df["est_delivery_days"] = None

    # --- Top seller proxy (top 20% sales) ---
    top20_threshold = df["sales_volume_num"].quantile(0.8)
    df["is_top_seller"] = df["sales_volume_num"] >= top20_threshold

    # ══════════════════════════════════════════════════════════════
    # 2. EXPORT TO JSON
    # ══════════════════════════════════════════════════════════════

    select_cols = [
        "is_prime", "delivery_fee", "sales_volume_num", "current_price",
        "revenue", "crawl_category", "rating_val", "is_amazon_choice",
        "fee_ratio", "est_delivery_days", "is_top_seller"
    ]
    export_df = df[select_cols].copy()
    data_json_str = export_df.to_json(orient="records", force_ascii=False)

    # ══════════════════════════════════════════════════════════════
    # 3. HTML TEMPLATE
    # ══════════════════════════════════════════════════════════════

    html_code = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #F97316;
            --primary-light: #FDBA74;
            --secondary: #3B82F6;
            --dark: #9A3412;
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 10px;
            --font-family: 'Inter', sans-serif;
            --success: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            font-family: var(--font-family);
            color: var(--text-primary);
            padding: 16px 20px;
            line-height: 1.5;
        }}

        /* ── Filter Bar ── */
        .filter-bar {{
            position: sticky; top: 0; z-index: 1000;
            display: flex; align-items: center; gap: 24px; flex-wrap: wrap;
            background: var(--card-bg); padding: 14px 20px; border-radius: var(--border-radius);
            box-shadow: var(--shadow-md); margin-bottom: 20px;
        }}
        .f-item {{ display: flex; flex-direction: column; gap: 5px; }}
        .f-label {{ font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }}
        select {{
            padding: 7px 12px; border: 1px solid #D6D3D1; border-radius: 6px;
            font-family: inherit; font-size: 12px; color: var(--text-primary);
            outline: none; cursor: pointer; min-width: 200px; background: #FAFAF9;
        }}
        select:focus {{ border-color: var(--primary); box-shadow: 0 0 0 2px rgba(249,115,22,0.15); }}

        /* ── Section Headers ── */
        .section-header {{
            font-size: 14px; font-weight: 800; color: var(--dark); text-transform: uppercase;
            padding: 10px 0 8px 0; border-bottom: 2px solid #FDBA74;
            margin: 28px 0 16px 0; display: flex; align-items: center; gap: 8px;
            letter-spacing: 0.5px;
        }}
        .section-header .num {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 26px; height: 26px; border-radius: 50%; background: var(--primary);
            color: white; font-size: 13px; font-weight: 700; flex-shrink: 0;
        }}

        /* ── Objective Card ── */
        .obj-card {{
            background: linear-gradient(135deg, #FFFAF5 0%, #FFF7ED 100%);
            border: 1px solid #FED7AA; border-radius: var(--border-radius);
            padding: 18px 22px; margin-bottom: 16px;
        }}
        .obj-title {{
            font-size: 13px; font-weight: 700; color: var(--dark); text-transform: uppercase;
            margin-bottom: 6px; display: flex; align-items: center; gap: 6px;
        }}
        .obj-text {{
            font-size: 13px; line-height: 1.65; color: #44403C; font-weight: 400;
        }}
        .obj-text strong {{ color: var(--dark); font-weight: 600; }}

        /* ── KPI Cards ── */
        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }}
        .kpi-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 14px 16px;
            box-shadow: var(--shadow-sm); border-left: 4px solid var(--primary);
            display: flex; flex-direction: column; gap: 2px; transition: transform 0.15s ease;
        }}
        .kpi-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
        .kpi-title {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.3px; }}
        .kpi-value {{ font-size: 22px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }}
        .kpi-sub {{ font-size: 10px; color: var(--text-secondary); font-weight: 500; }}
        .kpi-card.c-green {{ border-left-color: var(--success); }}
        .kpi-card.c-blue {{ border-left-color: var(--secondary); }}
        .kpi-card.c-red {{ border-left-color: var(--danger); }}
        .kpi-card.c-amber {{ border-left-color: var(--warning); }}

        /* ── Chart Cards ── */
        .chart-row {{ display: flex; gap: 16px; margin-bottom: 18px; align-items: stretch; }}
        .chart-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 18px;
            box-shadow: var(--shadow-sm); display: flex; flex-direction: column; flex: 1; min-width: 0;
        }}
        .chart-header {{ margin-bottom: 12px; }}
        .chart-title {{ font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px; }}
        .chart-subtitle {{ font-size: 11px; font-weight: 400; color: var(--text-secondary); line-height: 1.4; }}
        .chart-wrapper {{ position: relative; width: 100%; flex-grow: 1; min-height: 280px; }}

        /* ── Insight Box ── */
        .insight-box {{
            background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
            border: 1px solid #A7F3D0; border-left: 4px solid var(--success);
            border-radius: var(--border-radius); padding: 16px 20px; margin-bottom: 8px;
            display: flex; gap: 12px; align-items: flex-start;
        }}
        .insight-box.warn {{
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border-color: #FDE68A; border-left-color: var(--warning);
        }}
        .insight-icon {{ font-size: 20px; flex-shrink: 0; margin-top: 1px; }}
        .insight-content {{ flex: 1; }}
        .insight-label {{ font-size: 11px; font-weight: 700; color: var(--success); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .insight-box.warn .insight-label {{ color: #B45309; }}
        .insight-text {{ font-size: 12.5px; line-height: 1.7; color: #374151; }}
        .insight-text strong {{ color: var(--dark); }}

        /* ── Heatmap Table ── */
        .hm-table {{
            width: 100%; border-collapse: collapse; font-size: 12px;
        }}
        .hm-table th {{
            background: #F5F5F4; padding: 10px 8px; text-align: center;
            font-weight: 700; color: var(--text-secondary); font-size: 11px;
            text-transform: uppercase; border: 1px solid #E7E5E4;
        }}
        .hm-table td {{
            padding: 12px 10px; text-align: center; border: 1px solid #E7E5E4;
            vertical-align: middle; transition: background 0.2s;
        }}
        .hm-table td:hover {{ filter: brightness(0.95); }}
        .hm-rating {{ font-weight: 700; font-size: 14px; color: var(--text-primary); }}
        .hm-sales {{ font-size: 11px; color: var(--text-secondary); margin-top: 2px; }}
        .hm-count {{ font-size: 10px; color: #A8A29E; margin-top: 1px; }}
        .hm-row-label {{
            text-align: left !important; font-weight: 600; color: var(--text-primary);
            background: #FAFAF9 !important; white-space: nowrap;
        }}
    </style>
</head>
<body>

    <!-- ═══ FILTER BAR ═══ -->
    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Chỉ Số Hiệu Suất</span>
            <select id="selMetric" onchange="applyFilters()">
                <option value="revenue">Doanh Thu ($)</option>
                <option value="sales">Số Lượng Bán Ra</option>
            </select>
        </div>
        <div class="f-item">
            <span class="f-label">Danh Mục Sản Phẩm</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất Cả Danh Mục</option>
            </select>
        </div>
    </div>

    <!-- ═══ OVERVIEW CARD ═══ -->
    <div class="obj-card">
        <div class="obj-title">📍 TỔNG QUAN MỤC TIÊU PHÂN TÍCH TAB VẬN CHUYỂN</div>
        <div class="obj-text">
            Tab này phân tích <strong>3 khía cạnh chiến lược</strong> của hoạt động vận chuyển trên Amazon:
            <strong>(1)</strong> Mối tương quan giữa tỷ lệ phí ship/giá sản phẩm với doanh số để đề xuất chiến lược định giá tối ưu;
            <strong>(2)</strong> Vai trò của nhãn Prime trong việc định hình đặc điểm sản phẩm nổi bật;
            <strong>(3)</strong> Tác động của tốc độ giao hàng đến rating và doanh số, từ đó đề xuất chiến lược logistics.
        </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         SECTION 1: CHIẾN LƯỢC ĐỊNH GIÁ VẬN CHUYỂN
         ═══════════════════════════════════════════════════════════ -->
    <div class="section-header"><span class="num">1</span> CHIẾN LƯỢC ĐỊNH GIÁ TỐI ƯU QUA CẤU TRÚC PHÍ VẬN CHUYỂN</div>

    <div class="obj-card">
        <div class="obj-title">🎯 Mục tiêu phân tích</div>
        <div class="obj-text">
            Đánh giá mối tương quan giữa <strong>tỷ lệ phí vận chuyển trên giá trị sản phẩm (Shipping Fee / Price)</strong>
            với <strong>khối lượng bán ra (Sales Volume)</strong>. Xác định ngưỡng phí ship tối đa mà khách hàng chấp nhận
            và đề xuất chiến lược: <em>gộp phí ship vào giá bán (freeship)</em> hay <em>tách rời phí ship</em>.
        </div>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Tỷ Lệ Phí Ship / Giá TB</div>
            <div class="kpi-value" id="kpi1_fee_ratio">0%</div>
            <div class="kpi-sub" id="kpi1_fee_ratio_sub"></div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-title">Doanh Số TB — Nhóm Free Ship</div>
            <div class="kpi-value" id="kpi1_free_sales">0</div>
            <div class="kpi-sub" id="kpi1_free_sales_sub"></div>
        </div>
        <div class="kpi-card c-red">
            <div class="kpi-title">Doanh Số TB — Nhóm Tốn Phí Ship</div>
            <div class="kpi-value" id="kpi1_paid_sales">0</div>
            <div class="kpi-sub" id="kpi1_paid_sales_sub"></div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Revenue Share — Free Ship</div>
            <div class="kpi-value" id="kpi1_rev_share">0%</div>
            <div class="kpi-sub">Tỷ trọng doanh thu nhóm miễn phí ship</div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card" style="flex: 1.4;">
            <div class="chart-header">
                <div class="chart-title">Biến Động Doanh Số Trung Bình Theo Mức Tỷ Lệ Phí Ship / Giá Sản Phẩm</div>
                <div class="chart-subtitle">Bars = doanh số TB mỗi bin · Line = số lượng sản phẩm trong bin · Xác định ngưỡng kháng cự rõ ràng</div>
            </div>
            <div class="chart-wrapper"><canvas id="cFeeBins"></canvas></div>
        </div>
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div class="chart-title">Phân Bổ Doanh Thu Theo Chiến Lược Phí Vận Chuyển</div>
                <div class="chart-subtitle">So sánh tỷ trọng doanh thu giữa nhóm Free Ship và các mức phí ship khác nhau</div>
            </div>
            <div class="chart-wrapper"><canvas id="cRevShare"></canvas></div>
        </div>
    </div>

    <div class="insight-box" id="insightBox1">
        <div class="insight-icon">💡</div>
        <div class="insight-content">
            <div class="insight-label">KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC ĐỊNH GIÁ</div>
            <div class="insight-text" id="insight1_text">Đang phân tích...</div>
        </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         SECTION 2: VAI TRÒ CỦA PRIME
         ═══════════════════════════════════════════════════════════ -->
    <div class="section-header"><span class="num">2</span> VAI TRÒ CỦA PRIME TRONG ĐỊNH HÌNH SẢN PHẨM NỔI BẬT</div>

    <div class="obj-card">
        <div class="obj-title">🎯 Mục tiêu phân tích</div>
        <div class="obj-text">
            Phân tích xác suất lọt vào nhóm <strong>sản phẩm nổi bật (Amazon's Choice, Top 20% doanh số)</strong>
            và chênh lệch hiệu suất giữa nhóm <strong>Prime</strong> vs <strong>Non-Prime</strong>.
            Xác nhận liệu Prime có phải là <em>"tấm vé bắt buộc"</em> để một sản phẩm định vị top đầu.
            <br/><em style="color: var(--text-secondary); font-size: 11px;">⚠ Lưu ý: is_best_seller = True cho 100% sản phẩm trong dataset. Sử dụng is_amazon_choice + Top 20% Sales làm proxy.</em>
        </div>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Tỷ Lệ Prime Tổng Thể</div>
            <div class="kpi-value" id="kpi2_prime_rate">0%</div>
            <div class="kpi-sub" id="kpi2_prime_rate_sub"></div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-title">Prime Rate — Amazon's Choice</div>
            <div class="kpi-value" id="kpi2_ac_prime">0%</div>
            <div class="kpi-sub">Tỷ lệ Prime trong nhóm được đề xuất</div>
        </div>
        <div class="kpi-card c-amber">
            <div class="kpi-title">Chênh Lệch Doanh Số TB</div>
            <div class="kpi-value" id="kpi2_sales_diff">0</div>
            <div class="kpi-sub" id="kpi2_sales_diff_sub"></div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Chênh Lệch Rating TB</div>
            <div class="kpi-value" id="kpi2_rating_diff">0</div>
            <div class="kpi-sub" id="kpi2_rating_diff_sub"></div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div class="chart-title">So Sánh Tỷ Lệ Prime Giữa Các Nhóm Sản Phẩm</div>
                <div class="chart-subtitle">Tỷ lệ % sản phẩm có nhãn Prime trong từng tier · Đánh giá Prime như "tấm vé" cạnh tranh</div>
            </div>
            <div class="chart-wrapper"><canvas id="cPrimeRate"></canvas></div>
        </div>
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div class="chart-title">Hồ Sơ Đa Chiều: Prime vs Non-Prime</div>
                <div class="chart-subtitle">So sánh chuẩn hóa trên 5 trục: Rating, Doanh số, Giá, Amazon Choice %, Free Ship %</div>
            </div>
            <div class="chart-wrapper"><canvas id="cRadar"></canvas></div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Hiệu Suất Prime vs Non-Prime Theo Từng Danh Mục Ngành Hàng</div>
                <div class="chart-subtitle">Đo lường chênh lệch doanh số trung bình theo từng category · Xác định ngành hàng mà Prime tạo lợi thế rõ rệt</div>
            </div>
            <div class="chart-wrapper" style="min-height: 380px;"><canvas id="cPrimeCat"></canvas></div>
        </div>
    </div>

    <div class="insight-box warn" id="insightBox2">
        <div class="insight-icon">⚠️</div>
        <div class="insight-content">
            <div class="insight-label">KẾT LUẬN: PRIME CÓ PHẢI "TẤM VÉ BẮT BUỘC"?</div>
            <div class="insight-text" id="insight2_text">Đang phân tích...</div>
        </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         SECTION 3: TỐC ĐỘ GIAO HÀNG
         ═══════════════════════════════════════════════════════════ -->
    <div class="section-header"><span class="num">3</span> TÁC ĐỘNG TỐC ĐỘ GIAO HÀNG ĐẾN ĐỊNH VỊ THƯƠNG HIỆU</div>

    <div class="obj-card">
        <div class="obj-title">🎯 Mục tiêu phân tích</div>
        <div class="obj-text">
            Đo lường mức độ ảnh hưởng của <strong>thời gian chờ giao hàng</strong> (ước tính bằng số ngày)
            đến <strong>điểm đánh giá (rating)</strong> và <strong>khối lượng bán ra (sales volume)</strong>.
            Đề xuất chiến lược định vị sản phẩm thông qua <strong>chất lượng dịch vụ logistics</strong>.
        </div>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Thời Gian Giao Hàng TB</div>
            <div class="kpi-value" id="kpi3_avg_days">0 ngày</div>
            <div class="kpi-sub" id="kpi3_avg_days_sub"></div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-title">% Giao Dưới 7 Ngày</div>
            <div class="kpi-value" id="kpi3_fast_pct">0%</div>
            <div class="kpi-sub">Tỷ lệ sản phẩm giao nhanh</div>
        </div>
        <div class="kpi-card c-red">
            <div class="kpi-title">Chênh Lệch Rating (Nhanh vs Chậm)</div>
            <div class="kpi-value" id="kpi3_rating_gap">0</div>
            <div class="kpi-sub" id="kpi3_rating_gap_sub"></div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Hệ Số Tương Quan (Ngày Giao × Rating)</div>
            <div class="kpi-value" id="kpi3_corr">0</div>
            <div class="kpi-sub">Tương quan Pearson</div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div class="chart-title">Tác Động Thời Gian Giao Hàng Đến Doanh Số & Rating</div>
                <div class="chart-subtitle">Bars = doanh số TB · Line = rating TB · Trục kép cho 2 chỉ số khác đơn vị</div>
            </div>
            <div class="chart-wrapper"><canvas id="cDeliveryImpact"></canvas></div>
        </div>
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div class="chart-title">Ma Trận: Tốc Độ Giao × Phân Khúc Giá → Rating & Doanh Số</div>
                <div class="chart-subtitle">Màu nền = mức rating trung bình · ⭐ = rating · Số liệu = doanh số TB</div>
            </div>
            <div class="chart-wrapper" style="overflow-x: auto; display: block;"><div id="heatmapContainer"></div></div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Hiệu Suất Giao Hàng Theo Danh Mục: So Sánh Nhóm Giao Nhanh vs Chậm</div>
                <div class="chart-subtitle">Grouped bar: doanh số TB của sản phẩm giao nhanh (≤7 ngày) so với giao chậm (>7 ngày) trong mỗi ngành hàng</div>
            </div>
            <div class="chart-wrapper" style="min-height: 380px;"><canvas id="cCatDelivery"></canvas></div>
        </div>
    </div>

    <div class="insight-box" id="insightBox3">
        <div class="insight-icon">🚚</div>
        <div class="insight-content">
            <div class="insight-label">KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC LOGISTICS</div>
            <div class="insight-text" id="insight3_text">Đang phân tích...</div>
        </div>
    </div>

<!-- ═══════════════════════════════════════════════════════════
     JAVASCRIPT
     ═══════════════════════════════════════════════════════════ -->
<script>
    const RAW_DATA = {data_json_str};
    let GI = {{}};  // Global chart Instances

    const BRAND = {{
        prime: '#F97316', nonPrime: '#9CA3AF',
        palette: ['#10B981','#3B82F6','#F59E0B','#F97316','#EF4444','#8B5CF6'],
        green: '#10B981', red: '#EF4444', blue: '#3B82F6', amber: '#F59E0B'
    }};

    const fmtN  = n => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR  = n => Number(n).toFixed(2);
    const fmtPct = n => Number(n).toFixed(1) + '%';
    const fmtC  = n => "$" + fmtN(n);

    // ── SETUP ──
    function setup() {{
        let cats = new Set();
        RAW_DATA.forEach(d => {{ if (d.crawl_category && d.crawl_category !== 'Khác') cats.add(d.crawl_category); }});
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let o = document.createElement('option');
            o.value = c; o.innerText = c;
            sel.appendChild(o);
        }});
        initCharts();
        applyFilters();
    }}

    // ── APPLY FILTERS ──
    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let metric = document.getElementById('selMetric').value;
        let filtered = RAW_DATA.filter(d => cat === 'ALL' || d.crawl_category === cat);
        updateSection1(filtered, metric);
        updateSection2(filtered, metric);
        updateSection3(filtered, metric);
    }}

    // ══════════════════════════════════════════════
    // SECTION 1: Chiến Lược Định Giá
    // ══════════════════════════════════════════════
    function updateSection1(data, metric) {{
        let vP = metric === 'revenue' ? 'revenue' : 'sales_volume_num';
        let prefix = metric === 'revenue' ? '$' : '';

        // Free = fee==0 or prime, Paid = fee > 0 & not prime
        let freeGroup = data.filter(d => d.is_prime || d.delivery_fee === 0);
        let paidGroup = data.filter(d => !d.is_prime && d.delivery_fee > 0);

        let avgFeeRatio = data.length > 0 ? (data.reduce((a,d) => a + (d.fee_ratio||0), 0) / data.length * 100) : 0;
        let freeAvg = freeGroup.length > 0 ? freeGroup.reduce((a,d) => a + (d[vP]||0), 0) / freeGroup.length : 0;
        let paidAvg = paidGroup.length > 0 ? paidGroup.reduce((a,d) => a + (d[vP]||0), 0) / paidGroup.length : 0;

        let freeRev = freeGroup.reduce((a,d) => a + (d.revenue||0), 0);
        let totalRev = data.reduce((a,d) => a + (d.revenue||0), 0);
        let freeRevPct = totalRev > 0 ? (freeRev / totalRev * 100) : 0;

        let multiplier = paidAvg > 0 ? (freeAvg / paidAvg) : 0;

        document.getElementById('kpi1_fee_ratio').innerText = fmtPct(avgFeeRatio);
        document.getElementById('kpi1_fee_ratio_sub').innerText = avgFeeRatio > 30 ? '⚠ Trên ngưỡng khuyến nghị 30%' : '✓ Dưới ngưỡng khuyến nghị 30%';
        document.getElementById('kpi1_free_sales').innerText = prefix + fmtN(freeAvg);
        document.getElementById('kpi1_free_sales_sub').innerText = freeGroup.length + ' sản phẩm';
        document.getElementById('kpi1_paid_sales').innerText = prefix + fmtN(paidAvg);
        document.getElementById('kpi1_paid_sales_sub').innerText = paidGroup.length + ' sản phẩm';
        document.getElementById('kpi1_rev_share').innerText = fmtPct(freeRevPct);

        // ── Chart: Fee Bins ──
        let bins = [
            {{ label: 'Free (0%)', min:0, max:0.001, sumV:0, cnt:0 }},
            {{ label: '0-15%', min:0.001, max:0.15, sumV:0, cnt:0 }},
            {{ label: '15-30%', min:0.15, max:0.30, sumV:0, cnt:0 }},
            {{ label: '30-50%', min:0.30, max:0.50, sumV:0, cnt:0 }},
            {{ label: '50-100%', min:0.50, max:1.00, sumV:0, cnt:0 }},
            {{ label: '>100%', min:1.00, max:999, sumV:0, cnt:0 }}
        ];
        data.forEach(d => {{
            let r = d.is_prime ? 0 : (d.fee_ratio || 0);
            for (let b of bins) {{
                if (r >= b.min && r < b.max) {{ b.sumV += (d[vP]||0); b.cnt++; break; }}
                if (b.max === 999 && r >= b.min) {{ b.sumV += (d[vP]||0); b.cnt++; break; }}
            }}
        }});

        GI.cFeeBins.data.labels = bins.map(b => b.label);
        GI.cFeeBins.data.datasets[0].data = bins.map(b => b.cnt > 0 ? b.sumV / b.cnt : 0);
        GI.cFeeBins.data.datasets[1].data = bins.map(b => b.cnt);
        GI.cFeeBins.update();

        // ── Chart: Revenue Share Pie ──
        let revBins = [
            {{ label: 'Free Ship / Prime', sum: 0 }},
            {{ label: 'Phí Thấp (< $12)', sum: 0 }},
            {{ label: 'Phí TB ($12-25)', sum: 0 }},
            {{ label: 'Phí Cao ($25-50)', sum: 0 }},
            {{ label: 'Phí Rất Cao (> $50)', sum: 0 }}
        ];
        data.forEach(d => {{
            let rv = d[vP] || 0;
            if (d.is_prime || d.delivery_fee === 0) {{ revBins[0].sum += rv; }}
            else if (d.delivery_fee <= 12) {{ revBins[1].sum += rv; }}
            else if (d.delivery_fee <= 25) {{ revBins[2].sum += rv; }}
            else if (d.delivery_fee <= 50) {{ revBins[3].sum += rv; }}
            else {{ revBins[4].sum += rv; }}
        }});

        GI.cRevShare.data.labels = revBins.map(b => b.label);
        GI.cRevShare.data.datasets[0].data = revBins.map(b => b.sum);
        GI.cRevShare.update();

        // ── Insight 1 ──
        let mName = metric === 'revenue' ? 'doanh thu' : 'doanh số';
        let insight1 = '<strong>Phát hiện chính:</strong> Sản phẩm miễn phí vận chuyển đạt ' + mName + ' trung bình <strong>' + prefix + fmtN(freeAvg) + '</strong>';
        if (multiplier > 1) {{
            insight1 += ', cao gấp <strong>' + fmtR(multiplier) + ' lần</strong> so với nhóm tốn phí ship (' + prefix + fmtN(paidAvg) + ').';
        }} else {{
            insight1 += ' so với ' + prefix + fmtN(paidAvg) + ' của nhóm tốn phí ship.';
        }}
        insight1 += '<br/><strong>Ngưỡng kháng cự:</strong> Tỷ lệ phí ship/giá trung bình đạt <strong>' + fmtPct(avgFeeRatio) + '</strong>';
        insight1 += avgFeeRatio > 30 ? ' — đang ở mức cao, cần chiến lược giảm gánh nặng phí ship.' : ' — vẫn trong ngưỡng chấp nhận.';
        insight1 += '<br/><strong>Đề xuất:</strong> Với nhóm sản phẩm giá thấp (< $25), nên <strong>gộp phí ship vào giá bán</strong> để tạo hiệu ứng Free Ship, vì nhóm Free Ship chiếm <strong>' + fmtPct(freeRevPct) + '</strong> tổng ' + mName + '. Với sản phẩm cao cấp (> $100), có thể <strong>tách rời phí ship</strong> vì khách hàng ít nhạy cảm hơn với phí vận chuyển ở phân khúc này.';
        document.getElementById('insight1_text').innerHTML = insight1;
    }}

    // ══════════════════════════════════════════════
    // SECTION 2: Vai Trò Của Prime
    // ══════════════════════════════════════════════
    function updateSection2(data, metric) {{
        let vP = metric === 'revenue' ? 'revenue' : 'sales_volume_num';

        let primeD = data.filter(d => d.is_prime);
        let nonPrimeD = data.filter(d => !d.is_prime);
        let acD = data.filter(d => d.is_amazon_choice);
        let topD = data.filter(d => d.is_top_seller);
        let botD = data.filter(d => !d.is_top_seller);

        let primeRate = data.length > 0 ? (primeD.length / data.length * 100) : 0;
        let acPrimeRate = acD.length > 0 ? (acD.filter(d => d.is_prime).length / acD.length * 100) : 0;

        let primeAvgSales = primeD.length > 0 ? primeD.reduce((a,d) => a + (d[vP]||0), 0) / primeD.length : 0;
        let nonPrimeAvgSales = nonPrimeD.length > 0 ? nonPrimeD.reduce((a,d) => a + (d[vP]||0), 0) / nonPrimeD.length : 0;
        let salesDiff = primeAvgSales - nonPrimeAvgSales;

        let primeAvgRating = primeD.length > 0 ? primeD.reduce((a,d) => a + (d.rating_val||0), 0) / primeD.length : 0;
        let nonPrimeAvgRating = nonPrimeD.length > 0 ? nonPrimeD.reduce((a,d) => a + (d.rating_val||0), 0) / nonPrimeD.length : 0;
        let ratingDiff = primeAvgRating - nonPrimeAvgRating;

        let prefix = metric === 'revenue' ? '$' : '';

        document.getElementById('kpi2_prime_rate').innerText = fmtPct(primeRate);
        document.getElementById('kpi2_prime_rate_sub').innerText = primeD.length + ' / ' + data.length + ' sản phẩm';
        document.getElementById('kpi2_ac_prime').innerText = fmtPct(acPrimeRate);
        document.getElementById('kpi2_sales_diff').innerText = (salesDiff >= 0 ? '+' : '') + prefix + fmtN(salesDiff);
        document.getElementById('kpi2_sales_diff_sub').innerText = salesDiff >= 0 ? 'Prime cao hơn Non-Prime' : 'Prime thấp hơn Non-Prime';
        document.getElementById('kpi2_rating_diff').innerText = (ratingDiff >= 0 ? '+' : '') + fmtR(ratingDiff);
        document.getElementById('kpi2_rating_diff_sub').innerText = 'Prime: ' + fmtR(primeAvgRating) + ' vs Non-Prime: ' + fmtR(nonPrimeAvgRating);

        // ── Chart: Prime Rate Comparison ──
        let topPrimeRate = topD.length > 0 ? (topD.filter(d => d.is_prime).length / topD.length * 100) : 0;
        let botPrimeRate = botD.length > 0 ? (botD.filter(d => d.is_prime).length / botD.length * 100) : 0;

        GI.cPrimeRate.data.datasets[0].data = [primeRate, acPrimeRate, topPrimeRate, botPrimeRate];
        GI.cPrimeRate.update();

        // ── Chart: Radar Profile ──
        let maxSales = Math.max(primeAvgSales, nonPrimeAvgSales, 1);
        let maxPrice = Math.max(
            primeD.length > 0 ? primeD.reduce((a,d) => a + (d.current_price||0), 0) / primeD.length : 0,
            nonPrimeD.length > 0 ? nonPrimeD.reduce((a,d) => a + (d.current_price||0), 0) / nonPrimeD.length : 0,
            1
        );
        let pAvgPrice = primeD.length > 0 ? primeD.reduce((a,d)=>a+(d.current_price||0),0)/primeD.length : 0;
        let nAvgPrice = nonPrimeD.length > 0 ? nonPrimeD.reduce((a,d)=>a+(d.current_price||0),0)/nonPrimeD.length : 0;
        let pACpct = primeD.length > 0 ? (primeD.filter(d=>d.is_amazon_choice).length/primeD.length*100) : 0;
        let nACpct = nonPrimeD.length > 0 ? (nonPrimeD.filter(d=>d.is_amazon_choice).length/nonPrimeD.length*100) : 0;
        let pFreePct = primeD.length > 0 ? (primeD.filter(d=>d.delivery_fee===0).length/primeD.length*100) : 0;
        let nFreePct = nonPrimeD.length > 0 ? (nonPrimeD.filter(d=>d.delivery_fee===0).length/nonPrimeD.length*100) : 0;

        GI.cRadar.data.datasets[0].data = [
            primeAvgRating / 5 * 100,
            primeAvgSales / maxSales * 100,
            pAvgPrice / maxPrice * 100,
            pACpct,
            pFreePct
        ];
        GI.cRadar.data.datasets[1].data = [
            nonPrimeAvgRating / 5 * 100,
            nonPrimeAvgSales / maxSales * 100,
            nAvgPrice / maxPrice * 100,
            nACpct,
            nFreePct
        ];
        GI.cRadar.update();

        // ── Chart: Prime vs Non-Prime by Category ──
        let catStats = {{}};
        data.forEach(d => {{
            let c = d.crawl_category || 'Khác';
            if (c === 'Khác') return;
            if (!catStats[c]) catStats[c] = {{ pSum:0, pCnt:0, nSum:0, nCnt:0 }};
            if (d.is_prime) {{ catStats[c].pSum += (d[vP]||0); catStats[c].pCnt++; }}
            else {{ catStats[c].nSum += (d[vP]||0); catStats[c].nCnt++; }}
        }});
        let catLabels = Object.keys(catStats).sort();
        GI.cPrimeCat.data.labels = catLabels;
        GI.cPrimeCat.data.datasets[0].data = catLabels.map(c => catStats[c].pCnt > 0 ? catStats[c].pSum / catStats[c].pCnt : 0);
        GI.cPrimeCat.data.datasets[1].data = catLabels.map(c => catStats[c].nCnt > 0 ? catStats[c].nSum / catStats[c].nCnt : 0);
        GI.cPrimeCat.update();

        // ── Insight 2 ──
        let mName = metric === 'revenue' ? 'doanh thu' : 'doanh số';
        let insight2 = '<strong>Phát hiện về Prime:</strong> Prime chỉ chiếm <strong>' + fmtPct(primeRate) + '</strong> tổng sản phẩm (' + primeD.length + '/' + data.length + ')';
        insight2 += ', nhưng trong nhóm Amazon\\'s Choice, tỷ lệ Prime tăng lên <strong>' + fmtPct(acPrimeRate) + '</strong> — gấp <strong>' + fmtR(primeRate > 0 ? acPrimeRate / primeRate : 0) + ' lần</strong>.';
        insight2 += '<br/><strong>Chênh lệch hiệu suất:</strong> ' + mName + ' trung bình Prime = <strong>' + prefix + fmtN(primeAvgSales) + '</strong> vs Non-Prime = <strong>' + prefix + fmtN(nonPrimeAvgSales) + '</strong>';
        if (salesDiff < 0) {{
            insight2 += '. Prime <strong>không đảm bảo doanh số cao hơn</strong> — điều này cho thấy nhãn Prime không phải yếu tố quyết định doanh số, mà là yếu tố gia tăng <em>uy tín và khả năng hiển thị</em>.';
        }} else {{
            insight2 += '. Prime mang lại lợi thế rõ rệt về doanh số.';
        }}
        insight2 += '<br/><strong>Kết luận:</strong> Prime là <strong>"tấm vé ưu tiên"</strong> — tăng khả năng được Amazon đề xuất (gấp ' + fmtR(primeRate > 0 ? acPrimeRate / primeRate : 0) + 'x) — nhưng <strong>không phải "tấm vé bắt buộc"</strong> để doanh số cao. Yếu tố quyết định vẫn là chất lượng sản phẩm, giá cả và đánh giá.';
        document.getElementById('insight2_text').innerHTML = insight2;
    }}

    // ══════════════════════════════════════════════
    // SECTION 3: Tốc Độ Giao Hàng
    // ══════════════════════════════════════════════
    function updateSection3(data, metric) {{
        let vP = metric === 'revenue' ? 'revenue' : 'sales_volume_num';
        let prefix = metric === 'revenue' ? '$' : '';

        let withDays = data.filter(d => d.est_delivery_days != null && d.est_delivery_days > 0);

        let avgDays = withDays.length > 0 ? withDays.reduce((a,d) => a + d.est_delivery_days, 0) / withDays.length : 0;
        let fastGroup = withDays.filter(d => d.est_delivery_days <= 7);
        let slowGroup = withDays.filter(d => d.est_delivery_days > 7);
        let fastPct = withDays.length > 0 ? (fastGroup.length / withDays.length * 100) : 0;

        let fastAvgRating = fastGroup.length > 0 ? fastGroup.reduce((a,d) => a + (d.rating_val||0), 0) / fastGroup.length : 0;
        let slowAvgRating = slowGroup.length > 0 ? slowGroup.reduce((a,d) => a + (d.rating_val||0), 0) / slowGroup.length : 0;
        let ratingGap = fastAvgRating - slowAvgRating;

        // Pearson correlation: delivery_days vs rating
        let corr = pearsonCorr(withDays.map(d => d.est_delivery_days), withDays.map(d => d.rating_val || 0));

        document.getElementById('kpi3_avg_days').innerText = fmtR(avgDays) + ' ngày';
        document.getElementById('kpi3_avg_days_sub').innerText = withDays.length + '/' + data.length + ' SP có dữ liệu giao hàng';
        document.getElementById('kpi3_fast_pct').innerText = fmtPct(fastPct);
        document.getElementById('kpi3_rating_gap').innerText = (ratingGap >= 0 ? '+' : '') + fmtR(ratingGap);
        document.getElementById('kpi3_rating_gap_sub').innerText = 'Nhanh: ' + fmtR(fastAvgRating) + ' vs Chậm: ' + fmtR(slowAvgRating);
        document.getElementById('kpi3_corr').innerText = fmtR(corr);

        // ── Chart: Delivery Impact (Dual Axis) ──
        let dayBins = [
            {{ label: '1-3 ngày', min:1, max:3 }},
            {{ label: '4-5 ngày', min:4, max:5 }},
            {{ label: '6-7 ngày', min:6, max:7 }},
            {{ label: '8-10 ngày', min:8, max:10 }},
            {{ label: '11-14 ngày', min:11, max:14 }},
            {{ label: '15+ ngày', min:15, max:999 }}
        ];
        let dbStats = dayBins.map(b => ({{ sumV:0, sumR:0, cnt:0 }}));
        withDays.forEach(d => {{
            for (let i = 0; i < dayBins.length; i++) {{
                if (d.est_delivery_days >= dayBins[i].min && d.est_delivery_days <= dayBins[i].max) {{
                    dbStats[i].sumV += (d[vP]||0);
                    dbStats[i].sumR += (d.rating_val||0);
                    dbStats[i].cnt++;
                    break;
                }}
            }}
        }});

        GI.cDeliveryImpact.data.labels = dayBins.map(b => b.label);
        GI.cDeliveryImpact.data.datasets[0].data = dbStats.map(s => s.cnt > 0 ? s.sumV / s.cnt : 0);
        GI.cDeliveryImpact.data.datasets[1].data = dbStats.map(s => s.cnt > 0 ? s.sumR / s.cnt : 0);
        GI.cDeliveryImpact.update();

        // ── Heatmap Table ──
        let hmDays = ['1-3 ngày', '4-7 ngày', '8-14 ngày', '15+ ngày'];
        let hmDayRanges = [[1,3],[4,7],[8,14],[15,999]];
        let hmPrices = ['< $25', '$25-50', '$50-100', '> $100'];
        let hmPriceRanges = [[0,25],[25,50],[50,100],[100,999999]];

        let hmMatrix = {{}};
        hmDays.forEach((d,di) => {{
            hmMatrix[d] = {{}};
            hmPrices.forEach((p,pi) => {{
                hmMatrix[d][p] = {{ sumR:0, sumV:0, cnt:0 }};
            }});
        }});

        withDays.forEach(d => {{
            let dIdx = -1;
            for (let i = 0; i < hmDayRanges.length; i++) {{
                if (d.est_delivery_days >= hmDayRanges[i][0] && d.est_delivery_days <= hmDayRanges[i][1]) {{ dIdx = i; break; }}
            }}
            let pIdx = -1;
            let pr = d.current_price || 0;
            for (let i = 0; i < hmPriceRanges.length; i++) {{
                if (pr >= hmPriceRanges[i][0] && pr < hmPriceRanges[i][1]) {{ pIdx = i; break; }}
            }}
            if (dIdx >= 0 && pIdx >= 0) {{
                hmMatrix[hmDays[dIdx]][hmPrices[pIdx]].sumR += (d.rating_val||0);
                hmMatrix[hmDays[dIdx]][hmPrices[pIdx]].sumV += (d[vP]||0);
                hmMatrix[hmDays[dIdx]][hmPrices[pIdx]].cnt++;
            }}
        }});

        let hmHTML = '<table class="hm-table"><tr><th style="min-width:90px;">Tốc Độ Giao</th>';
        hmPrices.forEach(p => {{ hmHTML += '<th>' + p + '</th>'; }});
        hmHTML += '</tr>';

        hmDays.forEach(d => {{
            hmHTML += '<tr><td class="hm-row-label">' + d + '</td>';
            hmPrices.forEach(p => {{
                let cell = hmMatrix[d][p];
                let avgR = cell.cnt > 0 ? cell.sumR / cell.cnt : 0;
                let avgV = cell.cnt > 0 ? cell.sumV / cell.cnt : 0;
                let bg = getRatingBg(avgR);
                hmHTML += '<td style="background:' + bg + ';">';
                if (cell.cnt > 0) {{
                    hmHTML += '<div class="hm-rating">⭐ ' + fmtR(avgR) + '</div>';
                    hmHTML += '<div class="hm-sales">' + prefix + fmtN(avgV) + '</div>';
                    hmHTML += '<div class="hm-count">n=' + cell.cnt + '</div>';
                }} else {{
                    hmHTML += '<div class="hm-count" style="color:#D6D3D1;">—</div>';
                }}
                hmHTML += '</td>';
            }});
            hmHTML += '</tr>';
        }});
        hmHTML += '</table>';
        document.getElementById('heatmapContainer').innerHTML = hmHTML;

        // ── Chart: Category Delivery Performance ──
        let catDel = {{}};
        withDays.forEach(d => {{
            let c = d.crawl_category || 'Khác';
            if (c === 'Khác') return;
            if (!catDel[c]) catDel[c] = {{ fSum:0, fCnt:0, sSum:0, sCnt:0 }};
            if (d.est_delivery_days <= 7) {{ catDel[c].fSum += (d[vP]||0); catDel[c].fCnt++; }}
            else {{ catDel[c].sSum += (d[vP]||0); catDel[c].sCnt++; }}
        }});
        let cdLabels = Object.keys(catDel).sort();
        GI.cCatDelivery.data.labels = cdLabels;
        GI.cCatDelivery.data.datasets[0].data = cdLabels.map(c => catDel[c].fCnt > 0 ? catDel[c].fSum / catDel[c].fCnt : 0);
        GI.cCatDelivery.data.datasets[1].data = cdLabels.map(c => catDel[c].sCnt > 0 ? catDel[c].sSum / catDel[c].sCnt : 0);
        GI.cCatDelivery.update();

        // ── Insight 3 ──
        let mName = metric === 'revenue' ? 'doanh thu' : 'doanh số';
        let fastAvgSales = fastGroup.length > 0 ? fastGroup.reduce((a,d) => a + (d[vP]||0), 0) / fastGroup.length : 0;
        let slowAvgSales = slowGroup.length > 0 ? slowGroup.reduce((a,d) => a + (d[vP]||0), 0) / slowGroup.length : 0;

        let insight3 = '<strong>Phát hiện chính:</strong> Thời gian giao hàng trung bình đạt <strong>' + fmtR(avgDays) + ' ngày</strong>. ';
        insight3 += 'Nhóm giao nhanh (≤7 ngày) chiếm <strong>' + fmtPct(fastPct) + '</strong> và đạt rating TB <strong>' + fmtR(fastAvgRating) + '</strong>';
        insight3 += ' vs nhóm giao chậm (>7 ngày) chỉ đạt <strong>' + fmtR(slowAvgRating) + '</strong>';
        insight3 += ' (chênh lệch <strong>' + (ratingGap >= 0 ? '+' : '') + fmtR(ratingGap) + ' ⭐</strong>).';
        insight3 += '<br/><strong>Tương quan:</strong> Hệ số Pearson giữa ngày giao và rating = <strong>' + fmtR(corr) + '</strong>';
        if (corr < -0.03) {{
            insight3 += ' (tương quan âm) — giao hàng chậm <strong>làm giảm đánh giá</strong> của khách hàng.';
        }} else if (corr > 0.03) {{
            insight3 += ' (tương quan dương nhẹ) — thời gian giao không ảnh hưởng tiêu cực rõ rệt.';
        }} else {{
            insight3 += ' (gần 0) — tương quan yếu, nhưng sự chênh lệch rating giữa nhóm nhanh/chậm vẫn có ý nghĩa thực tiễn.';
        }}
        insight3 += '<br/><strong>Đề xuất:</strong> Nhà bán hàng nên cam kết giao trong <strong>≤7 ngày</strong> — khoảng thời gian tối ưu cho cả rating và ' + mName + '. ';
        insight3 += 'Đối với các category có chênh lệch lớn giữa giao nhanh/chậm, nên <strong>ưu tiên đầu tư logistics</strong> hoặc sử dụng <strong>FBA (Fulfilled by Amazon)</strong> để đảm bảo tốc độ giao hàng ổn định.';
        document.getElementById('insight3_text').innerHTML = insight3;
    }}

    // ── UTILITIES ──
    function pearsonCorr(x, y) {{
        let n = x.length;
        if (n < 2) return 0;
        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
        for (let i = 0; i < n; i++) {{
            sumX += x[i]; sumY += y[i];
            sumXY += x[i]*y[i]; sumX2 += x[i]*x[i]; sumY2 += y[i]*y[i];
        }}
        let denom = Math.sqrt((n*sumX2 - sumX*sumX) * (n*sumY2 - sumY*sumY));
        return denom === 0 ? 0 : (n*sumXY - sumX*sumY) / denom;
    }}

    function getRatingBg(r) {{
        if (r >= 4.5) return 'rgba(16, 185, 129, 0.18)';
        if (r >= 4.3) return 'rgba(245, 158, 11, 0.14)';
        if (r >= 4.0) return 'rgba(249, 115, 22, 0.14)';
        if (r > 0) return 'rgba(239, 68, 68, 0.12)';
        return 'transparent';
    }}

    // ══════════════════════════════════════════════
    // INIT CHARTS
    // ══════════════════════════════════════════════
    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.size = 11;

        let metricAxisFmt = function(val) {{
            let m = document.getElementById('selMetric').value;
            if (m === 'revenue') {{ return val >= 1000 ? '$' + (val/1000).toFixed(0) + 'K' : '$' + val; }}
            return val >= 1000 ? (val/1000).toFixed(0) + 'K' : val;
        }};
        let metricTooltipFmt = function(ctx) {{
            let m = document.getElementById('selMetric').value;
            return (m === 'revenue' ? '$' : '') + fmtN(ctx.raw);
        }};

        // ── S1: Fee Bins (Combo bar + line) ──
        GI.cFeeBins = new Chart(document.getElementById('cFeeBins'), {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Doanh Số / Doanh Thu TB',
                        data: [],
                        backgroundColor: ['rgba(16,185,129,0.75)', 'rgba(239,68,68,0.65)', 'rgba(249,115,22,0.65)', 'rgba(245,158,11,0.65)', 'rgba(59,130,246,0.65)', 'rgba(139,92,246,0.65)'],
                        borderRadius: 5,
                        barPercentage: 0.7,
                        yAxisID: 'y',
                        order: 2
                    }},
                    {{
                        label: 'Số Lượng Sản Phẩm',
                        data: [],
                        type: 'line',
                        borderColor: '#78716C',
                        backgroundColor: 'rgba(120,113,108,0.1)',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointBackgroundColor: '#78716C',
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y1',
                        order: 1
                    }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle', padding: 12 }} }},
                    tooltip: {{ callbacks: {{ label: function(ctx) {{
                        if (ctx.datasetIndex === 0) return ' ' + metricTooltipFmt(ctx);
                        return ' ' + fmtN(ctx.raw) + ' sản phẩm';
                    }} }} }}
                }},
                scales: {{
                    x: {{ grid: {{ display: false }} }},
                    y: {{ position: 'left', grid: {{ borderDash: [3,3] }}, ticks: {{ callback: metricAxisFmt }} }},
                    y1: {{ position: 'right', grid: {{ drawOnChartArea: false }}, ticks: {{ callback: v => fmtN(v) }},
                        title: {{ display: true, text: 'Số SP', font: {{ size: 10 }} }} }}
                }}
            }}
        }});

        // ── S1: Revenue Share (Doughnut) ──
        GI.cRevShare = new Chart(document.getElementById('cRevShare'), {{
            type: 'doughnut',
            data: {{
                labels: [],
                datasets: [{{ data: [], backgroundColor: BRAND.palette.concat(['#D4D4D8']), borderWidth: 1, hoverOffset: 6 }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                cutout: '55%',
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle', padding: 10, font: {{ size: 10 }} }} }},
                    tooltip: {{ callbacks: {{ label: function(ctx) {{
                        let total = ctx.dataset.data.reduce((a,b)=>a+b, 0);
                        let pct = total > 0 ? (ctx.raw/total*100).toFixed(1) : 0;
                        let m = document.getElementById('selMetric').value;
                        return ' ' + (m==='revenue'?'$':'') + fmtN(ctx.raw) + ' (' + pct + '%)';
                    }} }} }}
                }}
            }}
        }});

        // ── S2: Prime Rate Comparison ──
        GI.cPrimeRate = new Chart(document.getElementById('cPrimeRate'), {{
            type: 'bar',
            data: {{
                labels: ['Tổng Thể', 'Amazon\\'s Choice', 'Top 20% Sales', 'Bottom 80%'],
                datasets: [{{
                    label: 'Tỷ Lệ Prime (%)',
                    data: [0, 0, 0, 0],
                    backgroundColor: [BRAND.nonPrime, BRAND.green, BRAND.prime, '#D4D4D8'],
                    borderRadius: 5,
                    barPercentage: 0.6
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ callbacks: {{ label: ctx => ' ' + fmtR(ctx.raw) + '%' }} }}
                }},
                scales: {{
                    x: {{ grid: {{ borderDash: [3,3] }}, ticks: {{ callback: v => v + '%' }},
                        title: {{ display: true, text: 'Tỷ lệ Prime (%)', font: {{ size: 10 }} }} }},
                    y: {{ grid: {{ display: false }} }}
                }}
            }}
        }});

        // ── S2: Radar Profile ──
        GI.cRadar = new Chart(document.getElementById('cRadar'), {{
            type: 'radar',
            data: {{
                labels: ['Rating', 'Doanh Số', 'Giá TB', 'Amazon Choice %', 'Free Ship %'],
                datasets: [
                    {{
                        label: 'Prime',
                        data: [0,0,0,0,0],
                        borderColor: BRAND.prime,
                        backgroundColor: 'rgba(249,115,22,0.15)',
                        pointBackgroundColor: BRAND.prime,
                        pointRadius: 3,
                        borderWidth: 2
                    }},
                    {{
                        label: 'Non-Prime',
                        data: [0,0,0,0,0],
                        borderColor: BRAND.nonPrime,
                        backgroundColor: 'rgba(156,163,175,0.12)',
                        pointBackgroundColor: BRAND.nonPrime,
                        pointRadius: 3,
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle', padding: 12 }} }},
                    tooltip: {{ callbacks: {{ label: ctx => ' ' + ctx.dataset.label + ': ' + fmtR(ctx.raw) }} }}
                }},
                scales: {{
                    r: {{
                        min: 0, max: 100,
                        ticks: {{ stepSize: 25, display: false }},
                        grid: {{ color: '#E7E5E4' }},
                        angleLines: {{ color: '#E7E5E4' }},
                        pointLabels: {{ font: {{ size: 10, weight: '600' }} }}
                    }}
                }}
            }}
        }});

        // ── S2: Prime by Category ──
        GI.cPrimeCat = new Chart(document.getElementById('cPrimeCat'), {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: 'Prime', data: [], backgroundColor: BRAND.prime, borderRadius: 4, barPercentage: 0.7 }},
                    {{ label: 'Non-Prime', data: [], backgroundColor: BRAND.nonPrime, borderRadius: 4, barPercentage: 0.7 }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top', labels: {{ usePointStyle: true, pointStyle: 'circle' }} }},
                    tooltip: {{ callbacks: {{ label: metricTooltipFmt }} }}
                }},
                scales: {{
                    x: {{ grid: {{ borderDash: [3,3] }}, ticks: {{ callback: metricAxisFmt }} }},
                    y: {{ grid: {{ display: false }} }}
                }}
            }}
        }});

        // ── S3: Delivery Impact (Dual Axis) ──
        GI.cDeliveryImpact = new Chart(document.getElementById('cDeliveryImpact'), {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Doanh Số / Doanh Thu TB',
                        data: [],
                        backgroundColor: 'rgba(59,130,246,0.65)',
                        borderRadius: 5,
                        barPercentage: 0.6,
                        yAxisID: 'y',
                        order: 2
                    }},
                    {{
                        label: 'Rating TB',
                        data: [],
                        type: 'line',
                        borderColor: BRAND.primary || '#F97316',
                        backgroundColor: 'rgba(249,115,22,0.1)',
                        borderWidth: 2.5,
                        pointRadius: 5,
                        pointBackgroundColor: '#F97316',
                        fill: false,
                        tension: 0.3,
                        yAxisID: 'y1',
                        order: 1
                    }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle', padding: 12 }} }},
                    tooltip: {{ callbacks: {{ label: function(ctx) {{
                        if (ctx.datasetIndex === 0) return ' ' + metricTooltipFmt(ctx);
                        return ' Rating: ' + fmtR(ctx.raw) + ' ⭐';
                    }} }} }}
                }},
                scales: {{
                    x: {{ grid: {{ display: false }} }},
                    y: {{ position: 'left', grid: {{ borderDash: [3,3] }}, ticks: {{ callback: metricAxisFmt }},
                        title: {{ display: true, text: 'Doanh số / Doanh thu', font: {{ size: 10 }} }} }},
                    y1: {{ position: 'right', grid: {{ drawOnChartArea: false }},
                        min: 3.5, max: 5.0,
                        ticks: {{ callback: v => v.toFixed(1) + ' ⭐' }},
                        title: {{ display: true, text: 'Rating', font: {{ size: 10 }} }} }}
                }}
            }}
        }});

        // ── S3: Category Delivery ──
        GI.cCatDelivery = new Chart(document.getElementById('cCatDelivery'), {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: 'Giao Nhanh (≤7 ngày)', data: [], backgroundColor: BRAND.green, borderRadius: 4, barPercentage: 0.7 }},
                    {{ label: 'Giao Chậm (>7 ngày)', data: [], backgroundColor: BRAND.red, borderRadius: 4, barPercentage: 0.7 }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top', labels: {{ usePointStyle: true, pointStyle: 'circle' }} }},
                    tooltip: {{ callbacks: {{ label: metricTooltipFmt }} }}
                }},
                scales: {{
                    x: {{ grid: {{ borderDash: [3,3] }}, ticks: {{ callback: metricAxisFmt }} }},
                    y: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
    """

    components.html(html_code, height=4200, scrolling=False)
