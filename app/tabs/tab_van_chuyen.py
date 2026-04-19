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

    # --- crawl_category: DEEP sub-category mapping ---
    CATEGORY_MAP = {
        "electronics_laptops": "Laptop",
        "electronics_tablets": "Máy Tính Bảng",
        "electronics_smartphones": "Điện Thoại",
        "electronics_monitors": "Màn Hình",
        "electronics_headphones": "Tai Nghe",
        "electronics_keyboards": "Bàn Phím",
        "electronics_storage_ssd": "Ổ Cứng & SSD",
        "electronics_networking": "Thiết Bị Mạng",
        "electronics_gaming_consoles": "Máy Chơi Game",
        "home_kitchen_appliances": "Thiết Bị Bếp",
        "home_cleaning": "Dụng Cụ Vệ Sinh",
        "home_air_quality": "Máy Lọc Khí",
        "home_furniture": "Nội Thất",
        "office_supplies": "Văn Phòng Phẩm",
        "office_stationery": "Dụng Cụ VP",
        "fashion_mens": "Thời Trang Nam",
        "fashion_womens": "Thời Trang Nữ",
        "fashion_shoes": "Giày Dép",
        "fashion_bags": "Túi Xách",
        "beauty_skincare": "Chăm Sóc Da",
        "beauty_makeup": "Trang Điểm",
        "health_personal_care": "Chăm Sóc Cá Nhân",
        "health_supplements": "TPCN & Vitamin",
        "baby_products": "Sản Phẩm Cho Bé",
        "toys_games": "Đồ Chơi & Game",
        "sports_outdoors": "Thể Thao Ngoài Trời",
        "sports_fitness": "Dụng Cụ Gym",
        "pet_supplies": "Thú Cưng",
        "automotive_accessories": "Phụ Kiện Ô Tô",
        "tools_home_improvement": "Dụng Cụ Sửa Nhà",
    }

    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"

    df["crawl_category"] = df["crawl_category"].fillna("Không rõ").map(CATEGORY_MAP).fillna("Khác")

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
        m = re.search(r'\w+,\s*Apr\s+(\d+)', s)
        if m:
            return max(1, int(m.group(1)) - 6)
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
            --primary: #F97316; --primary-light: #FDBA74; --secondary: #3B82F6;
            --dark: #9A3412; --bg: #FEF3E2; --card-bg: #FFFFFF;
            --text-primary: #1C1917; --text-secondary: #78716C;
            --border-radius: 10px; --font-family: 'Inter', sans-serif;
            --success: #10B981; --danger: #EF4444; --warning: #F59E0B;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.06); --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg); font-family: var(--font-family); color: var(--text-primary); padding: 14px 18px; line-height: 1.5; }}

        /* ── Section Wrapper & Sticky Header ── */
        .section-wrapper {{ position: relative; margin-top: 24px; }}
        .section-sticky {{
            position: relative; z-index: 100;
            background: var(--bg); padding: 8px 0 6px 0;
            border-bottom: 2px solid #FDBA74;
            margin-bottom: 14px;
            transition: box-shadow 0.15s ease;
            will-change: transform;
        }}
        .section-sticky.is-stuck {{
            box-shadow: 0 3px 10px rgba(154, 52, 18, 0.15);
        }}
        .section-title-row {{
            display: flex; align-items: center; justify-content: space-between; gap: 10px;
        }}
        .section-title {{
            display: flex; align-items: center; gap: 7px;
            font-size: 12px; font-weight: 800; color: var(--dark); text-transform: uppercase; letter-spacing: 0.3px;
            white-space: nowrap; flex-shrink: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
        }}
        .section-title .num {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; border-radius: 50%; background: var(--primary);
            color: white; font-size: 12px; font-weight: 700; flex-shrink: 0;
        }}
        .header-filters {{
            display: flex; align-items: center; gap: 10px; flex-shrink: 0;
        }}
        .hf-item {{ display: flex; align-items: center; gap: 4px; }}
        .hf-label {{ font-size: 9.5px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; white-space: nowrap; }}
        select {{
            padding: 5px 8px; border: 1px solid #D6D3D1; border-radius: 5px;
            font-family: inherit; font-size: 11px; color: var(--text-primary);
            outline: none; cursor: pointer; background: white;
        }}
        select:focus {{ border-color: var(--primary); box-shadow: 0 0 0 2px rgba(249,115,22,0.15); }}

        /* ── Objective & Concept Cards ── */
        .obj-card {{
            background: linear-gradient(135deg, #FFFAF5 0%, #FFF7ED 100%);
            border: 1px solid #FED7AA; border-radius: var(--border-radius);
            padding: 16px 20px; margin-bottom: 12px;
        }}
        .obj-title {{
            font-size: 12px; font-weight: 700; color: var(--dark); text-transform: uppercase;
            margin-bottom: 5px; display: flex; align-items: center; gap: 6px;
        }}
        .obj-text {{
            font-size: 12.5px; line-height: 1.65; color: #44403C;
        }}
        .obj-text strong {{ color: var(--dark); font-weight: 600; }}

        details.concept-panel {{
            margin-top: 10px; border: 1px solid #E7E5E4; border-radius: 8px; overflow: hidden;
        }}
        details.concept-panel > summary {{
            padding: 8px 14px; background: #F5F5F4; font-size: 11.5px; font-weight: 700;
            color: var(--dark); cursor: pointer; list-style: none; user-select: none;
        }}
        details.concept-panel > summary::-webkit-details-marker {{ display: none; }}
        details.concept-panel > summary::before {{ content: '▸ '; }}
        details.concept-panel[open] > summary::before {{ content: '▾ '; }}
        .concept-list {{ padding: 10px 14px; display: flex; flex-direction: column; gap: 6px; background: #FAFAF9; }}
        .concept-item {{
            padding: 8px 12px; background: white; border-radius: 6px;
            font-size: 11.5px; line-height: 1.7; border-left: 3px solid var(--primary-light);
        }}
        .concept-var {{
            font-family: 'Consolas', 'SF Mono', monospace; font-weight: 700; color: var(--dark);
            background: #FEF3C7; padding: 1px 5px; border-radius: 3px; font-size: 10.5px;
        }}
        .concept-tag {{
            display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 9.5px; font-weight: 600;
        }}
        .concept-tag.green {{ background: #D1FAE5; color: #065F46; }}
        .concept-tag.amber {{ background: #FEF3C7; color: #92400E; }}
        .concept-tag.red {{ background: #FEE2E2; color: #991B1B; }}

        /* ── KPI Cards ── */
        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; }}
        .kpi-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 12px 14px;
            box-shadow: var(--shadow-sm); border-left: 4px solid var(--primary);
            display: flex; flex-direction: column; gap: 1px; transition: transform 0.15s ease;
        }}
        .kpi-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
        .kpi-title {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.3px; }}
        .kpi-value {{ font-size: 20px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }}
        .kpi-sub {{ font-size: 9.5px; color: var(--text-secondary); font-weight: 500; }}
        .kpi-card.c-green {{ border-left-color: var(--success); }}
        .kpi-card.c-blue {{ border-left-color: var(--secondary); }}
        .kpi-card.c-red {{ border-left-color: var(--danger); }}
        .kpi-card.c-amber {{ border-left-color: var(--warning); }}

        /* ── Chart Cards ── */
        .chart-row {{ display: flex; gap: 14px; margin-bottom: 14px; align-items: stretch; }}
        .chart-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 16px;
            box-shadow: var(--shadow-sm); display: flex; flex-direction: column; flex: 1; min-width: 0;
        }}
        .chart-header {{ margin-bottom: 10px; }}
        .chart-title {{ font-size: 12.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }}
        .chart-subtitle {{ font-size: 10.5px; color: var(--text-secondary); line-height: 1.4; }}
        .chart-wrapper {{ position: relative; width: 100%; flex-grow: 1; min-height: 280px; }}

        /* ── Insight Box ── */
        .insight-box {{
            background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
            border: 1px solid #A7F3D0; border-left: 4px solid var(--success);
            border-radius: var(--border-radius); padding: 14px 18px; margin-bottom: 6px;
            display: flex; gap: 10px; align-items: flex-start;
        }}
        .insight-box.warn {{
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border-color: #FDE68A; border-left-color: var(--warning);
        }}
        .insight-icon {{ font-size: 18px; flex-shrink: 0; margin-top: 1px; }}
        .insight-content {{ flex: 1; }}
        .insight-label {{ font-size: 10.5px; font-weight: 700; color: var(--success); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }}
        .insight-box.warn .insight-label {{ color: #B45309; }}
        .insight-text {{ font-size: 12px; line-height: 1.7; color: #374151; }}
        .insight-text strong {{ color: var(--dark); }}

        /* ── Heatmap Table ── */
        .hm-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
        .hm-table th {{
            background: #F5F5F4; padding: 8px 6px; text-align: center;
            font-weight: 700; color: var(--text-secondary); font-size: 10.5px;
            text-transform: uppercase; border: 1px solid #E7E5E4;
        }}
        .hm-table td {{
            padding: 10px 8px; text-align: center; border: 1px solid #E7E5E4;
            vertical-align: middle;
        }}
        .hm-rating {{ font-weight: 700; font-size: 13px; color: var(--text-primary); }}
        .hm-sales {{ font-size: 10.5px; color: var(--text-secondary); margin-top: 1px; }}
        .hm-count {{ font-size: 9.5px; color: #A8A29E; margin-top: 1px; }}
        .hm-row-label {{ text-align: left !important; font-weight: 600; color: var(--text-primary); background: #FAFAF9 !important; white-space: nowrap; }}
    </style>
</head>
<body>

    <!-- ═══ GLOBAL OVERVIEW ═══ -->
    <div class="obj-card" style="margin-bottom: 20px;">
        <div class="obj-title">📍 TỔNG QUAN MỤC TIÊU PHÂN TÍCH TAB VẬN CHUYỂN</div>
        <div class="obj-text">
            Tab này phân tích <strong>3 khía cạnh chiến lược</strong> của hoạt động vận chuyển:
            <strong>(1)</strong> Tương quan phí ship/giá sản phẩm với doanh số → chiến lược định giá;
            <strong>(2)</strong> Vai trò nhãn Prime trong sản phẩm nổi bật;
            <strong>(3)</strong> Tác động tốc độ giao hàng đến rating & doanh số → chiến lược logistics.
            <em style="font-size:11px; color:var(--text-secondary);"> Mỗi mục tiêu có bộ lọc riêng để phân tích độc lập theo chỉ số hiệu suất và danh mục sản phẩm.</em>
        </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         SECTION 1: CHIẾN LƯỢC ĐỊNH GIÁ VẬN CHUYỂN
         ═══════════════════════════════════════════════════════════ -->
    <div class="section-wrapper">
    <div class="section-sticky">
        <div class="section-title-row">
            <div class="section-title"><span class="num">1</span> CHIẾN LƯỢC ĐỊNH GIÁ PHÍ VẬN CHUYỂN</div>
            <div class="header-filters">
                <div class="hf-item"><span class="hf-label">Chỉ Số:</span>
                    <select id="selMetric1" onchange="applySection1()">
                        <option value="sales">Số Lượng Bán Ra</option>
                        <option value="revenue">Doanh Thu ($)</option>
                    </select>
                </div>
                <div class="hf-item"><span class="hf-label">Danh Mục:</span>
                    <select id="selCat1" onchange="applySection1()"><option value="ALL">Tất Cả Danh Mục</option></select>
                </div>
            </div>
        </div>
    </div>

    <div class="obj-card">
        <div class="obj-title">🎯 Mục tiêu phân tích</div>
        <div class="obj-text">
            Đánh giá mối tương quan giữa <strong>tỷ lệ phí vận chuyển trên giá trị sản phẩm (Shipping Fee / Price)</strong>
            với <strong>khối lượng bán ra (Sales Volume)</strong>. Xác định ngưỡng phí ship tối đa mà khách hàng chấp nhận,
            từ đó đề xuất chiến lược: <em>gộp phí ship vào giá bán (freeship ảo)</em> hay <em>tách rời phí ship minh bạch</em>.
        </div>
        <details class="concept-panel" open>
            <summary>📚 Giải thích các biến & khái niệm liên quan</summary>
            <div class="concept-list">
                <div class="concept-item">
                    <span class="concept-var">delivery_fee</span> <strong>(Phí Vận Chuyển)</strong> — Chi phí giao hàng hiển thị trên trang sản phẩm Amazon, tính bằng USD. Bao gồm cước vận chuyển thực tế + phí xử lý. Sản phẩm Prime hoặc đơn hàng từ $35 trở lên thường được <strong>miễn phí ship</strong>.
                </div>
                <div class="concept-item">
                    <span class="concept-var">price</span> <strong>(Giá Bán Hiện Tại)</strong> — Giá niêm yết của sản phẩm trên Amazon tại thời điểm crawl data (sau khi đã áp dụng khuyến mãi, coupon). Đây là giá khách hàng thực sự phải trả cho sản phẩm (chưa tính phí ship).
                </div>
                <div class="concept-item">
                    <span class="concept-var">fee_ratio</span> <strong>(Tỷ Lệ Phí Ship / Giá)</strong> — = <code>delivery_fee ÷ price × 100%</code>. Đo lường "gánh nặng phí ship" so với giá trị sản phẩm. <span class="concept-tag green">0%</span> = Free Ship. <span class="concept-tag amber">&lt;30%</span> = chấp nhận được. <span class="concept-tag red">&gt;50%</span> = rất cao, phí ship đắt hơn nửa giá sản phẩm.
                </div>
                <div class="concept-item">
                    <span class="concept-var">sales_volume_num</span> <strong>(Số Lượng Đã Bán)</strong> — Ước tính số lượng sản phẩm đã bán, trích xuất từ label "X+ bought in past month" trên Amazon. Phản ánh sức mua của thị trường.
                </div>
                <div class="concept-item">
                    <span class="concept-var">revenue</span> <strong>(Doanh Thu Ước Tính)</strong> — = <code>sales_volume_num × price</code>. Tổng doanh thu ước tính của sản phẩm. <em>Lưu ý: đây là ước tính, không phải doanh thu chính xác từ Amazon.</em>
                </div>
                <div class="concept-item">
                    <strong>🔬 Phương pháp:</strong> Chia sản phẩm thành các nhóm (bins) theo tỷ lệ <code>fee_ratio</code>, sau đó so sánh doanh số/doanh thu trung bình giữa các nhóm. Xác định <strong>ngưỡng kháng cự</strong> (resistance threshold) = mức fee_ratio mà tại đó doanh số bắt đầu sụt giảm mạnh.
                </div>
            </div>
        </details>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Tỷ Lệ Phí Ship / Giá TB</div>
            <div class="kpi-value" id="k1_fr">0%</div>
            <div class="kpi-sub" id="k1_fr_s"></div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-title" id="k1_t2">Doanh Số TB — Nhóm Free Ship</div>
            <div class="kpi-value" id="k1_free">0</div>
            <div class="kpi-sub" id="k1_free_s"></div>
        </div>
        <div class="kpi-card c-red">
            <div class="kpi-title" id="k1_t3">Doanh Số TB — Nhóm Tốn Phí Ship</div>
            <div class="kpi-value" id="k1_paid">0</div>
            <div class="kpi-sub" id="k1_paid_s"></div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Revenue Share — Free Ship</div>
            <div class="kpi-value" id="k1_rev">0%</div>
            <div class="kpi-sub">Tỷ trọng doanh thu nhóm miễn phí ship</div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card" style="flex: 1.4;">
            <div class="chart-header">
                <div class="chart-title">Biến Động Hiệu Suất Theo Mức Tỷ Lệ Phí Ship / Giá</div>
                <div class="chart-subtitle">Bars = hiệu suất TB mỗi bin · Line = số lượng SP · Xác định ngưỡng kháng cự</div>
            </div>
            <div class="chart-wrapper"><canvas id="cFeeBins"></canvas></div>
        </div>
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div class="chart-title">Phân Bổ Hiệu Suất Theo Chiến Lược Phí Ship</div>
                <div class="chart-subtitle">So sánh tỷ trọng giữa Free Ship và các mức phí ship</div>
            </div>
            <div class="chart-wrapper"><canvas id="cRevShare"></canvas></div>
        </div>
    </div>

    <div class="insight-box" id="insightBox1">
        <div class="insight-icon">💡</div>
        <div class="insight-content">
            <div class="insight-label">KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC ĐỊNH GIÁ</div>
            <div class="insight-text" id="ins1">Đang phân tích...</div>
        </div>
    </div>
    </div><!-- /section-wrapper 1 -->

    <!-- ═══════════════════════════════════════════════════════════
         SECTION 2: VAI TRÒ CỦA PRIME
         ═══════════════════════════════════════════════════════════ -->
    <div class="section-wrapper">
    <div class="section-sticky">
        <div class="section-title-row">
            <div class="section-title"><span class="num">2</span> VAI TRÒ PRIME VỚI SẢN PHẨM NỔI BẬT</div>
            <div class="header-filters">
                <div class="hf-item"><span class="hf-label">Chỉ Số:</span>
                    <select id="selMetric2" onchange="applySection2()">
                        <option value="sales">Số Lượng Bán Ra</option>
                        <option value="revenue">Doanh Thu ($)</option>
                    </select>
                </div>
                <div class="hf-item"><span class="hf-label">Danh Mục:</span>
                    <select id="selCat2" onchange="applySection2()"><option value="ALL">Tất Cả Danh Mục</option></select>
                </div>
            </div>
        </div>
    </div>

    <div class="obj-card">
        <div class="obj-title">🎯 Mục tiêu phân tích</div>
        <div class="obj-text">
            Phân tích xác suất lọt vào nhóm <strong>sản phẩm nổi bật</strong> và chênh lệch hiệu suất giữa nhóm
            <strong>Prime</strong> vs <strong>Non-Prime</strong>. Xác nhận liệu Prime có phải là <em>"tấm vé bắt buộc"</em>
            để một sản phẩm định vị top đầu ngành hàng.
        </div>
        <details class="concept-panel" open>
            <summary>📚 Giải thích các biến & khái niệm liên quan</summary>
            <div class="concept-list">
                <div class="concept-item">
                    <span class="concept-var">is_prime</span> <strong>(Nhãn Prime)</strong> —
                    <strong>Amazon Prime</strong> là chương trình thành viên trả phí ($14.99/tháng hoặc $139/năm) của Amazon.
                    Sản phẩm có nhãn Prime được:<br/>
                    ✅ Giao hàng miễn phí 1-2 ngày cho thành viên Prime<br/>
                    ✅ Xử lý bởi kho Amazon (<strong>FBA — Fulfilled by Amazon</strong>)<br/>
                    ✅ Hỗ trợ trả hàng miễn phí & dịch vụ khách hàng Amazon<br/>
                    <strong>Cách để có nhãn Prime:</strong> Người bán phải đăng ký <em>FBA</em> (gửi hàng vào kho Amazon) hoặc <em>Seller Fulfilled Prime (SFP)</em> và đạt tiêu chuẩn tốc độ giao, tỷ lệ hủy đơn <1%, tỷ lệ đúng hạn >93.5%.
                </div>
                <div class="concept-item">
                    <span class="concept-var">is_amazon_choice</span> <strong>(Nhãn Amazon's Choice)</strong> —
                    Nhãn do <strong>thuật toán Amazon TỰ ĐỘNG</strong> gán, dựa trên các tiêu chí:<br/>
                    ✅ Rating cao (thường ≥ 4.0 ⭐)<br/>
                    ✅ Giá cả cạnh tranh trong danh mục<br/>
                    ✅ Sẵn sàng giao hàng ngay (in stock)<br/>
                    ✅ Tỷ lệ hoàn trả thấp<br/>
                    ⚠️ <strong>Người bán KHÔNG THỂ tự đăng ký</strong> — phải đạt tiêu chuẩn để Amazon tự động cấp.
                </div>
                <div class="concept-item">
                    <span class="concept-var">is_best_seller</span> <strong>(Nhãn Best Seller)</strong> —
                    Sản phẩm <strong>#1 trong danh mục</strong> dựa trên doanh số bán gần nhất, cập nhật <em>mỗi giờ</em>.<br/>
                    ⚠️ <span class="concept-tag red">LƯU Ý QUAN TRỌNG</span> Trong dataset này, <code>is_best_seller = True</code> cho <strong>100% sản phẩm</strong> (do phương pháp crawl data chỉ thu thập các SP best seller). Do đó biến này <strong>không có khả năng phân biệt</strong>.
                </div>
                <div class="concept-item">
                    <strong>🔬 Phương pháp thay thế:</strong> Sử dụng <span class="concept-var">is_amazon_choice</span> (559 SP đạt nhãn) + <strong>Top 20% sales volume</strong> làm proxy cho "sản phẩm nổi bật". So sánh tỷ lệ Prime trong các tier: Tổng thể → Amazon's Choice → Top 20% → Bottom 80%. Vẽ radar đa chiều so sánh "hồ sơ" Prime vs Non-Prime.
                </div>
            </div>
        </details>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Tỷ Lệ Prime Tổng Thể</div>
            <div class="kpi-value" id="k2_pr">0%</div>
            <div class="kpi-sub" id="k2_pr_s"></div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-title">Prime Rate — Amazon's Choice</div>
            <div class="kpi-value" id="k2_ac">0%</div>
            <div class="kpi-sub">Tỷ lệ Prime trong nhóm được đề xuất</div>
        </div>
        <div class="kpi-card c-amber">
            <div class="kpi-title" id="k2_t3">Chênh Lệch Doanh Số TB</div>
            <div class="kpi-value" id="k2_sd">0</div>
            <div class="kpi-sub" id="k2_sd_s"></div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Chênh Lệch Rating TB</div>
            <div class="kpi-value" id="k2_rd">0</div>
            <div class="kpi-sub" id="k2_rd_s"></div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Tỷ Lệ Prime Giữa Các Nhóm Sản Phẩm</div>
                <div class="chart-subtitle">So sánh % sản phẩm có Prime trong từng tier</div>
            </div>
            <div class="chart-wrapper"><canvas id="cPrimeRate"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Hồ Sơ Đa Chiều: Prime vs Non-Prime</div>
                <div class="chart-subtitle">So sánh chuẩn hóa 5 trục: Rating, Doanh số, Giá, Amazon Choice %, Free Ship %</div>
            </div>
            <div class="chart-wrapper"><canvas id="cRadar"></canvas></div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Hiệu Suất Prime vs Non-Prime Theo Danh Mục</div>
                <div class="chart-subtitle">Chênh lệch hiệu suất TB theo từng ngành hàng chi tiết</div>
            </div>
            <div class="chart-wrapper" style="min-height: 700px;"><canvas id="cPrimeCat"></canvas></div>
        </div>
    </div>

    <div class="insight-box warn" id="insightBox2">
        <div class="insight-icon">⚠️</div>
        <div class="insight-content">
            <div class="insight-label">KẾT LUẬN: PRIME CÓ PHẢI "TẤM VÉ BẮT BUỘC"?</div>
            <div class="insight-text" id="ins2">Đang phân tích...</div>
        </div>
    </div>
    </div><!-- /section-wrapper 2 -->

    <!-- ═══════════════════════════════════════════════════════════
         SECTION 3: TỐC ĐỘ GIAO HÀNG
         ═══════════════════════════════════════════════════════════ -->
    <div class="section-wrapper">
    <div class="section-sticky">
        <div class="section-title-row">
            <div class="section-title"><span class="num">3</span> TÁC ĐỘNG TỐC ĐỘ GIAO HÀNG</div>
            <div class="header-filters">
                <div class="hf-item"><span class="hf-label">Chỉ Số:</span>
                    <select id="selMetric3" onchange="applySection3()">
                        <option value="sales">Số Lượng Bán Ra</option>
                        <option value="revenue">Doanh Thu ($)</option>
                    </select>
                </div>
                <div class="hf-item"><span class="hf-label">Danh Mục:</span>
                    <select id="selCat3" onchange="applySection3()"><option value="ALL">Tất Cả Danh Mục</option></select>
                </div>
            </div>
        </div>
    </div>

    <div class="obj-card">
        <div class="obj-title">🎯 Mục tiêu phân tích</div>
        <div class="obj-text">
            Đo lường mức độ ảnh hưởng của <strong>thời gian chờ giao hàng</strong> (ước tính bằng số ngày)
            đến <strong>điểm đánh giá (rating)</strong> và <strong>khối lượng bán ra (sales volume)</strong>.
            Đề xuất chiến lược định vị sản phẩm thông qua <strong>chất lượng dịch vụ logistics</strong>.
        </div>
        <details class="concept-panel" open>
            <summary>📚 Giải thích các biến & khái niệm liên quan</summary>
            <div class="concept-list">
                <div class="concept-item">
                    <span class="concept-var">delivery_date_text</span> <strong>(Ngày Giao Dự Kiến)</strong> —
                    Thông tin ngày giao hàng hiển thị trên trang sản phẩm Amazon. Có 2 format chính:
                    <code>"Mon, Apr 13"</code> (giao vào thứ 2 ngày 13/4) hoặc
                    <code>"Apr 8 - 28"</code> (giao trong khoảng 8-28/4).
                </div>
                <div class="concept-item">
                    <span class="concept-var">est_delivery_days</span> <strong>(Số Ngày Giao Ước Tính)</strong> —
                    Biến được <em>tính toán</em> (feature engineering): số ngày từ <strong>ngày crawl data</strong> (ước tính ~6/4/2025) đến ngày giao dự kiến.<br/>
                    Công thức: <code>est_delivery_days = ngày giao - ngày crawl</code>.<br/>
                    Với format "Apr 8 - 28" → lấy trung bình: <code>(8+28)/2 - 6 = 12 ngày</code>.
                </div>
                <div class="concept-item">
                    <span class="concept-var">rating</span> <strong>(Điểm Đánh Giá Trung Bình)</strong> —
                    Điểm trung bình từ <strong>1-5 ⭐</strong> do khách hàng đánh giá sau khi mua sản phẩm.
                    Phản ánh mức độ hài lòng tổng thể: chất lượng sản phẩm, dịch vụ bán hàng, <em>bao gồm cả trải nghiệm giao hàng</em>.
                    Rating thấp có thể do giao chậm dù sản phẩm tốt → đây là giả thuyết cần kiểm chứng.
                </div>
                <div class="concept-item">
                    <strong>📊 Hệ Số Tương Quan Pearson</strong> —
                    Đo lường mức độ tương quan <strong>tuyến tính</strong> giữa 2 biến, giá trị từ <strong>-1</strong> đến <strong>+1</strong>.
                    <span class="concept-tag red">-1</span> = tương quan âm hoàn hảo (khi A tăng → B giảm).
                    <span class="concept-tag amber">0</span> = không tương quan.
                    <span class="concept-tag green">+1</span> = tương quan dương hoàn hảo.
                    Ở đây tính: <code>corr(est_delivery_days, rating)</code> — nếu âm → giao chậm làm giảm rating.
                </div>
                <div class="concept-item">
                    <strong>🔬 Phương pháp:</strong> Chia sản phẩm thành nhóm theo thời gian giao (1-3, 4-5, 6-7, 8-10, 11-14, 15+ ngày). So sánh rating TB và doanh số TB giữa các nhóm. Build heatmap matrix kết hợp <em>tốc độ giao × phân khúc giá</em> để tìm "điểm ngọt" (sweet spot) cho logistics.
                </div>
            </div>
        </details>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Thời Gian Giao Hàng TB</div>
            <div class="kpi-value" id="k3_days">0 ngày</div>
            <div class="kpi-sub" id="k3_days_s"></div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-title">% Giao Dưới 7 Ngày</div>
            <div class="kpi-value" id="k3_fast">0%</div>
            <div class="kpi-sub">Tỷ lệ sản phẩm giao nhanh</div>
        </div>
        <div class="kpi-card c-red">
            <div class="kpi-title">Chênh Lệch Rating (Nhanh vs Chậm)</div>
            <div class="kpi-value" id="k3_rg">0</div>
            <div class="kpi-sub" id="k3_rg_s"></div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Hệ Số Pearson (Ngày Giao × Rating)</div>
            <div class="kpi-value" id="k3_corr">0</div>
            <div class="kpi-sub">Tương quan tuyến tính</div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Tác Động Thời Gian Giao Đến Hiệu Suất & Rating</div>
                <div class="chart-subtitle">Bars = hiệu suất TB · Line = rating TB · Trục kép</div>
            </div>
            <div class="chart-wrapper"><canvas id="cDelivImpact"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Ma Trận: Tốc Độ Giao × Phân Khúc Giá</div>
                <div class="chart-subtitle">Màu nền = rating · ⭐ = rating TB · Giá trị = hiệu suất TB</div>
            </div>
            <div class="chart-wrapper" style="overflow-x:auto; display:block;"><div id="hmContainer"></div></div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Hiệu Suất Theo Danh Mục: Giao Nhanh (≤7 Ngày) vs Giao Chậm (>7 Ngày)</div>
                <div class="chart-subtitle">So sánh hiệu suất TB giữa nhóm giao nhanh và chậm trong mỗi ngành hàng</div>
            </div>
            <div class="chart-wrapper" style="min-height: 700px;"><canvas id="cCatDeliv"></canvas></div>
        </div>
    </div>

    <div class="insight-box" id="insightBox3">
        <div class="insight-icon">🚚</div>
        <div class="insight-content">
            <div class="insight-label">KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC LOGISTICS</div>
            <div class="insight-text" id="ins3">Đang phân tích...</div>
        </div>
    </div>
    </div><!-- /section-wrapper 3 -->

<!-- ═══════════════════════════════════════════════════════════
     JAVASCRIPT
     ═══════════════════════════════════════════════════════════ -->
<script>
    const RAW = {data_json_str};
    let GI = {{}};

    const C = {{
        prime: '#F97316', non: '#9CA3AF',
        pal: ['#10B981','#3B82F6','#F59E0B','#F97316','#EF4444','#8B5CF6'],
        green: '#10B981', red: '#EF4444', blue: '#3B82F6', amber: '#F59E0B'
    }};
    const fmtN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR = n => Number(n).toFixed(2);
    const fmtP = n => Number(n).toFixed(1) + '%';

    function axF(isCur) {{ return function(v) {{
        if (isCur) return v >= 1000 ? '$' + (v/1000).toFixed(0) + 'K' : '$' + Math.round(v);
        return v >= 1000 ? (v/1000).toFixed(0) + 'K' : Math.round(v);
    }}; }}
    function ttF(isCur) {{ return function(ctx) {{
        return ' ' + (isCur ? '$' : '') + fmtN(ctx.raw);
    }}; }}
    function filterData(catSelId) {{
        let cat = document.getElementById(catSelId).value;
        return RAW.filter(d => cat === 'ALL' || d.crawl_category === cat);
    }}

    // ── SETUP ──
    function setup() {{
        let cats = [...new Set(RAW.map(d => d.crawl_category).filter(c => c && c !== 'Khác'))].sort();
        ['selCat1','selCat2','selCat3'].forEach(id => {{
            let sel = document.getElementById(id);
            cats.forEach(c => {{ let o = document.createElement('option'); o.value = c; o.innerText = c; sel.appendChild(o); }});
        }});
        initCharts();
        applySection1(); applySection2(); applySection3();
        initStickyHeaders();
    }}

    // ── JS-driven Sticky Headers (GPU-composited, no layout thrash) ──
    function initStickyHeaders() {{
        const wraps = [...document.querySelectorAll('.section-wrapper')];
        const sticks = wraps.map(w => w.querySelector('.section-sticky'));
        if (!wraps.length) return;

        let myIframe = null;
        try {{
            const iframes = window.parent.document.querySelectorAll('iframe');
            for (let f of iframes) {{
                try {{ if (f.contentWindow === window) {{ myIframe = f; break; }} }} catch(e) {{}}
            }}
        }} catch(e) {{ return; }}
        if (!myIframe) return;

        // Cache layout measurements (avoid reading DOM every frame)
        let L = [];
        function cacheLayout() {{
            L = wraps.map((w, i) => ({{
                wTop: w.offsetTop,
                wH: w.offsetHeight,
                sH: sticks[i].offsetHeight
            }}));
        }}
        cacheLayout();
        window.addEventListener('resize', cacheLayout);

        let ticking = false;
        let prevStates = wraps.map(() => 0); // 0=normal, 1=stuck, 2=bottom

        function update() {{
            const scrollY = Math.max(0, -myIframe.getBoundingClientRect().top);

            for (let i = 0; i < wraps.length; i++) {{
                const s = sticks[i];
                const {{ wTop, wH, sH }} = L[i];
                let newState = 0, dy = 0;

                if (scrollY >= wTop && scrollY < wTop + wH - sH) {{
                    newState = 1;
                    dy = scrollY - wTop;
                }} else if (scrollY >= wTop + wH - sH && scrollY < wTop + wH) {{
                    newState = 2;
                    dy = wH - sH;
                }}

                // GPU-composited transform (no reflow)
                s.style.transform = dy > 0 ? 'translateY(' + dy + 'px)' : '';

                // Only toggle class when state actually changes
                if (newState !== prevStates[i]) {{
                    s.classList.toggle('is-stuck', newState > 0);
                    prevStates[i] = newState;
                }}
            }}
            ticking = false;
        }}

        function onScroll() {{
            if (!ticking) {{ requestAnimationFrame(update); ticking = true; }}
        }}

        try {{ window.parent.addEventListener('scroll', onScroll, true); }} catch(e) {{}}
        window.addEventListener('scroll', onScroll);
        setTimeout(cacheLayout, 500); // recache after charts render
        update();
    }}

    // ══════════════════════════════════════
    // SECTION 1
    // ══════════════════════════════════════
    function applySection1() {{
        let metric = document.getElementById('selMetric1').value;
        let data = filterData('selCat1');
        let isCur = metric === 'revenue';
        let vP = isCur ? 'revenue' : 'sales_volume_num';
        let pfx = isCur ? '$' : '';
        let mNm = isCur ? 'Doanh Thu' : 'Doanh Số';

        document.getElementById('k1_t2').innerText = mNm + ' TB — Nhóm Free Ship';
        document.getElementById('k1_t3').innerText = mNm + ' TB — Nhóm Tốn Phí Ship';

        let freeG = data.filter(d => d.is_prime || d.delivery_fee === 0);
        let paidG = data.filter(d => !d.is_prime && d.delivery_fee > 0);
        let avgFR = data.length > 0 ? (data.reduce((a,d) => a + (d.fee_ratio||0), 0) / data.length * 100) : 0;
        let freeAvg = freeG.length > 0 ? freeG.reduce((a,d) => a + (d[vP]||0), 0) / freeG.length : 0;
        let paidAvg = paidG.length > 0 ? paidG.reduce((a,d) => a + (d[vP]||0), 0) / paidG.length : 0;
        let freeRev = freeG.reduce((a,d) => a + (d.revenue||0), 0);
        let totalRev = data.reduce((a,d) => a + (d.revenue||0), 0);
        let freeRevP = totalRev > 0 ? (freeRev / totalRev * 100) : 0;
        let mult = paidAvg > 0 ? (freeAvg / paidAvg) : 0;

        document.getElementById('k1_fr').innerText = fmtP(avgFR);
        document.getElementById('k1_fr_s').innerText = avgFR > 30 ? '⚠ Trên ngưỡng khuyến nghị 30%' : '✓ Dưới ngưỡng 30%';
        document.getElementById('k1_free').innerText = pfx + fmtN(freeAvg);
        document.getElementById('k1_free_s').innerText = freeG.length + ' sản phẩm';
        document.getElementById('k1_paid').innerText = pfx + fmtN(paidAvg);
        document.getElementById('k1_paid_s').innerText = paidG.length + ' sản phẩm';
        document.getElementById('k1_rev').innerText = fmtP(freeRevP);

        // Fee Bins chart
        let bins = [
            {{l:'Free (0%)',mn:0,mx:0.001,s:0,c:0}}, {{l:'0-15%',mn:0.001,mx:0.15,s:0,c:0}},
            {{l:'15-30%',mn:0.15,mx:0.30,s:0,c:0}}, {{l:'30-50%',mn:0.30,mx:0.50,s:0,c:0}},
            {{l:'50-100%',mn:0.50,mx:1.00,s:0,c:0}}, {{l:'>100%',mn:1.00,mx:999,s:0,c:0}}
        ];
        data.forEach(d => {{
            let r = d.is_prime ? 0 : (d.fee_ratio||0);
            for(let b of bins) {{ if(r >= b.mn && r < b.mx) {{ b.s += (d[vP]||0); b.c++; break; }}
                if(b.mx===999 && r>=b.mn) {{ b.s += (d[vP]||0); b.c++; break; }} }}
        }});
        GI.cFeeBins.data.labels = bins.map(b=>b.l);
        GI.cFeeBins.data.datasets[0].data = bins.map(b=> b.c>0 ? b.s/b.c : 0);
        GI.cFeeBins.data.datasets[0].label = mNm + ' TB';
        GI.cFeeBins.data.datasets[1].data = bins.map(b=>b.c);
        GI.cFeeBins.options.scales.y.ticks.callback = axF(isCur);
        GI.cFeeBins.options.scales.y.title = {{display:true, text: mNm, font:{{size:10}}}};
        GI.cFeeBins.update();

        // Revenue Share Doughnut
        let rb = [{{l:'Free Ship / Prime',s:0}}, {{l:'Phí < $12',s:0}}, {{l:'$12-25',s:0}}, {{l:'$25-50',s:0}}, {{l:'> $50',s:0}}];
        data.forEach(d => {{
            let v = d[vP]||0;
            if(d.is_prime||d.delivery_fee===0) rb[0].s+=v;
            else if(d.delivery_fee<=12) rb[1].s+=v;
            else if(d.delivery_fee<=25) rb[2].s+=v;
            else if(d.delivery_fee<=50) rb[3].s+=v;
            else rb[4].s+=v;
        }});
        GI.cRevShare.data.labels = rb.map(b=>b.l);
        GI.cRevShare.data.datasets[0].data = rb.map(b=>b.s);
        GI.cRevShare.options.plugins.tooltip.callbacks.label = function(ctx) {{
            let tot = ctx.dataset.data.reduce((a,b)=>a+b,0);
            let pct = tot>0?(ctx.raw/tot*100).toFixed(1):0;
            return ' ' + pfx + fmtN(ctx.raw) + ' (' + pct + '%)';
        }};
        GI.cRevShare.update();

        // Insight
        let ins = '<strong>Phát hiện chính:</strong> Sản phẩm miễn phí vận chuyển đạt ' + mNm.toLowerCase() + ' trung bình <strong>' + pfx + fmtN(freeAvg) + '</strong>';
        if(mult>1) ins += ', cao gấp <strong>' + fmtR(mult) + ' lần</strong> so với nhóm tốn phí ship (' + pfx + fmtN(paidAvg) + ').';
        else ins += ' so với ' + pfx + fmtN(paidAvg) + ' của nhóm tốn phí.';
        ins += '<br/><strong>Ngưỡng kháng cự:</strong> Tỷ lệ phí ship/giá trung bình đạt <strong>' + fmtP(avgFR) + '</strong>';
        ins += avgFR>30 ? ' — đang ở mức cao, cần chiến lược giảm gánh nặng.' : ' — còn trong ngưỡng chấp nhận.';
        ins += '<br/><strong>Đề xuất:</strong> Với nhóm sản phẩm giá thấp (< $25), nên <strong>gộp phí ship vào giá bán</strong> để tạo hiệu ứng Free Ship, vì Free Ship chiếm <strong>' + fmtP(freeRevP) + '</strong> tổng doanh thu. Với sản phẩm cao cấp (> $100), có thể <strong>tách rời phí ship</strong> vì khách hàng ít nhạy cảm hơn.';
        document.getElementById('ins1').innerHTML = ins;
    }}

    // ══════════════════════════════════════
    // SECTION 2
    // ══════════════════════════════════════
    function applySection2() {{
        let metric = document.getElementById('selMetric2').value;
        let data = filterData('selCat2');
        let isCur = metric === 'revenue';
        let vP = isCur ? 'revenue' : 'sales_volume_num';
        let pfx = isCur ? '$' : '';
        let mNm = isCur ? 'Doanh Thu' : 'Doanh Số';

        document.getElementById('k2_t3').innerText = 'Chênh Lệch ' + mNm + ' TB';

        let primeD = data.filter(d=>d.is_prime), nonD = data.filter(d=>!d.is_prime);
        let acD = data.filter(d=>d.is_amazon_choice);
        let topD = data.filter(d=>d.is_top_seller), botD = data.filter(d=>!d.is_top_seller);

        let prR = data.length>0 ? primeD.length/data.length*100 : 0;
        let acPR = acD.length>0 ? acD.filter(d=>d.is_prime).length/acD.length*100 : 0;
        let pAvg = primeD.length>0 ? primeD.reduce((a,d)=>a+(d[vP]||0),0)/primeD.length : 0;
        let nAvg = nonD.length>0 ? nonD.reduce((a,d)=>a+(d[vP]||0),0)/nonD.length : 0;
        let pRat = primeD.length>0 ? primeD.reduce((a,d)=>a+(d.rating_val||0),0)/primeD.length : 0;
        let nRat = nonD.length>0 ? nonD.reduce((a,d)=>a+(d.rating_val||0),0)/nonD.length : 0;
        let sDiff = pAvg - nAvg, rDiff = pRat - nRat;

        document.getElementById('k2_pr').innerText = fmtP(prR);
        document.getElementById('k2_pr_s').innerText = primeD.length + ' / ' + data.length + ' SP';
        document.getElementById('k2_ac').innerText = fmtP(acPR);
        document.getElementById('k2_sd').innerText = (sDiff>=0?'+':'') + pfx + fmtN(sDiff);
        document.getElementById('k2_sd_s').innerText = sDiff>=0 ? 'Prime cao hơn' : 'Prime thấp hơn Non-Prime';
        document.getElementById('k2_rd').innerText = (rDiff>=0?'+':'') + fmtR(rDiff);
        document.getElementById('k2_rd_s').innerText = 'Prime: ' + fmtR(pRat) + ' vs Non-Prime: ' + fmtR(nRat);

        // Prime Rate Bar
        let topPR = topD.length>0 ? topD.filter(d=>d.is_prime).length/topD.length*100 : 0;
        let botPR = botD.length>0 ? botD.filter(d=>d.is_prime).length/botD.length*100 : 0;
        GI.cPrimeRate.data.datasets[0].data = [prR, acPR, topPR, botPR];
        GI.cPrimeRate.update();

        // Radar
        let maxS = Math.max(pAvg, nAvg, 1);
        let pPr = primeD.length>0 ? primeD.reduce((a,d)=>a+(d.current_price||0),0)/primeD.length : 0;
        let nPr = nonD.length>0 ? nonD.reduce((a,d)=>a+(d.current_price||0),0)/nonD.length : 0;
        let maxPr = Math.max(pPr, nPr, 1);
        let pAC = primeD.length>0 ? primeD.filter(d=>d.is_amazon_choice).length/primeD.length*100 : 0;
        let nAC = nonD.length>0 ? nonD.filter(d=>d.is_amazon_choice).length/nonD.length*100 : 0;
        let pFS = primeD.length>0 ? primeD.filter(d=>d.delivery_fee===0).length/primeD.length*100 : 0;
        let nFS = nonD.length>0 ? nonD.filter(d=>d.delivery_fee===0).length/nonD.length*100 : 0;
        GI.cRadar.data.datasets[0].data = [pRat/5*100, pAvg/maxS*100, pPr/maxPr*100, pAC, pFS];
        GI.cRadar.data.datasets[1].data = [nRat/5*100, nAvg/maxS*100, nPr/maxPr*100, nAC, nFS];
        GI.cRadar.update();

        // Category bar
        let cs = {{}};
        data.forEach(d => {{
            let c = d.crawl_category || 'Khác'; if(c==='Khác') return;
            if(!cs[c]) cs[c] = {{pS:0,pC:0,nS:0,nC:0}};
            if(d.is_prime) {{ cs[c].pS += (d[vP]||0); cs[c].pC++; }}
            else {{ cs[c].nS += (d[vP]||0); cs[c].nC++; }}
        }});
        let cl = Object.keys(cs).sort();
        GI.cPrimeCat.data.labels = cl;
        GI.cPrimeCat.data.datasets[0].data = cl.map(c=> cs[c].pC>0 ? cs[c].pS/cs[c].pC : 0);
        GI.cPrimeCat.data.datasets[0].label = 'Prime — ' + mNm + ' TB';
        GI.cPrimeCat.data.datasets[1].data = cl.map(c=> cs[c].nC>0 ? cs[c].nS/cs[c].nC : 0);
        GI.cPrimeCat.data.datasets[1].label = 'Non-Prime — ' + mNm + ' TB';
        GI.cPrimeCat.options.scales.x.ticks.callback = axF(isCur);
        GI.cPrimeCat.options.plugins.tooltip.callbacks.label = ttF(isCur);
        GI.cPrimeCat.update();

        // Insight
        let ins = '<strong>Phát hiện về Prime:</strong> Prime chiếm <strong>' + fmtP(prR) + '</strong> tổng SP (' + primeD.length + '/' + data.length + ')';
        ins += ', nhưng trong Amazon\\'s Choice tỷ lệ Prime là <strong>' + fmtP(acPR) + '</strong>';
        let mult2 = prR > 0 ? acPR / prR : 0;
        if(mult2 > 1) ins += ' — gấp <strong>' + fmtR(mult2) + 'x</strong>.';
        else ins += '.';
        ins += '<br/><strong>Chênh lệch hiệu suất:</strong> ' + mNm + ' TB Prime = <strong>' + pfx + fmtN(pAvg) + '</strong> vs Non-Prime = <strong>' + pfx + fmtN(nAvg) + '</strong>';
        if(sDiff < 0) ins += '. Prime <strong>không đảm bảo ' + mNm.toLowerCase() + ' cao hơn</strong> — nhãn Prime là yếu tố gia tăng <em>uy tín và khả năng hiển thị</em>, không phải yếu tố quyết định doanh số.';
        else ins += '. Prime mang lại lợi thế rõ rệt.';
        ins += '<br/><strong>Kết luận:</strong> Prime là <strong>"tấm vé ưu tiên"</strong> — tăng khả năng được Amazon đề xuất';
        if(mult2 > 1) ins += ' (gấp ' + fmtR(mult2) + 'x)';
        ins += ' — nhưng <strong>không phải "tấm vé bắt buộc"</strong> để ' + mNm.toLowerCase() + ' cao. Yếu tố quyết định vẫn là chất lượng SP, giá cả và đánh giá.';
        document.getElementById('ins2').innerHTML = ins;
    }}

    // ══════════════════════════════════════
    // SECTION 3
    // ══════════════════════════════════════
    function applySection3() {{
        let metric = document.getElementById('selMetric3').value;
        let data = filterData('selCat3');
        let isCur = metric === 'revenue';
        let vP = isCur ? 'revenue' : 'sales_volume_num';
        let pfx = isCur ? '$' : '';
        let mNm = isCur ? 'Doanh Thu' : 'Doanh Số';

        let wD = data.filter(d => d.est_delivery_days != null && d.est_delivery_days > 0);
        let avgD = wD.length>0 ? wD.reduce((a,d)=>a+d.est_delivery_days,0)/wD.length : 0;
        let fastG = wD.filter(d=>d.est_delivery_days<=7), slowG = wD.filter(d=>d.est_delivery_days>7);
        let fastP = wD.length>0 ? fastG.length/wD.length*100 : 0;
        let fR = fastG.length>0 ? fastG.reduce((a,d)=>a+(d.rating_val||0),0)/fastG.length : 0;
        let sR = slowG.length>0 ? slowG.reduce((a,d)=>a+(d.rating_val||0),0)/slowG.length : 0;
        let rGap = fR - sR;
        let corr = pearsonCorr(wD.map(d=>d.est_delivery_days), wD.map(d=>d.rating_val||0));

        document.getElementById('k3_days').innerText = fmtR(avgD) + ' ngày';
        document.getElementById('k3_days_s').innerText = wD.length + '/' + data.length + ' SP có dữ liệu';
        document.getElementById('k3_fast').innerText = fmtP(fastP);
        document.getElementById('k3_rg').innerText = (rGap>=0?'+':'') + fmtR(rGap);
        document.getElementById('k3_rg_s').innerText = 'Nhanh: ' + fmtR(fR) + ' vs Chậm: ' + fmtR(sR);
        document.getElementById('k3_corr').innerText = fmtR(corr);

        // Delivery Impact chart
        let db = [
            {{l:'1-3d',mn:1,mx:3}}, {{l:'4-5d',mn:4,mx:5}}, {{l:'6-7d',mn:6,mx:7}},
            {{l:'8-10d',mn:8,mx:10}}, {{l:'11-14d',mn:11,mx:14}}, {{l:'15d+',mn:15,mx:999}}
        ];
        let dbs = db.map(()=>({{sV:0,sR:0,c:0}}));
        wD.forEach(d => {{ for(let i=0;i<db.length;i++) {{ if(d.est_delivery_days>=db[i].mn && d.est_delivery_days<=db[i].mx) {{ dbs[i].sV+=(d[vP]||0); dbs[i].sR+=(d.rating_val||0); dbs[i].c++; break; }} }} }});
        GI.cDelivImpact.data.labels = db.map(b=>b.l);
        GI.cDelivImpact.data.datasets[0].data = dbs.map(s=>s.c>0?s.sV/s.c:0);
        GI.cDelivImpact.data.datasets[0].label = mNm + ' TB';
        GI.cDelivImpact.data.datasets[1].data = dbs.map(s=>s.c>0?s.sR/s.c:0);
        GI.cDelivImpact.options.scales.y.ticks.callback = axF(isCur);
        GI.cDelivImpact.options.scales.y.title = {{display:true, text:mNm, font:{{size:10}}}};
        GI.cDelivImpact.update();

        // Heatmap
        let hmD = ['1-3 ngày','4-7 ngày','8-14 ngày','15+ ngày'];
        let hmDR = [[1,3],[4,7],[8,14],[15,999]];
        let hmP = ['< $25','$25-50','$50-100','> $100'];
        let hmPR = [[0,25],[25,50],[50,100],[100,999999]];
        let hmM = {{}};
        hmD.forEach(d => {{ hmM[d]={{}}; hmP.forEach(p => {{ hmM[d][p]={{sR:0,sV:0,c:0}}; }}); }});
        wD.forEach(d => {{
            let di=-1, pi=-1, pr=d.current_price||0;
            for(let i=0;i<hmDR.length;i++) if(d.est_delivery_days>=hmDR[i][0]&&d.est_delivery_days<=hmDR[i][1]) {{ di=i; break; }}
            for(let i=0;i<hmPR.length;i++) if(pr>=hmPR[i][0]&&pr<hmPR[i][1]) {{ pi=i; break; }}
            if(di>=0&&pi>=0) {{ hmM[hmD[di]][hmP[pi]].sR+=(d.rating_val||0); hmM[hmD[di]][hmP[pi]].sV+=(d[vP]||0); hmM[hmD[di]][hmP[pi]].c++; }}
        }});
        let h = '<table class="hm-table"><tr><th style="min-width:80px;">Tốc Độ</th>';
        hmP.forEach(p => {{ h += '<th>'+p+'</th>'; }}); h += '</tr>';
        hmD.forEach(d => {{
            h += '<tr><td class="hm-row-label">'+d+'</td>';
            hmP.forEach(p => {{
                let cl=hmM[d][p], ar=cl.c>0?cl.sR/cl.c:0, av=cl.c>0?cl.sV/cl.c:0;
                h += '<td style="background:'+rBg(ar)+';">';
                if(cl.c>0) h += '<div class="hm-rating">⭐'+fmtR(ar)+'</div><div class="hm-sales">'+pfx+fmtN(av)+'</div><div class="hm-count">n='+cl.c+'</div>';
                else h += '<div class="hm-count" style="color:#D6D3D1;">—</div>';
                h += '</td>';
            }}); h += '</tr>';
        }}); h += '</table>';
        document.getElementById('hmContainer').innerHTML = h;

        // Category Delivery
        let cd = {{}};
        wD.forEach(d => {{
            let c=d.crawl_category||'Khác'; if(c==='Khác') return;
            if(!cd[c]) cd[c]={{fS:0,fC:0,sS:0,sC:0}};
            if(d.est_delivery_days<=7) {{ cd[c].fS+=(d[vP]||0); cd[c].fC++; }}
            else {{ cd[c].sS+=(d[vP]||0); cd[c].sC++; }}
        }});
        let cdl = Object.keys(cd).sort();
        GI.cCatDeliv.data.labels = cdl;
        GI.cCatDeliv.data.datasets[0].data = cdl.map(c=>cd[c].fC>0?cd[c].fS/cd[c].fC:0);
        GI.cCatDeliv.data.datasets[0].label = 'Nhanh (≤7d) — ' + mNm + ' TB';
        GI.cCatDeliv.data.datasets[1].data = cdl.map(c=>cd[c].sC>0?cd[c].sS/cd[c].sC:0);
        GI.cCatDeliv.data.datasets[1].label = 'Chậm (>7d) — ' + mNm + ' TB';
        GI.cCatDeliv.options.scales.x.ticks.callback = axF(isCur);
        GI.cCatDeliv.options.plugins.tooltip.callbacks.label = ttF(isCur);
        GI.cCatDeliv.update();

        // Insight
        let fAvgS = fastG.length>0 ? fastG.reduce((a,d)=>a+(d[vP]||0),0)/fastG.length : 0;
        let sAvgS = slowG.length>0 ? slowG.reduce((a,d)=>a+(d[vP]||0),0)/slowG.length : 0;
        let ins = '<strong>Phát hiện:</strong> Thời gian giao TB = <strong>' + fmtR(avgD) + ' ngày</strong>. ';
        ins += 'Nhóm giao nhanh (≤7 ngày) chiếm <strong>' + fmtP(fastP) + '</strong>, đạt rating <strong>' + fmtR(fR) + '</strong> vs chậm (>7 ngày) <strong>' + fmtR(sR) + '</strong>';
        ins += ' (Δ = <strong>' + (rGap>=0?'+':'') + fmtR(rGap) + ' ⭐</strong>).';
        ins += '<br/><strong>Tương quan:</strong> Pearson(ngày giao, rating) = <strong>' + fmtR(corr) + '</strong>';
        if(corr<-0.03) ins += ' (âm) — giao chậm <strong>làm giảm đánh giá</strong>.';
        else if(corr>0.03) ins += ' (dương nhẹ) — thời gian giao không ảnh hưởng tiêu cực rõ.';
        else ins += ' (gần 0) — tương quan yếu, nhưng chênh lệch rating nhóm nhanh/chậm vẫn có ý nghĩa thực tiễn.';
        ins += '<br/><strong>' + mNm + ':</strong> Giao nhanh đạt TB <strong>' + pfx + fmtN(fAvgS) + '</strong> vs giao chậm <strong>' + pfx + fmtN(sAvgS) + '</strong>.';
        ins += '<br/><strong>Đề xuất:</strong> Cam kết giao <strong>≤7 ngày</strong> — khoảng thời gian tối ưu. Với các category chênh lệch lớn giữa nhanh/chậm, nên <strong>ưu tiên FBA</strong> hoặc đầu tư logistics nội bộ.';
        document.getElementById('ins3').innerHTML = ins;
    }}

    // ── UTILITIES ──
    function pearsonCorr(x,y) {{
        let n=x.length; if(n<2) return 0;
        let sx=0,sy=0,sxy=0,sx2=0,sy2=0;
        for(let i=0;i<n;i++) {{ sx+=x[i]; sy+=y[i]; sxy+=x[i]*y[i]; sx2+=x[i]*x[i]; sy2+=y[i]*y[i]; }}
        let d=Math.sqrt((n*sx2-sx*sx)*(n*sy2-sy*sy));
        return d===0?0:(n*sxy-sx*sy)/d;
    }}
    function rBg(r) {{ if(r>=4.5) return 'rgba(16,185,129,0.18)'; if(r>=4.3) return 'rgba(245,158,11,0.14)'; if(r>=4.0) return 'rgba(249,115,22,0.14)'; if(r>0) return 'rgba(239,68,68,0.12)'; return 'transparent'; }}

    // ══════════════════════════════════════
    // INIT CHARTS
    // ══════════════════════════════════════
    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.size = 11;

        // S1: Fee Bins
        GI.cFeeBins = new Chart(document.getElementById('cFeeBins'), {{
            type:'bar',
            data: {{ labels:[], datasets:[
                {{ label:'Doanh Số TB', data:[], backgroundColor:['rgba(16,185,129,0.75)','rgba(239,68,68,0.65)','rgba(249,115,22,0.65)','rgba(245,158,11,0.65)','rgba(59,130,246,0.65)','rgba(139,92,246,0.65)'], borderRadius:5, barPercentage:0.7, yAxisID:'y', order:2 }},
                {{ label:'Số Lượng SP', data:[], type:'line', borderColor:'#78716C', backgroundColor:'rgba(120,113,108,0.1)', borderWidth:2, pointRadius:4, pointBackgroundColor:'#78716C', fill:true, tension:0.3, yAxisID:'y1', order:1 }}
            ] }},
            options: {{ responsive:true, maintainAspectRatio:false,
                plugins: {{ legend:{{position:'bottom', labels:{{usePointStyle:true, pointStyle:'circle', padding:12}}}},
                    tooltip:{{callbacks:{{label:function(ctx){{ if(ctx.datasetIndex===0) return ' '+fmtN(ctx.raw); return ' '+fmtN(ctx.raw)+' SP'; }}}}}} }},
                scales: {{ x:{{grid:{{display:false}}}}, y:{{position:'left', grid:{{borderDash:[3,3]}}, ticks:{{callback:axF(false)}}, title:{{display:true,text:'Doanh Số',font:{{size:10}}}}}},
                    y1:{{position:'right', grid:{{drawOnChartArea:false}}, ticks:{{callback:v=>fmtN(v)}}, title:{{display:true,text:'Số SP',font:{{size:10}}}}}} }}
            }}
        }});

        // S1: Revenue Share
        GI.cRevShare = new Chart(document.getElementById('cRevShare'), {{
            type:'doughnut',
            data: {{ labels:[], datasets:[{{data:[], backgroundColor:C.pal.concat(['#D4D4D8']), borderWidth:1, hoverOffset:6}}] }},
            options: {{ responsive:true, maintainAspectRatio:false, cutout:'55%',
                plugins: {{ legend:{{position:'bottom', labels:{{usePointStyle:true, pointStyle:'circle', padding:10, font:{{size:10}}}}}},
                    tooltip:{{callbacks:{{label:function(ctx){{ let t=ctx.dataset.data.reduce((a,b)=>a+b,0); return ' '+fmtN(ctx.raw)+' ('+(t>0?(ctx.raw/t*100).toFixed(1):0)+'%)'; }}}}}} }}
            }}
        }});

        // S2: Prime Rate
        GI.cPrimeRate = new Chart(document.getElementById('cPrimeRate'), {{
            type:'bar',
            data: {{ labels:['Tổng Thể','Amazon\\'s Choice','Top 20% Sales','Bottom 80%'],
                datasets:[{{ label:'Tỷ Lệ Prime (%)', data:[0,0,0,0], backgroundColor:[C.non,C.green,C.prime,'#D4D4D8'], borderRadius:5, barPercentage:0.6 }}] }},
            options: {{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
                plugins: {{ legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>' '+fmtR(ctx.raw)+'%'}}}} }},
                scales: {{ x:{{grid:{{borderDash:[3,3]}}, ticks:{{callback:v=>v+'%'}}}}, y:{{grid:{{display:false}}}} }}
            }}
        }});

        // S2: Radar
        GI.cRadar = new Chart(document.getElementById('cRadar'), {{
            type:'radar',
            data: {{ labels:['Rating','Doanh Số','Giá TB','Amazon Choice %','Free Ship %'],
                datasets:[
                    {{ label:'Prime', data:[0,0,0,0,0], borderColor:C.prime, backgroundColor:'rgba(249,115,22,0.15)', pointBackgroundColor:C.prime, pointRadius:3, borderWidth:2 }},
                    {{ label:'Non-Prime', data:[0,0,0,0,0], borderColor:C.non, backgroundColor:'rgba(156,163,175,0.12)', pointBackgroundColor:C.non, pointRadius:3, borderWidth:2 }}
                ] }},
            options: {{ responsive:true, maintainAspectRatio:false,
                plugins: {{ legend:{{position:'bottom', labels:{{usePointStyle:true, pointStyle:'circle', padding:12}}}},
                    tooltip:{{callbacks:{{label:ctx=>' '+ctx.dataset.label+': '+fmtR(ctx.raw)}}}} }},
                scales: {{ r:{{ min:0, max:100, ticks:{{stepSize:25,display:false}}, grid:{{color:'#E7E5E4'}}, angleLines:{{color:'#E7E5E4'}}, pointLabels:{{font:{{size:10,weight:'600'}}}} }} }}
            }}
        }});

        // S2: Prime by Category
        GI.cPrimeCat = new Chart(document.getElementById('cPrimeCat'), {{
            type:'bar',
            data: {{ labels:[], datasets:[
                {{ label:'Prime', data:[], backgroundColor:C.prime, borderRadius:4, barPercentage:0.7 }},
                {{ label:'Non-Prime', data:[], backgroundColor:C.non, borderRadius:4, barPercentage:0.7 }}
            ] }},
            options: {{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
                plugins: {{ legend:{{position:'top', labels:{{usePointStyle:true, pointStyle:'circle'}}}},
                    tooltip:{{callbacks:{{label:ttF(false)}}}} }},
                scales: {{ x:{{grid:{{borderDash:[3,3]}}, ticks:{{callback:axF(false)}}}}, y:{{grid:{{display:false}}}} }}
            }}
        }});

        // S3: Delivery Impact
        GI.cDelivImpact = new Chart(document.getElementById('cDelivImpact'), {{
            type:'bar',
            data: {{ labels:[], datasets:[
                {{ label:'Doanh Số TB', data:[], backgroundColor:'rgba(59,130,246,0.65)', borderRadius:5, barPercentage:0.6, yAxisID:'y', order:2 }},
                {{ label:'Rating TB', data:[], type:'line', borderColor:'#F97316', backgroundColor:'rgba(249,115,22,0.1)', borderWidth:2.5, pointRadius:5, pointBackgroundColor:'#F97316', fill:false, tension:0.3, yAxisID:'y1', order:1 }}
            ] }},
            options: {{ responsive:true, maintainAspectRatio:false,
                plugins: {{ legend:{{position:'bottom', labels:{{usePointStyle:true, pointStyle:'circle', padding:12}}}},
                    tooltip:{{callbacks:{{label:function(ctx){{ if(ctx.datasetIndex===0) return ' '+fmtN(ctx.raw); return ' Rating: '+fmtR(ctx.raw)+' ⭐'; }}}}}} }},
                scales: {{ x:{{grid:{{display:false}}}}, y:{{position:'left', grid:{{borderDash:[3,3]}}, ticks:{{callback:axF(false)}}, title:{{display:true,text:'Doanh Số',font:{{size:10}}}}}},
                    y1:{{position:'right', grid:{{drawOnChartArea:false}}, min:3.5, max:5.0, ticks:{{callback:v=>v.toFixed(1)+' ⭐'}}, title:{{display:true,text:'Rating',font:{{size:10}}}}}} }}
            }}
        }});

        // S3: Cat Delivery
        GI.cCatDeliv = new Chart(document.getElementById('cCatDeliv'), {{
            type:'bar',
            data: {{ labels:[], datasets:[
                {{ label:'Nhanh (≤7d)', data:[], backgroundColor:C.green, borderRadius:4, barPercentage:0.7 }},
                {{ label:'Chậm (>7d)', data:[], backgroundColor:C.red, borderRadius:4, barPercentage:0.7 }}
            ] }},
            options: {{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
                plugins: {{ legend:{{position:'top', labels:{{usePointStyle:true, pointStyle:'circle'}}}},
                    tooltip:{{callbacks:{{label:ttF(false)}}}} }},
                scales: {{ x:{{grid:{{borderDash:[3,3]}}, ticks:{{callback:axF(false)}}}}, y:{{grid:{{display:false}}}} }}
            }}
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
    """

    components.html(html_code, height=5200, scrolling=False)
