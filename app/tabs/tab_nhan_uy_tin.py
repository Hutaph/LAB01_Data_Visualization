import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def render(df_raw):
    df = df_raw.copy()

    # ══════════════════════════════════════════════════════════════
    # 1. TIỀN XỬ LÝ DỮ LIỆU & MAPPING DANH MỤC
    # ══════════════════════════════════════════════════════════════
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

    if "is_amazon_choice" not in df.columns:
        df["is_amazon_choice"] = False
    else:
        df["is_amazon_choice"] = df["is_amazon_choice"].fillna(False).astype(bool)
        
    if "is_best_seller" not in df.columns:
        df["is_best_seller"] = True

    if "is_prime" not in df.columns:
        df["is_prime"] = False
    else:
        df["is_prime"] = df["is_prime"].fillna(False).astype(bool)

    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"
    else:
        df["crawl_category"] = df["crawl_category"].fillna("Không rõ").map(CATEGORY_MAP).fillna("Khác")

    df["current_price"] = pd.to_numeric(df.get("price", 0), errors="coerce").fillna(0.0)
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0)
    df["rating_val"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0.0)
    df["reviews_val"] = pd.to_numeric(df.get("reviews", 0), errors="coerce").fillna(0)
    
    if "title" not in df.columns:
        df["title"] = "Sản phẩm ẩn danh"
    else:
        df["title"] = df["title"].fillna("Sản phẩm ẩn danh")

    # Tạo phân khúc giá
    def get_price_tier(p):
        if p < 25: return "1. Bình dân (<$25)"
        elif p < 50: return "2. Phổ thông ($25-$50)"
        elif p < 100: return "3. Trung cấp ($50-$100)"
        else: return "4. Cao cấp (>$100)"
    df["price_tier"] = df["current_price"].apply(get_price_tier)

    # ══════════════════════════════════════════════════════════════
    # 2. XUẤT JSON CHO CHART.JS
    # ══════════════════════════════════════════════════════════════
    select_cols = [
        "title", "crawl_category", "is_amazon_choice", "is_best_seller", 
        "current_price", "sales_volume_num", "rating_val", "reviews_val", "is_prime", "price_tier"
    ]
    export_df = df[select_cols].copy()
    data_json_str = export_df.to_json(orient="records", force_ascii=False)

    # ══════════════════════════════════════════════════════════════
    # 3. HTML/CSS/JS CHUẨN ĐỒNG BỘ
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

        /* ── SECTION WRP ── */
        .section-wrapper {{ position: relative; margin-top: 10px; }}
        .section-sticky {{
            position: relative; z-index: 100;
            background: var(--bg); padding: 8px 0 6px 0;
            border-bottom: 2px solid var(--primary-light);
            margin-bottom: 14px;
        }}
        .section-title-row {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; }}
        .section-title {{
            display: flex; align-items: center; gap: 7px;
            font-size: 13px; font-weight: 800; color: var(--dark); text-transform: uppercase; letter-spacing: 0.3px;
        }}
        .section-title .num {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; border-radius: 50%; background: var(--primary);
            color: white; font-size: 12px; font-weight: 700; flex-shrink: 0;
        }}
        
        .header-filters {{ display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}
        .hf-item {{ display: flex; align-items: center; gap: 4px; }}
        .hf-label {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; }}
        select, input.range {{
            padding: 5px 8px; border: 1px solid #D6D3D1; border-radius: 5px;
            font-family: inherit; font-size: 11px; color: var(--text-primary); outline: none; background: white;
        }}

        /* ── OBJECTIVE  ── */
        .obj-card {{
            background: linear-gradient(135deg, #FFFAF5 0%, #FFF7ED 100%);
            border: 1px solid #FED7AA; border-radius: var(--border-radius);
            padding: 16px 20px; margin-bottom: 12px;
        }}
        .obj-title {{ font-size: 12px; font-weight: 700; color: var(--dark); text-transform: uppercase; margin-bottom: 5px; }}
        .obj-text {{ font-size: 12.5px; line-height: 1.65; color: #44403C; }}
        
        /* ── KPIs ── */
        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; }}
        .kpi-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 12px 14px;
            box-shadow: var(--shadow-sm); border-left: 4px solid var(--primary);
            display: flex; flex-direction: column; gap: 1px; transition: transform 0.15s;
        }}
        .kpi-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
        .kpi-title {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; }}
        .kpi-value {{ font-size: 20px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }}
        .kpi-sub {{ font-size: 9.5px; color: var(--text-secondary); font-weight: 500; }}
        .kpi-card.c-green {{ border-left-color: var(--success); }}
        .kpi-card.c-blue {{ border-left-color: var(--secondary); }}
        .kpi-card.c-red {{ border-left-color: var(--danger); }}
        .kpi-card.c-amber {{ border-left-color: var(--warning); }}

        /* ── CHARTS ── */
        .chart-row {{ display: flex; gap: 14px; margin-bottom: 14px; align-items: stretch; }}
        .chart-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 16px;
            box-shadow: var(--shadow-sm); display: flex; flex-direction: column; flex: 1; min-width: 0;
        }}
        .chart-header {{ margin-bottom: 10px; }}
        .chart-title {{ font-size: 12.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }}
        .chart-subtitle {{ font-size: 10.5px; color: var(--text-secondary); line-height: 1.4; }}
        .chart-wrapper {{ position: relative; width: 100%; flex-grow: 1; min-height: 250px; }}

        /* ── INSIGHT BOXES ── */
        .insight-box {{
            background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
            border: 1px solid #A7F3D0; border-left: 4px solid var(--success);
            border-radius: var(--border-radius); padding: 14px 18px; margin-bottom: 14px;
            display: flex; gap: 10px; align-items: flex-start;
        }}
        .insight-box.amber {{
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border-color: #FDE68A; border-left-color: var(--warning);
        }}
        .insight-icon {{ font-size: 18px; flex-shrink: 0; }}
        .insight-content {{ flex: 1; }}
        .insight-label {{ font-size: 10.5px; font-weight: 700; color: var(--success); text-transform: uppercase; margin-bottom: 3px; }}
        .insight-box.amber .insight-label {{ color: #B45309; }}
        .insight-text {{ font-size: 12px; line-height: 1.7; color: #374151; }}

        /* ── TABLES ── */
        table {{
            width: 100%; border-collapse: collapse; font-size: 11.5px;
            table-layout: fixed;
        }}
        th {{
            background: #F5F5F4; color: var(--text-secondary); font-weight: 700; font-size: 10px;
            text-align: left; padding: 10px 8px; text-transform: uppercase; border-bottom: 2px solid #E7E5E4;
        }}
        th:first-child {{ width: 45%; }}
        td {{ padding: 10px 8px; border-bottom: 1px solid #E5E7EB; }}
        .truncate-col {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    </style>
</head>
<body>

    <!-- OBJECTIVE PANE -->
    <div class="obj-card">
        <div class="obj-title">📍 TỔNG QUAN PHÂN TÍCH NHÃN HIỆU (AMAZON'S CHOICE)</div>
        <div class="obj-text">
            <strong>Ghi nhận dữ liệu:</strong> 100% sản phẩm đầu vào đều là <strong>Best Seller</strong>. <br>
            Do đó, mục tiêu của Dashboard này là <strong>Đào sâu giá trị gia tăng của nhãn Amazon's Choice</strong>: Nhãn này có tác động như thế nào đến giá niêm yết, tỉ lệ đánh giá và quan trọng nhất là mức chênh lệch doanh số bán ra vượt bậc trong chính tập hàng đầu.
        </div>
    </div>

    <!-- MAIN SECTION -->
    <div class="section-wrapper">
        <div class="section-sticky">
            <div class="section-title-row">
                <div class="section-title"><span class="num">1</span> BÁO CÁO TOÀN DIỆN: AMAZON'S CHOICE VS BEST SELLER TỰ NHIÊN</div>
                <div class="header-filters">
                    <div class="hf-item"><span class="hf-label">Danh Mục (Đã Map Tiếng Việt):</span>
                        <select id="selCategory" onchange="applyFilters()"><option value="ALL">Tất cả Danh mục</option></select>
                    </div>
                </div>
            </div>
        </div>

        <!-- 4 KPI CARDS -->
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-title">Tỉ Lệ Đạt Amazon's Choice</div>
                <div class="kpi-value" id="kpi_ac_pct">0%</div>
                <div class="kpi-sub" id="kpi_ac_sub">0 / 0 sản phẩm</div>
            </div>
            <div class="kpi-card c-green">
                <div class="kpi-title">Chênh Lệch Doanh Số Bán</div>
                <div class="kpi-value" id="kpi_sales_diff">+0%</div>
                <div class="kpi-sub" id="kpi_sales_sub">Doanh số: 0 vs 0</div>
            </div>
            <div class="kpi-card c-blue">
                <div class="kpi-title">Chênh Lệch Định Giá ($)</div>
                <div class="kpi-value" id="kpi_price_diff">+$0</div>
                <div class="kpi-sub" id="kpi_price_sub">Giá bán: $0 vs $0</div>
            </div>
            <div class="kpi-card c-amber">
                <div class="kpi-title">Chênh Lệch Rating (⭐)</div>
                <div class="kpi-value" id="kpi_rating_diff">+0.0</div>
                <div class="kpi-sub" id="kpi_rating_sub">Rating: 0.0 vs 0.0</div>
            </div>
        </div>

        <!-- ROW 1: Donut & Radar -->
        <div class="chart-row">
            <div class="chart-card" style="flex: 0.8;">
                <div class="chart-header">
                    <div class="chart-title">Phân Bổ Kích Trọng Giá Trị Nhãn Hiệu</div>
                    <div class="chart-subtitle">Tỉ trọng nhóm Amazon's Choice trong tập Best Seller</div>
                </div>
                <div class="chart-wrapper" style="height: 250px;"><canvas id="cDonut"></canvas></div>
            </div>
            
            <div class="chart-card" style="flex: 1.2;">
                <div class="chart-header">
                    <div class="chart-title">Hồ Sơ Cạnh Tranh (Radar Cân Bằng)</div>
                    <div class="chart-subtitle">So sánh chuẩn hóa: Doanh Số, Lượt Đánh Giá, Giá Bán và Rating</div>
                </div>
                <div class="chart-wrapper" style="height: 250px;"><canvas id="cRadar"></canvas></div>
            </div>
        </div>

        <!-- ROW 2: Stacked Bar Price Tier & Sales/Rev Bar -->
        <div class="chart-row">
            <div class="chart-card" style="flex: 1;">
                <div class="chart-header">
                    <div class="chart-title">Phân Bổ Kích Trọng Theo Phân Khúc Giá</div>
                    <div class="chart-subtitle">Tỉ lệ cột mốc: 100% cột chia theo tỉ lệ đạt Choice từng mức giá</div>
                </div>
                <div class="chart-wrapper" style="height: 280px;"><canvas id="cPriceTier"></canvas></div>
            </div>
            <div class="chart-card" style="flex: 1;">
                <div class="chart-header">
                    <div class="chart-title">Hiệu Suất Tuyệt Đối: Doanh Số TB và Doanh Thu TB ($)</div>
                    <div class="chart-subtitle">So sánh số lượng bán ra mặt bằng chung. Khác biệt lớn minh chứng uy tín</div>
                </div>
                <div class="chart-wrapper" style="height: 280px;"><canvas id="cBarSales"></canvas></div>
            </div>
        </div>

        <!-- ROW 3: Horizontal Categories & Scatter Plots -->
        <div class="chart-row">
            <div class="chart-card" style="flex: 0.8;">
                <div class="chart-header">
                    <div class="chart-title">Tham Kiếu Nhóm Ngành Hàng Đề Xuất</div>
                    <div class="chart-subtitle">Tỉ lệ xuất hiện Amazon's Choice theo TOP 10 danh mục lớn</div>
                </div>
                <div class="chart-wrapper" style="height: 380px;"><canvas id="cBarHorCat"></canvas></div>
            </div>
            
            <div class="chart-card" style="flex: 1.2;">
                <div class="chart-header">
                    <div class="chart-title">Bức Tranh Hệ Trục: Giá Bán vs. Doanh Số Bán Ra</div>
                    <div class="chart-subtitle">Ma trận Scatter xác định "Sweet Spot" định giá của Amazon's Choice</div>
                </div>
                <div class="chart-wrapper" style="height: 380px;"><canvas id="cScatter"></canvas></div>
            </div>
        </div>

        <!-- BẢNG DỮ LIỆU ĐÁNG CHÚ Ý -->
        <div class="chart-card" style="margin-bottom: 20px;">
            <div class="chart-header">
                <div class="chart-title">Top 5 Sản Phẩm Amazon's Choice Bán Chạy Nhất</div>
                <div class="chart-subtitle">Phân cụm xuất sắc từ thuật toán đề xuất</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Tên sản phẩm</th>
                        <th>Danh mục</th>
                        <th>Giá ($)</th>
                        <th>Đánh giá (⭐)</th>
                        <th>Doanh số (lượt)</th>
                    </tr>
                </thead>
                <tbody id="tbTop5Choice">
                    <!-- Rendered by JS -->
                </tbody>
            </table>
        </div>

        <div class="insight-box" id="insightBox1">
            <div class="insight-icon">💡</div>
            <div class="insight-content">
                <div class="insight-label">INSIGHT CHIẾN LƯỢC: HỆ SINH THÁI NHÃN DÁN CỦA AMAZON</div>
                <div class="insight-text" id="ins1">Đang phân tích...</div>
            </div>
        </div>

    </div><!-- /section -->

<script>
    const RAW = {data_json_str};
    let globalInstances = {{}};
    const COLORS = {{ choice: '#F97316', non: '#3B82F6', green: '#10B981', dark: '#9A3412', blue: '#3B82F6', amber: '#F59E0B' }};

    const fmtN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR = n => Number(n).toFixed(2);
    const fmtP = n => Number(n).toFixed(1) + '%';

    function setup() {{
        // Lấy danh sách danh mục
        let cats = new Set();
        RAW.forEach(d => {{ if(d.crawl_category && d.crawl_category !== 'Không rõ' && d.crawl_category !== 'Khác') cats.add(d.crawl_category); }});
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option');
            opt.value = c; opt.innerText = c;
            sel.appendChild(opt);
        }});

        initCharts();
        applyFilters();
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let data = RAW.filter(d => cat === 'ALL' || d.crawl_category === cat);
        updateDashboard(data);
    }}

    function updateDashboard(data) {{
        if(data.length === 0) return;

        let G_choice = data.filter(d => d.is_amazon_choice);
        let G_non = data.filter(d => !d.is_amazon_choice);

        // ------------------ 1. KPIs Update ------------------
        let t_prod = data.length;
        let c_cnt = G_choice.length;
        let c_pct = (c_cnt / t_prod) * 100;
        
        document.getElementById('kpi_ac_pct').innerText = fmtP(c_pct);
        document.getElementById('kpi_ac_sub').innerText = c_cnt + ' / ' + t_prod + ' sản phẩm';

        let s_c = c_cnt > 0 ? G_choice.reduce((a,b)=>a+b.sales_volume_num,0)/c_cnt : 0;
        let s_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.sales_volume_num,0)/G_non.length : 0;
        let s_diff = (s_c - s_n);
        let s_pct = s_n > 0 ? ((s_c - s_n) / s_n) * 100 : 0;
        let k1_elem = document.getElementById('kpi_sales_diff');
        k1_elem.innerText = (s_diff >= 0 ? '+' : '') + fmtP(s_pct);
        k1_elem.parentElement.className = 'kpi-card ' + (s_pct > 0 ? 'c-green' : 'c-amber');
        document.getElementById('kpi_sales_sub').innerText = fmtN(s_c) + ' vs ' + fmtN(s_n);

        let p_c = c_cnt > 0 ? G_choice.reduce((a,b)=>a+b.current_price,0)/c_cnt : 0;
        let p_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.current_price,0)/G_non.length : 0;
        let p_diff = p_c - p_n;
        let p_elem = document.getElementById('kpi_price_diff');
        p_elem.innerText = (p_diff >= 0 ? '+$' : '-$') + fmtR(Math.abs(p_diff));
        p_elem.parentElement.className = 'kpi-card ' + (p_diff < 0 ? 'c-blue' : 'c-amber');
        document.getElementById('kpi_price_sub').innerText = '$' + fmtR(p_c) + ' vs $' + fmtR(p_n);

        let r_c = c_cnt > 0 ? G_choice.reduce((a,b)=>a+b.rating_val,0)/c_cnt : 0;
        let r_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.rating_val,0)/G_non.length : 0;
        let r_diff = r_c - r_n;
        document.getElementById('kpi_rating_diff').innerText = (r_diff >= 0 ? '+' : '') + fmtR(r_diff);
        document.getElementById('kpi_rating_sub').innerText = fmtR(r_c) + ' vs ' + fmtR(r_n);

        // ------------------ 2. INSIGHT GENERATION ------------------
        let insHTML = `Khảo sát hiển thị nhóm sản phẩm nhận <strong>Amazon's Choice</strong> chiếm khoảng <strong>${{fmtP(c_pct)}}</strong> tổng hàng mẫu. <br>`;
        if (s_pct > 0) {{
            insHTML += `Hiệu ứng nhãn dẫn đến doanh số trung bình vọt lên mức <strong>+${{fmtP(s_pct)}} cao hơn</strong> so với nhóm chỉ là Best Seller (với baseline là các mặt hàng đã top đầu). Điều này chứng minh thuật toán cực độ cộng hưởng doanh số. `;
        }}
        if (p_diff < 0) {{
            insHTML += `Đáng chú ý, mặt bằng giá nhóm Choice <strong>thấp hơn -$${{fmtR(Math.abs(p_diff))}}</strong>. Điều này cho thấy thuật toán Amazon tìm kiếm "Sweet spot" - sản phẩm có rating tốt nhưng định giá cạnh tranh. `;
        }} else {{
            insHTML += `Nhóm Amazon's Choice dù duy trì mức định giá cao hơn (+$${{fmtR(Math.abs(p_diff))}}) vẫn tạo ra đột phá doanh thu, chứng minh uy tín tuyệt đối mà Amazon tạo ra kích cầu "upsell".`;
        }}
        document.getElementById('ins1').innerHTML = insHTML;

        // ------------------ 3. CHART: Donut ------------------
        globalInstances.cDonut.data.datasets[0].data = [c_cnt, G_non.length];
        globalInstances.cDonut.update();

        // ------------------ 4. CHART: Radar (Normalize) ------------------
        let max_s = Math.max(s_c, s_n, 1);
        let max_r = 5;
        let rev_c = c_cnt > 0 ? G_choice.reduce((a,b)=>a+b.reviews_val,0)/c_cnt : 0;
        let rev_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.reviews_val,0)/G_non.length : 0;
        let max_rev = Math.max(rev_c, rev_n, 1);
        let max_p = Math.max(p_c, p_n, 1);

        globalInstances.cRadar.data.datasets[0].data = [
            (r_c/max_r)*100, (s_c/max_s)*100, (rev_c/max_rev)*100, (p_c/max_p)*100
        ];
        globalInstances.cRadar.data.datasets[1].data = [
            (r_n/max_r)*100, (s_n/max_s)*100, (rev_n/max_rev)*100, (p_n/max_p)*100
        ];
        globalInstances.cRadar.update();

        // ------------------ 5. CHART: Stacked Bar Price Tier ------------------
        let tiers = ["1. Bình dân (<$25)", "2. Phổ thông ($25-$50)", "3. Trung cấp ($50-$100)", "4. Cao cấp (>$100)"];
        let tierChData = []; let tierNoData = [];
        tiers.forEach(t => {{
            let t_data = data.filter(d => d.price_tier === t);
            let tot = t_data.length;
            if (tot === 0) {{ tierChData.push(0); tierNoData.push(0); return; }}
            let ch_p = (t_data.filter(d => d.is_amazon_choice).length / tot) * 100;
            tierChData.push(ch_p);
            tierNoData.push(100 - ch_p);
        }});
        globalInstances.cPriceTier.data.labels = tiers;
        globalInstances.cPriceTier.data.datasets[0].data = tierChData;
        globalInstances.cPriceTier.data.datasets[1].data = tierNoData;
        globalInstances.cPriceTier.update();

        // ------------------ 6. CHART: Bar Sales Absolute ------------------
        let revS_c = c_cnt > 0 ? G_choice.reduce((a,b)=>a+(b.sales_volume_num*b.current_price),0)/c_cnt : 0;
        let revS_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+(b.sales_volume_num*b.current_price),0)/G_non.length : 0;

        globalInstances.cBarSales.data.datasets[0].data = [s_c, s_n];
        globalInstances.cBarSales.data.datasets[1].data = [revS_c, revS_n];
        globalInstances.cBarSales.update();

        // ------------------ 7. CHART: Bar Horizontal Categories ------------------
        let catMap = {{}};
        data.forEach(d => {{
            let c = d.crawl_category;
            if(!catMap[c]) catMap[c] = {{t:0, ch:0}};
            catMap[c].t++;
            if(d.is_amazon_choice) catMap[c].ch++;
        }});
        let catArr = Object.keys(catMap).map(k => ({{
            cat: k,
            pct: (catMap[k].ch / catMap[k].t) * 100,
            vol: catMap[k].t
        }})).filter(x => x.vol > 5).sort((a,b) => b.pct - a.pct).slice(0, 10);
        
        catArr.reverse(); // For horizontal chart bottom-up
        globalInstances.cBarHorCat.data.labels = catArr.map(x => x.cat.length > 20 ? x.cat.substring(0,18)+'...' : x.cat);
        globalInstances.cBarHorCat.data.datasets[0].data = catArr.map(x => x.pct);
        globalInstances.cBarHorCat.update();

        // ------------------ 8. CHART: Scatter ------------------
        let scatterCh = []; let scatterNo = [];
        let max_scatter = 1000;
        // Limit points dynamically to prevent canvas lag
        let renderData = data.length > max_scatter 
            ? [...data].sort(() => 0.5 - Math.random()).slice(0, max_scatter) 
            : data;

        renderData.forEach(d => {{
            let pt = {{x: d.current_price, y: d.sales_volume_num}};
            if (d.is_amazon_choice) scatterCh.push(pt);
            else scatterNo.push(pt);
        }});
        
        globalInstances.cScatter.data.datasets[0].data = scatterCh;
        globalInstances.cScatter.data.datasets[1].data = scatterNo;
        globalInstances.cScatter.update();

        // ------------------ 9. HTML Table update ------------------
        let sorted = [...G_choice].sort((a,b) => b.sales_volume_num - a.sales_volume_num).slice(0,5);
        let tb = document.getElementById('tbTop5Choice');
        tb.innerHTML = "";
        sorted.forEach(s => {{
            let title = s.title || "";
            if(title.length > 55) title = title.substring(0, 55) + "...";
            let tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="truncate-col" title="${{s.title}}"><b>${{title}}</b></td>
                <td>${{s.crawl_category}}</td>
                <td><span style="color:var(--dark); font-weight:600;">$${{fmtR(s.current_price)}}</span></td>
                <td>⭐ ${{fmtR(s.rating_val)}}</td>
                <td><span style="background:var(--primary-light); padding:2px 6px; border-radius:4px; font-weight:600; font-size:10.5px;">${{fmtN(s.sales_volume_num)}}</span></td>
            `;
            tb.appendChild(tr);
        }});
    }}

    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';

        // 1. Donut Chart
        let ctxDonut = document.getElementById('cDonut').getContext('2d');
        globalInstances.cDonut = new Chart(ctxDonut, {{
            type: 'doughnut',
            data: {{
                labels: ["Amazon's Choice", "Chỉ Best Seller"],
                datasets: [{{
                    data: [0,0],
                    backgroundColor: [COLORS.choice, COLORS.non],
                    borderWidth: 2, borderColor: '#FFFFFF'
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false, cutout: '65%',
                plugins: {{ legend: {{position: 'bottom', labels: {{usePointStyle:true, padding:20, font:{{size:11}}}}}} }}
            }}
        }});

        // 2. Radar Chart
        let ctxRadar = document.getElementById('cRadar').getContext('2d');
        globalInstances.cRadar = new Chart(ctxRadar, {{
            type: 'radar',
            data: {{
                labels: ['Rating TB', 'Doanh Số TB', 'Lượt Review TB', 'Giá Bán TB'],
                datasets: [
                    {{ label: "Amazon's Choice", data: [0,0,0,0], backgroundColor: 'rgba(249, 115, 22, 0.2)', borderColor: COLORS.choice, borderWidth: 2, pointBackgroundColor: COLORS.choice, pointRadius:3 }},
                    {{ label: "Chỉ Best Seller", data: [0,0,0,0], backgroundColor: 'rgba(59, 130, 246, 0.2)', borderColor: COLORS.non, borderWidth: 2, pointBackgroundColor: COLORS.non, pointRadius:3 }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                scales: {{ r: {{ angleLines: {{ display: true, color:'rgba(0,0,0,0.05)' }}, grid: {{color:'rgba(0,0,0,0.05)'}}, suggestedMin: 0, suggestedMax: 100, ticks:{{display:false}} }} }},
                plugins: {{ legend: {{position: 'bottom', labels: {{usePointStyle:true, padding:20, font:{{size:11}}}}}} }}
            }}
        }});

        // 3. Price Tier Stacked Bar
        let ctxTier = document.getElementById('cPriceTier').getContext('2d');
        globalInstances.cPriceTier = new Chart(ctxTier, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: "Amazon's Choice (%)", data: [], backgroundColor: COLORS.choice }},
                    {{ label: "Non-Choice (%)", data: [], backgroundColor: COLORS.non }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels:{{usePointStyle:true}} }}, tooltip: {{ mode:'index', intersect:false }} }},
                scales: {{
                    x: {{ stacked: true, grid: {{ display: false }} }},
                    y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.05)' }}, max: 100, ticks: {{ callback: v => v+'%' }} }}
                }}
            }}
        }});

        // 4. Bar Sales Absolute
        let ctxBar = document.getElementById('cBarSales').getContext('2d');
        globalInstances.cBarSales = new Chart(ctxBar, {{
            type: 'bar',
            data: {{
                labels: ["Amazon's Choice", "Chỉ Best Seller"],
                datasets: [
                    {{ type: 'bar', label: 'Doanh Số Ước Tính', data:[0,0], backgroundColor: COLORS.choice, yAxisID: 'y' }},
                    {{ type: 'bar', label: 'Doanh Thu ($)', data:[0,0], backgroundColor: COLORS.dark, yAxisID: 'yRev' }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels:{{usePointStyle:true}} }} }},
                scales: {{
                    y: {{ type:'linear', position:'left', grid:{{color:'rgba(0,0,0,0.05)'}} }},
                    yRev: {{ type:'linear', position:'right', grid:{{display:false}} }}
                }}
            }}
        }});

        // 5. Bar Horizontal Categories
        let ctxHoriz = document.getElementById('cBarHorCat').getContext('2d');
        globalInstances.cBarHorCat = new Chart(ctxHoriz, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [{{ label: 'Xác suất đạt Nhãn (%)', data: [], backgroundColor: COLORS.choice, borderRadius: 4 }}]
            }},
            options: {{
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{display:false}} }},
                scales: {{
                    x: {{ beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback: v => v+'%'}} }},
                    y: {{ grid:{{display:false}} }}
                }}
            }}
        }});

        // 6. Scatter graphic
        let ctxScatter = document.getElementById('cScatter').getContext('2d');
        globalInstances.cScatter = new Chart(ctxScatter, {{
            type: 'scatter',
            data: {{
                datasets: [
                    {{ label: "Amazon's Choice", data: [], backgroundColor: 'rgba(249, 115, 22, 0.8)', borderColor: '#FFFFFF', borderWidth:1, pointRadius: 5 }},
                    {{ label: "Chỉ Best Seller", data: [], backgroundColor: 'rgba(59, 130, 246, 0.4)', borderColor: 'transparent', pointRadius: 3 }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels:{{usePointStyle:true}} }} }},
                scales: {{
                    x: {{ title: {{display:true, text:'Giá bán định giá ($)', color:COLORS.dark}}, grid: {{color:'rgba(0,0,0,0.05)'}} }},
                    y: {{ title: {{display:true, text:'Doanh Số Ước Tính (/Tháng)', color:COLORS.dark}}, grid: {{color:'rgba(0,0,0,0.05)'}} }}
                }}
            }}
        }});

    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
"""
    components.html(html_code, height=1920, scrolling=False)
