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
    # 3. HTML/CSS/JS CHUẨN ĐỒNG BỘ - COMPACT VERSION
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
            --dark: #9A3412; --bg: #F8FAFC; --card-bg: #FFFFFF;
            --text-primary: #0F172A; --text-secondary: #64748B;
            --border-radius: 12px; --font-family: 'Inter', sans-serif;
            --success: #10B981; --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            background: var(--bg); font-family: var(--font-family); color: var(--text-primary); 
            padding: 8px 12px; overflow: hidden; width: 100vw; height: 100vh;
        }}
        .header-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .title-main {{ font-size: 14px; font-weight: 800; color: var(--dark); letter-spacing: -0.2px; }}
        select {{ padding: 3px 8px; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 10px; font-weight: 600; outline: none; background: white; }}

        .q-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
        .q-cell {{ background: white; border: 1px solid #E2E8F0; border-radius: var(--border-radius); padding: 10px 12px; box-shadow: var(--shadow); border-top: 3px solid var(--primary); }}
        .q-tag {{ font-size: 8px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 2px; display: block; }}
        .q-text {{ font-size: 11.5px; font-weight: 600; line-height: 1.3; color: #1E293B; }}

        .display-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; height: calc(100% - 105px); }}
        .panel {{ display: flex; flex-direction: column; gap: 12px; height: 100%; }}
        .chart-card {{ background: white; border-radius: var(--border-radius); padding: 10px; box-shadow: var(--shadow); flex: 1; min-height: 0; display: flex; flex-direction: column; }}
        .chart-title {{ font-size: 9.5px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 5px; }}
        .chart-wrapper {{ position: relative; width: 100%; flex: 1; min-height: 0; }}

        .kpi-mini {{ background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border-radius: var(--border-radius); padding: 8px 12px; border-left: 4px solid var(--success); display: flex; flex-direction: column; box-shadow: var(--shadow); }}
        .kpi-mini-label {{ font-size: 8.5px; font-weight: 700; color: #9A3412; opacity: 0.7; text-transform: uppercase; }}
        .kpi-mini-val {{ font-size: 20px; font-weight: 800; color: #7C2D12; margin: 1px 0; }}
        .kpi-mini-sub {{ font-size: 9.5px; font-weight: 500; color: #C2410C; }}
    </style>
</head>
<body>
    <div class="header-row">
        <div class="title-main">📊 DASHBOARD NHÃN UY TÍN (AMAZON'S CHOICE)</div>
        <select id="selCategory" onchange="applyFilters()"><option value="ALL">Tất cả Danh mục</option></select>
    </div>
    <div class="q-grid">
        <div class="q-cell">
            <span class="q-tag">MỤC TIÊU 1: ĐÁNH GIÁ HIỆU NĂNG CỦA NHÃN UY TÍN (SMART)</span>
            <div class="q-text">Thực hiện so sánh doanh số đơn hàng trung bình giữa nhóm sản phẩm có nhãn Amazon's Choice và nhóm thông thường để kiểm chứng liệu nhãn uy tín có thúc đẩy doanh số tăng trưởng ít nhất 15% trong tập dữ liệu mẫu hay không.</div>
        </div>
        <div class="q-cell">
            <span class="q-tag">MỤC TIÊU 2: PHÂN TÍCH CHIẾN LƯỢC ĐỊNH GIÁ TỐI ƯU (SMART)</span>
            <div class="q-text">Phân tích sự phân bổ tỷ lệ gắn nhãn Amazon’s Choice trên 4 phân khúc giá để xác định liệu Amazon có ưu tiên các sản phẩm thuộc "Sweet Spot" ($25-$50) nhằm tối ưu hóa khả năng tiếp cận khách hàng hay không.</div>
        </div>
    </div>
    <div class="display-grid">
        <!-- Panel 1: Hiệu ứng nhãn -->
        <div class="panel">
            <div class="kpi-mini">
                <span class="kpi-mini-label">Chênh lệch doanh số trung bình</span>
                <div class="kpi-mini-val" id="kpi_sales_diff">+0%</div>
                <div class="kpi-mini-sub" id="kpi_sales_sub">TB: 0 (Choice) vs 0 (Best Seller)</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div class="kpi-mini" style="border-left-color: var(--secondary); background: #EFF6FF; padding: 6px 10px;">
                    <span class="kpi-mini-label" style="color: #1E40AF;">Rating Trung Bình</span>
                    <div class="kpi-mini-val" id="kpi_rating" style="font-size: 16px; color: #1E3A8A;">0.0 ⭐</div>
                </div>
                <div class="kpi-mini" style="border-left-color: #A855F7; background: #FAF5FF; padding: 6px 10px;">
                    <span class="kpi-mini-label" style="color: #6B21A8;">Số Review TB</span>
                    <div class="kpi-mini-val" id="kpi_reviews" style="font-size: 16px; color: #581C87;">0</div>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-title">So sánh hiệu suất bán ra (Doanh số)</div>
                <div class="chart-wrapper"><canvas id="cBarSales"></canvas></div>
            </div>
        </div>
        <div class="panel" style="display: grid; grid-template-rows: 1.2fr 0.8fr; gap: 10px;">
            <div class="chart-card"><div class="chart-title">Ma trận Giá vs. Doanh Số Bán</div><div class="chart-wrapper"><canvas id="cScatter"></canvas></div></div>
            <div class="chart-card"><div class="chart-title">Tỷ lệ Amazon's Choice theo mức giá</div><div class="chart-wrapper"><canvas id="cPriceTier"></canvas></div></div>
        </div>
    </div>
<script>
    const RAW = {data_json_str};
    let globalInstances = {{}};
    const COLORS = {{ choice: '#F97316', non: '#3B82F6' }};
    const fmtN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtP = n => Number(n).toFixed(1) + '%';

    function setup() {{
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
        let G_choice = data.filter(d => d.is_amazon_choice), G_non = data.filter(d => !d.is_amazon_choice);
        
        // 1. KPI Doanh số (Panel 1)
        let s_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.sales_volume_num,0)/G_choice.length : 0;
        let s_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.sales_volume_num,0)/G_non.length : 0;
        let s_pct = s_n > 0 ? ((s_c - s_n) / s_n) * 100 : 0;
        document.getElementById('kpi_sales_diff').innerText = (s_pct >= 0 ? '+' : '') + fmtP(s_pct);
        document.getElementById('kpi_sales_sub').innerText = 'TB: ' + fmtN(s_c) + ' (Choice) vs ' + fmtN(s_n) + ' (Best Seller)';
        
        // 2. Info bổ sung (Rating, Reviews - Panel 1)
        let r_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.rating_val,0)/G_choice.length : 0;
        let rev_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.reviews_val,0)/G_choice.length : 0;
        document.getElementById('kpi_rating').innerText = r_c.toFixed(1) + ' ⭐';
        document.getElementById('kpi_reviews').innerText = fmtN(rev_c);

        globalInstances.cBarSales.data.datasets[0].data = [s_c, s_n];
        globalInstances.cBarSales.update();

        // 3. Scatter Matrix (Panel 2)
        let scatterCh = [], scatterNo = [];
        let renderData = data.length > 500 ? [...data].sort(() => 0.5 - Math.random()).slice(0, 500) : data;
        renderData.forEach(d => {{
            let pt = {{x: d.current_price, y: d.sales_volume_num}};
            if (d.is_amazon_choice) scatterCh.push(pt); else scatterNo.push(pt);
        }});
        globalInstances.cScatter.data.datasets[0].data = scatterCh;
        globalInstances.cScatter.data.datasets[1].data = scatterNo;
        globalInstances.cScatter.update();

        // 4. Price Tiers (Panel 2)
        let tiers = ["1. Bình dân (<$25)", "2. Phổ thông ($25-$50)", "3. Trung cấp ($50-$100)", "4. Cao cấp (>$100)"];
        let tierChData = [], tierNoData = [];
        tiers.forEach(t => {{
            let t_data = data.filter(d => d.price_tier === t);
            if (t_data.length === 0) {{ tierChData.push(0); tierNoData.push(0); }}
            else {{ let p = (t_data.filter(d => d.is_amazon_choice).length / t_data.length) * 100;
                   tierChData.push(p); tierNoData.push(100 - p); }}
        }});
        globalInstances.cPriceTier.data.labels = tiers;
        globalInstances.cPriceTier.data.datasets[0].data = tierChData;
        globalInstances.cPriceTier.data.datasets[1].data = tierNoData;
        globalInstances.cPriceTier.update();
    }}

    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#64748B';

        // 1. Biểu đồ Doanh số
        const ctxBar = document.getElementById('cBarSales').getContext('2d');
        globalInstances.cBarSales = new Chart(ctxBar, {{
            type: 'bar',
            data: {{
                labels: ["Amazon's Choice", "Best Seller"],
                datasets: [{{
                    label: 'Doanh Số',
                    data: [0, 0],
                    backgroundColor: [COLORS.choice, COLORS.non],
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ drawBorder: false, color: '#F1F5F9' }}
                    }}
                }}
            }}
        }});

        // 2. Biểu đồ Scatter
        const ctxScatter = document.getElementById('cScatter').getContext('2d');
        globalInstances.cScatter = new Chart(ctxScatter, {{
            type: 'scatter',
            data: {{
                datasets: [
                    {{
                        label: "Choice",
                        data: [],
                        backgroundColor: 'rgba(249, 115, 22, 0.7)',
                        pointRadius: 4
                    }},
                    {{
                        label: "Thường",
                        data: [],
                        backgroundColor: 'rgba(59, 130, 246, 0.3)',
                        pointRadius: 2.5
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{ usePointStyle: true, padding: 5, font: {{ size: 9 }} }}
                    }}
                }},
                scales: {{
                    x: {{
                        title: {{ display: true, text: 'Giá ($)', font: {{ size: 8 }} }},
                        grid: {{ color: '#F1F5F9' }}
                    }},
                    y: {{
                        title: {{ display: true, text: 'Doanh Số', font: {{ size: 8 }} }},
                        grid: {{ color: '#F1F5F9' }}
                    }}
                }}
            }}
        }});

        // 3. Biểu đồ Price Tier
        const ctxTier = document.getElementById('cPriceTier').getContext('2d');
        globalInstances.cPriceTier = new Chart(ctxTier, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: "Choice (%)",
                        data: [],
                        backgroundColor: COLORS.choice
                    }},
                    {{
                        label: "Thường (%)",
                        data: [],
                        backgroundColor: COLORS.non
                    }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ usePointStyle: true, padding: 5, font: {{ size: 9 }} }}
                    }}
                }},
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        ticks: {{ callback: v => v + '%', font: {{ size: 8 }} }},
                        grid: {{ display: false }}
                    }},
                    y: {{
                        stacked: true,
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 8 }} }}
                    }}
                }}
            }}
        }});
    }}
    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
"""
    components.html(html_code, height=620, scrolling=False)
