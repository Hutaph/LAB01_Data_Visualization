import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    from utils.constants import FEATURE_MAP
except ImportError:
    try:
        import utils.constants
        FEATURE_MAP = getattr(utils.constants, 'FEATURE_MAP', {})
    except ImportError:
        FEATURE_MAP = {}

def render(df_raw):
    """
    Hàm chính để render tab Phân tích Chất lượng Niêm yết (Thông tin sản phẩm).
    """
    # Khởi tạo dữ liệu làm việc từ dataframe gốc
    df = df_raw.copy()

    # TIỀN XỬ LÝ DỮ LIỆU
    # Chuyển đổi doanh số sang kiểu số, xử lý lỗi và giá trị thiếu
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0).astype(int)

    # Xử lý logic Danh mục sản phẩm (sử dụng CATEGORY_MAP từ constants nếu có)
    from utils.constants import CATEGORY_MAP
    if "crawl_category" in df.columns:
        df["Danh Mục Sản Phẩm"] = df["crawl_category"].map(CATEGORY_MAP).fillna(df["crawl_category"])
    else:
        df["Danh Mục Sản Phẩm"] = "Không Rõ"

    # TÍNH TOÁN CÁC NGƯỠNG PHÂN KHÚC GIÁ
    # Chuyển đổi giá sang số và xác định các điểm phân vị (quartiles)
    df["price_num"] = pd.to_numeric(df.get("price", 0), errors="coerce").fillna(0)
    price_nonzero = df["price_num"][df["price_num"] > 0]
    
    # Mốc 33% và 67% dùng để chia 3 phân khúc: Bình dân, Trung cấp, Cao cấp
    p33 = round(float(price_nonzero.quantile(0.33)), 2) if not price_nonzero.empty else 10.0
    p67 = round(float(price_nonzero.quantile(0.67)), 2) if not price_nonzero.empty else 30.0

    # ĐÁNH GIÁ MỨC ĐỘ ĐẦY ĐỦ THÔNG TIN (Listing Completeness)
    # Danh sách các cột KHÔNG dùng để đánh giá chất lượng nội dung niêm yết (ASIN, URL, các cột kỹ thuật...)
    exclude_cols = [
        'asin', 'link', 'slug', 'parent_asin', 'landing_asin', 'date', 
        'image_url', 'brand_url', 'brand_urls', 'crawl_category', 'Danh Mục Sản Phẩm',
        'discount', 'discount_rate',
        'frequently_bought_together', 'currency', 'min_order_quantity',
        # Các cột helper phục vụ trực quan hóa
        'price_num', 'price_clean', 'rating_clean',
        'delivery_date_text', 'delivery_ship_to', 'delivery_stock_note',
        # Loại bỏ các thông tin logistics biến động theo thời gian/vị trí
        'delivery_info', 'delivery_fee', 'estimated_delivery_date',
        # Loại bỏ các trường cấu trúc phức tạp hoặc review thô
        'top_reviews', 'detailed_rating',
        'is_amazon_choice', 'is_prime', 'is_bestseller', 'is_best_seller',
        'sales_volume', 'sales_volume_num'
    ]
    # eval_cols là danh sách các trường thông tin mô tả sản phẩm thực tế
    eval_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Định nghĩa các cột kiểu số (để xử lý riêng giá trị 0 là CÓ thông tin)
    quantitative_cols = [
        'rating', 'reviews', 'number_of_offers', 'lowest_offer_price', 
        'current_price', 'unit_price', 'unit_count', 'min_order_quantity'
    ]
    
    def is_missing_value(series, col_name):
        """Kiểm tra xem dữ liệu trong một cột có bị thiếu hay không."""
        s_str = series.astype(str).str.strip().str.lower()
        
        # Các giá trị cơ bản coi là thiếu: NaN, Rỗng, None, mảng/dict rỗng
        missing_vals = ["", "nan", "none", "[]", "{}"]
        
        # Với các trường KHÔNG phải định lượng: "false" hoặc "0" cũng coi là không có thông tin
        # Với các trường định lượng (quantitative): "0" vẫn được tính là có thông tin
        if col_name not in quantitative_cols:
            missing_vals.extend(["false", "0", "0.0"])
        else:
            missing_vals.extend(["false"])

        return s_str.isin(missing_vals) | series.isna()

    # Tạo mask đánh giá các trường bị thiếu
    missing_mask_dict = {col: is_missing_value(df[col], col) for col in eval_cols}
    missing_df = pd.DataFrame(missing_mask_dict)
    provided_df = ~missing_df

    # Tính tổng số trường thông tin bị thiếu cho mỗi sản phẩm
    df["missing_count"] = missing_df.sum(axis=1)
    total_features = len(eval_cols)
    
    # PHÂN TÍCH ĐẶC TÍNH (FEATURES) CỦA TOP 10% SẢN PHẨM BÁN CHẠY
    # Tính toán cho từng tổ hợp Danh mục x Phân khúc giá
    top_features_dict = {}
    all_features_dict = {}
    top_counts_dict = {}
    all_counts_dict = {}

    def calc_provided_features_with_count(sub_df, prov_mask):
        """Tính tỷ lệ và số lượng các trường thông tin được cung cấp trong một tập dữ liệu."""
        if len(sub_df) == 0: 
            return {}, {}
        
        prov_counts = prov_mask.loc[sub_df.index].sum()
        prov_pct = (prov_counts / len(sub_df) * 100).round(1)
        return prov_pct.to_dict(), prov_counts.to_dict()

    def calc_top_provided_features_with_count(sub_df, prov_mask):
        """Tính tỷ lệ và số lượng các trường thông tin được cung cấp cho TOP 10% sản phẩm bán chạy nhất."""
        if len(sub_df) == 0: 
            return {}, {}
            
        # Lấy Top 10% sản phẩm dựa trên doanh số
        top_n = max(1, int(len(sub_df) * 0.1))
        top_indices = sub_df.nlargest(top_n, "sales_volume_num").index
        
        if len(top_indices) == 0: 
            return {}, {}
            
        prov_counts = prov_mask.loc[top_indices].sum()
        prov_pct = (prov_counts / len(top_indices) * 100).round(1)
        return prov_pct.to_dict(), prov_counts.to_dict()

    # Định nghĩa các bộ lọc phân khúc giá
    price_segments = {
        "ALL": lambda d: d,
        "LOW": lambda d: d[d["price_num"] <= p33],
        "MID": lambda d: d[(d["price_num"] > p33) & (d["price_num"] <= p67)],
        "HIGH": lambda d: d[d["price_num"] > p67]
    }

    # Lặp qua tất cả danh mục và phân khúc để tính toán trước (Pre-calculate)
    unique_cats = ["ALL"] + list(df["Danh Mục Sản Phẩm"].unique())
    for cat in unique_cats:
        cat_df = df if cat == "ALL" else df[df["Danh Mục Sản Phẩm"] == cat]
        
        top_features_dict[cat] = {}
        all_features_dict[cat] = {}
        top_counts_dict[cat] = {}
        all_counts_dict[cat] = {}
        
        for seg_name, filter_fn in price_segments.items():
            seg_df = filter_fn(cat_df)
            t_p, t_c = calc_top_provided_features_with_count(seg_df, provided_df)
            a_p, a_c = calc_provided_features_with_count(seg_df, provided_df)
            
            top_features_dict[cat][seg_name] = t_p
            top_counts_dict[cat][seg_name] = t_c
            all_features_dict[cat][seg_name] = a_p
            all_counts_dict[cat][seg_name] = a_c

    # Chuyển đổi dữ liệu sang dạng JSON để truyền vào JavaScript
    top_feats_json_str = json.dumps(top_features_dict)
    all_feats_json_str = json.dumps(all_features_dict)
    top_counts_json_str = json.dumps(top_counts_dict)
    all_counts_json_str = json.dumps(all_counts_dict, ensure_ascii=False)

    # Chuẩn bị dữ liệu xuất bản (export) cho các biểu đồ chính
    select_cols = ["Danh Mục Sản Phẩm", "sales_volume_num", "missing_count", "price_num"]
    export_df = df[select_cols].copy()
    data_json = export_df.to_dict(orient="records")
    data_json_str = json.dumps(data_json, ensure_ascii=False)

    html_code = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        :root {{
            --primary: #F97316;
            --secondary: #FB923C;
            --dark: #9A3412;
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 8px;
            --font-family: 'Inter', sans-serif;
            --accent-emerald: #10b981;
            --accent-rose: #f43f5e;
            --accent-blue: #3b82f6;
            --accent-amber: #f59e0b;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            background-color: var(--bg);
            color: var(--text-primary);
            font-family: var(--font-family);
            height: 100vh;
            overflow: hidden;
            padding: 10px 14px;
        }}

        .filter-bar {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 10px;
            background: var(--card-bg);
            padding: 8px 16px;
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            flex-wrap: wrap;
        }}

        .f-item {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .f-label {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        select {{
            padding: 7px 12px;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            font-family: inherit;
            font-size: 13px;
            color: var(--text-primary);
            outline: none;
            cursor: pointer;
            width: 240px;
            background: #fff;
            transition: border-color 0.2s;
        }}
        select:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(249,115,22,0.1); }}

        .toggle-group {{
            display: flex;
            background: #F3F4F6;
            border-radius: 6px;
            padding: 3px;
            gap: 2px;
        }}
        .toggle-btn {{
            border: none;
            background: transparent;
            font-family: inherit;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            padding: 6px 14px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .toggle-btn.active {{
            background: #FFFFFF;
            color: var(--primary);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}


        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 10px;
        }}

        .kpi-card {{
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            padding: 8px 12px;
            border-left: 4px solid var(--primary);
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}

        .kpi-title {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kpi-val {{ font-size: 22px; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kpi-sub {{ font-size: 11px; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 4px; }}
        .trend-up {{ color: var(--accent-emerald); font-weight: 700; }}
        .trend-down {{ color: var(--accent-rose); font-weight: 700; }}

        .charts-wrapper {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: calc((100vh - 200px) / 2) calc((100vh - 200px) / 2);
            gap: 10px;
        }}

        .chart-card {{
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
        }}

        .chart-header {{ margin-bottom: 6px; }}
        .chart-title {{ font-size: 14px; font-weight: 700; margin-bottom: 3px; color: var(--text-primary); }}
        .chart-subtitle {{ font-size: 11px; color: var(--text-secondary); line-height: 1.4; }}
        .chart-container {{ flex: 1; position: relative; min-height: 0; width: 100%; }}

        .legend-row {{
            display: flex;
            gap: 16px;
            margin-top: 8px;
            justify-content: center;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 500;
        }}
        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
    </style>
</head>
<body>

    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Danh Mục Sản Phẩm</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả danh mục sản phẩm</option>
            </select>
        </div>
        <div class="f-item">
            <span class="f-label">Phân Khúc Giá</span>
            <select id="selPrice" onchange="applyFilters()">
                <option value="ALL">Tất cả phân khúc</option>
                <option value="LOW">Bình Dân (≤ {p33})</option>
                <option value="MID">Trung Cấp ({p33}–{p67})</option>
                <option value="HIGH">Cao Cấp (≥ {p67})</option>
            </select>
        </div>
        <div class="f-item">
            <span class="f-label">Chỉ Số Doanh Số</span>
            <div class="toggle-group">
                <button class="toggle-btn active" id="btn_mean" onclick="setMetric('mean')">Mean</button>
                <button class="toggle-btn" id="btn_median" onclick="setMetric('median')">Median</button>
            </div>
        </div>
        <div style="margin-left:auto; display:flex; flex-direction:column; align-items:flex-end; justify-content:center;">
            <div style="font-size:16px; font-weight:800; color:var(--dark);">PHÂN TÍCH THÔNG TIN SẢN PHẨM & DOANH SỐ</div>
            <div style="font-size:11px; color:var(--text-secondary); font-weight:500;">Mối liên hệ giữa mức độ thiếu thông tin và hiệu quả bán hàng</div>
        </div>
    </div>


    <!-- KPI ROW -->
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title" id="kpi_sales_title">Doanh Số Nhóm Đầy Đủ Nhất</div>
            <div class="kpi-val" id="kpi_sales_good">0</div>
            <div class="kpi-sub" id="kpi_sales_diff">-</div>
        </div>
        <div class="kpi-card" style="border-left-color: #9A3412;">
            <div class="kpi-title">Bỏ Trống Trung Bình Toàn Ngành</div>
            <div class="kpi-val" id="kpi_missing_avg">0</div>
            <div class="kpi-sub">Trên tổng {total_features} trường thông tin</div>
        </div>
        <div class="kpi-card" style="border-left-color: #F59E0B;">
            <div class="kpi-title">Trường Thông Tin #1 Của Top Doanh Số</div>
            <div class="kpi-val" style="font-size: 17px" id="kpi_top_feat">-</div>
            <div class="kpi-sub">Xuất hiện nhiều nhất ở sản phẩm bán chạy</div>
        </div>
        <div class="kpi-card" style="border-left-color: var(--accent-blue);">
            <div class="kpi-title">Tổng Sản Phẩm Đang Phân Tích</div>
            <div class="kpi-val" id="kpi_total_products">0</div>
            <div class="kpi-sub">Tổng sản phẩm theo bộ lọc</div>
        </div>
    </div>

    <!-- CHARTS -->
    <div class="charts-wrapper">
        
        <div class="chart-card" id="card_trend">
            <div class="chart-header">
                <div class="chart-title">Sự Chuyển Biến Doanh Số</div>
                <div class="chart-subtitle">Trục X: Số Trường Thông Tin Thiếu | Trục Y: Doanh Số & Số Lượng Sản Phẩm</div>
            </div>
            <div class="chart-container"><canvas id="c_trend"></canvas></div>
        </div>

        <div class="chart-card" id="card_features">
            <div class="chart-header">
                <div class="chart-title">Trường Thông Tin Phân Hoá: Top 10% Doanh Số so với Toàn Bộ</div>
                <div class="chart-subtitle">Top các feature có mức độ chênh lệch tỷ lệ xuất hiện cao nhất</div>
            </div>
            <div class="chart-container"><canvas id="c_features"></canvas></div>
        </div>

        <div class="chart-card" id="card_missing">
            <div class="chart-header">
                <div class="chart-title">Mức Độ Tập Trung Theo Nhóm Thông Tin Thiếu</div>
                <div class="chart-subtitle">Đường đỏ (10%): Tỷ lệ kỳ vọng ngẫu nhiên (Baseline)</div>
            </div>
            <div class="chart-container">
                <canvas id="c_top_missing_dist"></canvas>
            </div>
        </div>

        <div class="chart-card" id="card_top10">
            <div class="chart-header">
                <div class="chart-title">Mức Độ Tập Trung Ở Top 10% Doanh Số</div>
                <div class="chart-subtitle">Đường đỏ (10%): Tỷ lệ kỳ vọng ngẫu nhiên (Baseline)</div>
            </div>
            <div class="chart-container"><canvas id="c_concentration"></canvas></div>
        </div>
    </div>

<script>
    // KHỞI TẠO DỮ LIỆU CHO JAVASCRIPT
    const RAW_DATA = {data_json_str};              // Dữ liệu sản phẩm thô (danh mục, doanh số, số trường thiếu)
    const TOP_FEATS_DATA = {top_feats_json_str};   // Tỷ lệ feature của Top 10% doanh số
    const ALL_FEATS_DATA = {all_feats_json_str};   // Tỷ lệ feature trung bình toàn ngành
    const TOP_COUNTS_DATA = {top_counts_json_str}; // Số lượng feature của Top 10% doanh số
    const ALL_COUNTS_DATA = {all_counts_json_str}; // Số lượng feature toàn ngành
    const FEATURE_MAP = {json.dumps(FEATURE_MAP, ensure_ascii=False)}; // Bản đồ tên feature thân thiện
    const TOTAL_FEATS = {total_features};           // Tổng số trường thông tin đánh giá
    const PRICE_T1 = {p33}; // Ngưỡng trên của phân khúc Bình Dân
    const PRICE_T2 = {p67}; // Ngưỡng trên của phân khúc Trung Cấp
    
    let CHARTS = {{}};      // Lưu trữ các đối tượng Chart.js
    let METRIC = 'mean';   // Chỉ số doanh số hiển thị: 'mean' (trung bình) hoặc 'median' (trung vị)

    function _slugify(s) {{
        return String(s || '')
            .trim()
            .toLowerCase()
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '')
            .slice(0, 64) || 'all';
    }}


    function median(arr) {{
        /** Tính toán giá trị trung vị (median) của một mảng số */
        if (!arr.length) return 0;
        let sorted = [...arr].sort((a,b) => a - b);
        let mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid-1] + sorted[mid]) / 2;
    }}

    function setMetric(m) {{
        /** Chuyển đổi giữa hiển thị Mean (Trung bình) và Median (Trung vị) */
        METRIC = m;
        document.getElementById('btn_mean').classList.toggle('active', m === 'mean');
        document.getElementById('btn_median').classList.toggle('active', m === 'median');
        
        // Cập nhật tiêu đề KPI và nhãn trục Y của biểu đồ xu hướng
        document.getElementById('kpi_sales_title').innerText = m === 'mean' ? 'Doanh Số Trung Bình (Nhóm Tốt Nhất)' : 'Doanh Số Trung Vị (Nhóm Tốt Nhất)';
        if (CHARTS.trend) {{
            CHARTS.trend.options.scales.y.title.text = m === 'mean' ? 'Doanh Số Mean (lượt bán)' : 'Doanh Số Median (lượt bán)';
        }}
        applyFilters();
    }}

    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n)); // Định dạng số kiểu phân cách hàng ngàn

    function setup() {{
        // Cấu hình mặc định cho Chart.js
        Chart.register(ChartDataLabels);
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.family = "'Inter', sans-serif";
        
        // Khởi tạo danh sách các danh mục sản phẩm vào dropdown
        let cats = new Set();
        RAW_DATA.forEach(d => {{ if(d['Danh Mục Sản Phẩm'] && d['Danh Mục Sản Phẩm'] !== 'Không Rõ') cats.add(d['Danh Mục Sản Phẩm']); }});
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option'); opt.value = c; opt.innerText = c; sel.appendChild(opt);
        }});

        // Khởi tạo các biểu đồ và áp dụng bộ lọc ban đầu
        initCharts();
        applyFilters();
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let seg = document.getElementById('selPrice').value;
        
        // Lọc dữ liệu thô dựa trên Danh mục và Phân khúc giá đã chọn
        let data = RAW_DATA.filter(d => {{
            let catOk = (cat === 'ALL' || d['Danh Mục Sản Phẩm'] === cat);
            let price = d.price_num || 0;
            let segOk = seg === 'ALL'
                ? true
                : seg === 'LOW' ? price <= PRICE_T1
                : seg === 'MID' ? (price > PRICE_T1 && price <= PRICE_T2)
                : price > PRICE_T2; // HIGH
            return catOk && segOk;
        }});
        processData(data, cat);
    }}

    function processData(data, cat) {{
        if (!data.length) return;

        // 1. PHÂN NHÓM (BINNING) DỮ LIỆU ĐỂ TRỰC QUAN HÓA
        // Gộp sản phẩm theo số trường thông tin thiếu
        let freqMap = new Map();
        data.forEach(d => {{
            let m = d.missing_count;
            // Gộp tất cả sản phẩm thiếu từ 34 trường trở lên vào nhóm '34+'
            let key = (m >= 34) ? 999 : m;
            if (!freqMap.has(key)) freqMap.set(key, {{ count: 0, products: [], vals: [] }});
            let entry = freqMap.get(key);
            entry.count++;
            entry.products.push(d);
            if (!entry.vals.includes(m)) entry.vals.push(m);
        }});

        let sortedKeys = Array.from(freqMap.keys()).sort((a,b) => a - b);
        let targetSize = data.length / 7; // Mục tiêu chia dữ liệu thành ~7 nhóm để biểu đồ cân đối
        let bins = [];
        let curBin = {{ vals: [], products: [], count: 0 }};
        
        // Các mốc chia quan trọng được yêu cầu để giữ logic phân tích
        const FORCED = [15, 18, 28, 999];

        sortedKeys.forEach((v, idx) => {{
            let entry = freqMap.get(v);
            let wouldBeTooBig = (curBin.count + entry.count > targetSize * 1.5);
            let isHalfFull = (curBin.count > targetSize * 0.7);
            let isForced = FORCED.includes(v);

            // Chốt nhóm nếu vượt quá kích thước mục tiêu hoặc gặp mốc quan trọng
            if (bins.length < 6 && curBin.count > 0 && (wouldBeTooBig || isHalfFull || isForced)) {{
                bins.push(curBin);
                curBin = {{ vals: entry.vals, products: entry.products, count: entry.count }};
            }} else {{
                curBin.vals = curBin.vals.concat(entry.vals);
                curBin.products = curBin.products.concat(entry.products);
                curBin.count += entry.count;
            }}
        }});
        if (curBin.count > 0) bins.push(curBin);

        // Chuyển đổi các nhóm (bins) sang định dạng hiển thị trên biểu đồ
        let chartBins = bins.map(b => {{
            b.vals.sort((a,b) => a - b);
            let minM = b.vals[0];
            let maxM = b.vals[b.vals.length - 1];
            let label = (minM >= 34) ? '34+' : (minM === maxM ? `${{minM}}` : `${{minM}}-${{maxM}}`);
            return {{
                label: label,
                salesArr: b.products.map(p => p.sales_volume_num),
                count: b.count,
                chunk: b.products
            }};
        }});

        // Gộp thêm các nhóm đặc thù (ví dụ: nhóm 29 và 30-31) để biểu đồ gọn hơn
        const mergedBins = [];
        for (let i = 0; i < chartBins.length; i++) {{
            const cur = chartBins[i];
            const nxt = chartBins[i + 1];
            if (cur && nxt && cur.label === '29' && (nxt.label === '30-31' || nxt.label === '30' || nxt.label.startsWith('30-31'))) {{
                mergedBins.push({{
                    label: '29-31',
                    salesArr: cur.salesArr.concat(nxt.salesArr),
                    count: cur.count + nxt.count,
                    chunk: cur.chunk.concat(nxt.chunk),
                }});
                i += 1;
                continue;
            }}
            mergedBins.push(cur);
        }}
        chartBins = mergedBins;

        // 2. Chart 1: Sales Trend & Quantity
        const trendLabels = chartBins.map(b => b.label);
        const trendSales = chartBins.map(b => {{
            if (METRIC === 'median') return Math.round(median(b.salesArr));
            return Math.round(b.salesArr.reduce((s,v) => s+v, 0) / b.count);
        }});
        const trendCounts = chartBins.map(b => b.count);

        // 3. KPIs
        let totalMissing = 0;
        data.forEach(d => totalMissing += d.missing_count);
        let avgMissing = totalMissing / data.length;

        document.getElementById('kpi_missing_avg').innerText = Math.round(avgMissing);
        let statTop = trendSales[0]; // Best group (least missing)
        let statBot = trendSales[trendSales.length - 1]; // Worst group
        document.getElementById('kpi_sales_good').innerText = statTop > 0 ? fmtN(statTop) : 0;
        document.getElementById('kpi_total_products').innerText = fmtN(data.length);

        let diff_el = document.getElementById('kpi_sales_diff');
        let diff = statTop - statBot;
        if (chartBins.length >= 2) {{
            if (diff > 0) {{
                diff_el.innerHTML = `So với nhóm thiếu nhiều nhất: <span class="trend-up">Cao hơn +${{fmtN(diff)}}</span>`;
            }} else if (diff < 0) {{
                diff_el.innerHTML = `So với nhóm thiếu nhiều nhất: <span class="trend-down">Thấp hơn ${{fmtN(Math.abs(diff))}}</span>`;
            }} else {{
                diff_el.innerHTML = `<span style="color:#9CA3AF">Bằng với nhóm tệ nhất</span>`;
            }}
        }} else {{
            diff_el.innerHTML = `<span style="color:#9CA3AF">Không đủ dữ liệu so sánh</span>`;
        }}

        // Dynamic Features KPI
        let segCurrent = document.getElementById('selPrice').value;
        let topFeatData = (TOP_FEATS_DATA[cat] && TOP_FEATS_DATA[cat][segCurrent]) || {{}};
        let allFeatData = (ALL_FEATS_DATA[cat] && ALL_FEATS_DATA[cat][segCurrent]) || {{}};
        
        let diffsList = Object.keys(topFeatData).map(f => ({{
            f: f, diff: (topFeatData[f] || 0) - (allFeatData[f] || 0), t: topFeatData[f] || 0
        }})).filter(item => item.t > 5).sort((a,b) => b.diff - a.diff);
        
        let kpiFeatEl = document.getElementById('kpi_top_feat');
        let kpiTitleEl = kpiFeatEl.previousElementSibling;
        let kpiSubEl = kpiFeatEl.nextElementSibling;
        
        if (diffsList.length > 0 && diffsList[0].diff > 0.1) {{
            let fBest = diffsList[0];
            kpiTitleEl.innerText = "Feature Tạo Sự Khác Biệt";
            kpiFeatEl.innerText = FEATURE_MAP[fBest.f] || fBest.f;
            kpiSubEl.innerHTML = `Chênh lệch <span class="trend-up">+${{fBest.diff.toFixed(1)}}%</span> so với trung bình`;
        }} else {{
            kpiTitleEl.innerText = "Thông tin Quan trọng";
            kpiFeatEl.innerText = "N/A";
            kpiSubEl.innerText = "Chưa có dữ liệu phân hoá";
        }}

        updateTrendChart(trendLabels, trendSales, trendCounts);

        // Chart 2: Feature Distribution Diffs
        let featsList = Object.keys(topFeatData).map(f => ({{
            f: f, diff: (topFeatData[f] || 0) - (allFeatData[f] || 0)
        }})).sort((a,b) => b.diff - a.diff).slice(0, 7);
        updateFeaturesChart(featsList.map(d => FEATURE_MAP[d.f] || d.f), featsList.map(d => d.diff));

        // Chart 3: Concentration
        let tCounts = (TOP_COUNTS_DATA[cat] && TOP_COUNTS_DATA[cat][segCurrent]) || {{}};
        let aCounts = (ALL_COUNTS_DATA[cat] && ALL_COUNTS_DATA[cat][segCurrent]) || {{}};
        let MIN_C = Math.max(10, data.length * 0.01);
        let concList = Object.keys(aCounts).map(f => {{
            if (aCounts[f] < MIN_C) return null;
            return {{ f: f, t: tCounts[f] || 0, a: aCounts[f], p: ((tCounts[f] || 0)/aCounts[f])*100 }};
        }}).filter(i => i !== null).sort((a,b) => b.p - a.p).slice(0, 7);
        updateConcentrationChart(concList.map(d => FEATURE_MAP[d.f] || d.f), concList.map(d => d.p), concList.map(d => 100-d.p), concList.map(d => ({{t: d.t, a: d.a}})));

        // Chart 4: Missing Distribution (Concentration into Top 10% Sales)
        const sortedSales = [...data].sort((a,b) => b.sales_volume_num - a.sales_volume_num);
        const t10S = Math.max(1, Math.floor(sortedSales.length * 0.1));
        const t10T = sortedSales.length >= t10S ? sortedSales[t10S-1].sales_volume_num : 0;

        let dL = [], dTop = [], dRest = [], dRaw = [];
        chartBins.forEach(b => {{
            let topC = b.chunk.filter(d => d.sales_volume_num >= t10T && d.sales_volume_num > 0).length;
            let p = (topC / b.count) * 100;
            dL.push(b.label + ' Thiếu');
            dTop.push(p);
            dRest.push(100 - p);
            dRaw.push({{ t: topC, a: b.count }});
        }});

        CHARTS.missingDist._rawCounts = dRaw;
        CHARTS.missingDist.data.labels = dL;
        CHARTS.missingDist.data.datasets[0].data = dTop;
        CHARTS.missingDist.data.datasets[1].data = dRest;
        CHARTS.missingDist.update();
    }}

    function updateTrendChart(labels, salesData, countData) {{
        CHARTS.trend.data.labels = labels;
        CHARTS.trend.data.datasets[0].data = salesData;
        CHARTS.trend.data.datasets[1].data = countData;

        // Find max count for right Y axis scaling
        let maxCount = Math.max(...countData, 1);
        CHARTS.trend.options.scales.y1.max = Math.ceil(maxCount * 1.3);
        CHARTS.trend.update();
    }}

    function updateFeaturesChart(labels, diffData) {{
        CHARTS.features.data.labels = labels;
        CHARTS.features.data.datasets[0].data = diffData;
        CHARTS.features.update();
    }}

    function updateConcentrationChart(labels, topData, restData, countsData) {{
        CHARTS.concentration.data.labels = labels;
        CHARTS.concentration.data.datasets[0].data = topData;
        CHARTS.concentration.data.datasets[1].data = restData;
        CHARTS.concentration._rawCounts = countsData; // For tooltips
        CHARTS.concentration.update();
    }}

    function initCharts() {{
        // Chart 1: Dual-axis Area + Bar (Trend)
        let ctxTrend = document.getElementById('c_trend').getContext('2d');
        
        // Create gradient for line fill
        let gradientFill = ctxTrend.createLinearGradient(0, 0, 0, 400);
        gradientFill.addColorStop(0, 'rgba(249, 115, 22, 0.25)');
        gradientFill.addColorStop(1, 'rgba(249, 115, 22, 0.02)');

        CHARTS.trend = new Chart(ctxTrend, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Doanh Số Trung Bình',
                        type: 'line',
                        data: [],
                        borderColor: '#ea580c',
                        backgroundColor: gradientFill,
                        borderWidth: 2.5,
                        tension: 0.35,
                        fill: true,
                        pointBackgroundColor: '#fff',
                        pointBorderColor: '#ea580c',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y',
                        order: 1,
                        datalabels: {{
                            display: function(ctx) {{
                                // Show datalabel only for first, peak, and last point
                                let d = ctx.dataset.data;
                                let i = ctx.dataIndex;
                                if (i === 0 || i === d.length - 1) return true;
                                let maxVal = Math.max(...d);
                                if (d[i] === maxVal) return true;
                                return false;
                            }},
                            color: '#ea580c',
                            font: {{ weight: '700', size: 11 }},
                            formatter: (v) => fmtN(v),
                            anchor: 'end',
                            align: 'top',
                            offset: 4,
                            clamp: true,
                            clip: false
                        }}
                    }},
                    {{
                        label: 'Số Lượng Sản Phẩm',
                        type: 'bar',
                        data: [],
                        backgroundColor: 'rgba(251, 146, 60, 0.3)',
                        borderColor: 'rgba(251, 146, 60, 0.5)',
                        borderWidth: 1,
                        borderRadius: 3,
                        yAxisID: 'y1',
                        order: 2,
                        datalabels: {{ display: false }}
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{ top: 18 }}
                }},
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                scales: {{
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 0 }},
                        title: {{ display: true, text: 'Số Trường Thông Tin Thiếu', color: '#78716C', font: {{ size: 11, weight: '600' }} }}
                    }},
                    y: {{
                        position: 'left',
                        grid: {{ color: 'rgba(0,0,0,0.04)' }},
                        ticks: {{ callback: (v) => fmtN(v), font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Doanh Số Mean (lượt bán)', color: '#ea580c', font: {{ size: 11, weight: '600' }} }},
                        grace: '12%'
                    }},
                    y1: {{
                        position: 'right',
                        grid: {{ drawOnChartArea: false }},
                        ticks: {{ font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Số Lượng Sản Phẩm', color: 'rgba(251,146,60,0.8)', font: {{ size: 11, weight: '600' }} }},
                        max: 100
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(28,25,23,0.92)',
                        titleFont: {{ size: 12, weight: '600' }},
                        bodyFont: {{ size: 11 }},
                        padding: 10,
                        cornerRadius: 6,
                        callbacks: {{
                            title: function(tooltipItems) {{
                                return 'Thiếu ' + tooltipItems[0].label + ' trường thông tin';
                            }},
                            label: function(ctx) {{
                                if (ctx.datasetIndex === 0) return '  Doanh Số Trung Bình: ' + fmtN(ctx.raw) + ' lượt';
                                return '  Số Sản Phẩm: ' + fmtN(ctx.raw) + ' sản phẩm';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Chart 2: Difference Bar Chart (Feature comparison)
        let ctxFeats = document.getElementById('c_features').getContext('2d');
        CHARTS.features = new Chart(ctxFeats, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Chênh lệch (% Sản phẩm)',
                        data: [],
                        backgroundColor: 'rgba(249, 115, 22, 0.75)',
                        borderColor: '#ea580c',
                        borderWidth: 1,
                        borderRadius: 3,
                        barPercentage: 0.8
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {{
                    // Prevent right-side labels from being clipped.
                    padding: {{ right: 28 }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(0,0,0,0.04)' }},
                        ticks: {{ callback: (v) => (v > 0 ? '+' : '') + v + '%', font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Mức độ ảnh hưởng (Chênh lệch % độ phủ)', color: '#78716C', font: {{ size: 11, weight: '600' }} }},
                        grace: '10%',
                        suggestedMax: 20
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 10, weight: '500' }}, color: '#44403C' }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    datalabels: {{
                        display: true,
                        color: '#9A3412',
                        font: {{ weight: '800', size: 11 }},
                        formatter: (v) => (v > 0 ? '+' : '') + v.toFixed(1) + '%',
                        anchor: 'end',
                        align: 'right',
                        offset: 6,
                        clamp: true,
                        clip: false
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(28,25,23,0.92)',
                        titleFont: {{ size: 12, weight: '600' }},
                        bodyFont: {{ size: 11 }},
                        padding: 10,
                        cornerRadius: 6,
                        callbacks: {{
                            label: function(ctx) {{
                                let v = ctx.raw;
                                return `  Phổ biến hơn ${{v > 0 ? '+' : ''}}${{v.toFixed(1)}}% ở nhóm Top 10% Doanh Số`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Chart 3: Concentration 100% Stacked Bar
        let ctxConc = document.getElementById('c_concentration').getContext('2d');
        CHARTS.concentration = new Chart(ctxConc, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Thuộc Top 10% Doanh số',
                        data: [],
                        backgroundColor: 'rgba(234, 179, 8, 0.85)', // Amber/Yellow
                        barPercentage: 0.7,
                        categoryPercentage: 0.8
                    }},
                    {{
                        label: 'Phần Còn Lại (90%)',
                        data: [],
                        backgroundColor: 'rgba(214, 211, 209, 0.4)', // Light gray
                        barPercentage: 0.7,
                        categoryPercentage: 0.8
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        grid: {{ color: 'rgba(0,0,0,0.04)' }},
                        ticks: {{ callback: v => v + '%', font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Tỷ trọng % Đặc tính', color: '#78716C', font: {{ size: 11, weight: '600' }} }}
                    }},
                    y: {{
                        stacked: true,
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 10, weight: '500' }}, color: '#44403C' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true, position: 'bottom',
                        labels: {{ boxWidth: 12, boxHeight: 12, useBorderRadius: true, borderRadius: 3, padding: 16, font: {{ size: 11, weight: '500' }} }}
                    }},
                    datalabels: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(28,25,23,0.92)',
                        titleFont: {{ size: 12, weight: '600' }},
                        bodyFont: {{ size: 11 }},
                        padding: 10, cornerRadius: 6,
                        callbacks: {{
                            label: function(ctx) {{
                                let label = ctx.dataset.label;
                                let pct = ctx.raw.toFixed(1);
                                let d = CHARTS.concentration._rawCounts[ctx.dataIndex]; 
                                let count = ctx.datasetIndex === 0 ? d.t : (d.a - d.t);
                                return `  ${{label}}: ${{pct}}%  (${{count}} sp)`;
                            }},
                            afterBody: function(ctx) {{
                                let d = CHARTS.concentration._rawCounts[ctx[0].dataIndex];
                                let topPct = ctx[0].chart.data.datasets[0].data[ctx[0].dataIndex];
                                let upliftX = (topPct / 10).toFixed(1);
                                return `\n  Tổng Sản Phẩm chứa thông tin này: ${{d.a}}\n  Độ tập trung gấp ${{upliftX}} lần mức kỳ vọng ngẫu nhiên`;
                            }}
                        }}
                    }}
                }}
            }},
            plugins: [{{
                id: 'baseline10',
                afterDatasetDraw: (chart) => {{
                    const {{ctx, chartArea: {{top, bottom}}, scales: {{x}} }} = chart;
                    let xPos = x.getPixelForValue(10);
                    ctx.save();
                    ctx.beginPath();
                    ctx.lineWidth = 1.5;
                    ctx.strokeStyle = '#ef4444'; // red-500
                    ctx.setLineDash([4, 4]);
                    ctx.moveTo(xPos, top);
                    ctx.lineTo(xPos, bottom);
                    ctx.stroke();
                    ctx.restore();
                }}
            }}]
        }});

        // Chart 4: Missing Distribution Concentration (Stacked Bar)
        let ctxMissDist = document.getElementById('c_top_missing_dist').getContext('2d');
        CHARTS.missingDist = new Chart(ctxMissDist, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Thuộc Top 10% Doanh số',
                        data: [],
                        backgroundColor: 'rgba(249, 115, 22, 0.85)', // Orange
                        barPercentage: 0.7,
                        categoryPercentage: 0.8
                    }},
                    {{
                        label: 'Phần Còn Lại (90%)',
                        data: [],
                        backgroundColor: 'rgba(214, 211, 209, 0.4)', // Light gray
                        barPercentage: 0.7,
                        categoryPercentage: 0.8
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        grid: {{ color: 'rgba(0,0,0,0.04)' }},
                        ticks: {{ callback: v => v + '%', font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Tỷ trọng % Nhóm', color: '#78716C', font: {{ size: 11, weight: '600' }} }}
                    }},
                    y: {{
                        stacked: true,
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 10, weight: '500' }}, color: '#44403C' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true, position: 'bottom',
                        labels: {{ boxWidth: 12, boxHeight: 12, useBorderRadius: true, borderRadius: 3, padding: 16, font: {{ size: 11, weight: '500' }} }}
                    }},
                    datalabels: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(28,25,23,0.92)',
                        titleFont: {{ size: 12, weight: '600' }},
                        bodyFont: {{ size: 11 }},
                        padding: 10, cornerRadius: 6,
                        callbacks: {{
                            label: function(ctx) {{
                                let label = ctx.dataset.label;
                                let pct = ctx.raw.toFixed(1);
                                let d = CHARTS.missingDist._rawCounts[ctx.dataIndex]; 
                                let count = ctx.datasetIndex === 0 ? d.t : (d.a - d.t);
                                return `  ${{label}}: ${{pct}}%  (${{count}} sp)`;
                            }},
                            afterBody: function(ctx) {{
                                let d = CHARTS.missingDist._rawCounts[ctx[0].dataIndex];
                                let topPct = ctx[0].chart.data.datasets[0].data[ctx[0].dataIndex];
                                let upliftX = (topPct / 10).toFixed(1);
                                return `\n  Tổng Sản Phẩm trong nhóm này: ${{d.a}}\n  Độ tập trung gấp ${{upliftX}} lần mức kỳ vọng ngẫu nhiên`;
                            }}
                        }}
                    }}
                }}
            }},
            plugins: [{{
                id: 'baseline10_miss',
                afterDatasetDraw: (chart) => {{
                    const {{ctx, chartArea: {{top, bottom}}, scales: {{x}} }} = chart;
                    let xPos = x.getPixelForValue(10);
                    ctx.save();
                    ctx.setLineDash([5, 5]);
                    ctx.strokeStyle = '#ef4444';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(xPos, top);
                    ctx.lineTo(xPos, bottom);
                    ctx.stroke();
                    ctx.restore();
                }}
            }}]
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
    """
    
    components.html(html_code, height=800, scrolling=False)
