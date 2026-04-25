import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def render(df_raw):
    df = df_raw.copy()

    # Preprocessing
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0).astype(int)

    # Categories logic
    from utils.constants import CATEGORY_MAP
    if "crawl_category" in df.columns:
        df["Danh Mục Sản Phẩm"] = df["crawl_category"].map(CATEGORY_MAP).fillna(df["crawl_category"])
    else:
        df["Danh Mục Sản Phẩm"] = "Không Rõ"

    # Evaluate missing columns
    exclude_cols = ['asin', 'title', 'price', 'original_price', 'sales_volume', 'sales_volume_num', 'currency', 'is_best_seller', 'link', 'Danh Mục Sản Phẩm', 'crawl_category']
    eval_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Optimization: Calculate missing logic across dataframe
    # We create a boolean mask dataframe where True means the feature is PROVIDED (not missing)
    def is_missing_series(series):
        # Convert to string, strip, compare against missing indicators, or boolean isna
        s_str = series.astype(str).str.strip()
        return s_str.isin(["", "nan", "NaN", "None", "[]", "{}"]) | series.isna()

    missing_df = df[eval_cols].apply(is_missing_series)
    provided_df = ~missing_df

    df["missing_count"] = missing_df.sum(axis=1)
    total_features = len(eval_cols)
    
    # Pre-calculate Top Features for TOP 20% Sales products (Globally & Per Category)
    top_features_dict = {}

    def calc_top_provided_features(sub_df, prov_mask):
        if len(sub_df) == 0: return {}
        # Get top 20% by sales volume
        top_n = max(1, int(len(sub_df) * 0.2))
        top_indices = sub_df.nlargest(top_n, "sales_volume_num").index
        
        if len(top_indices) == 0: return {}
        
        # Calculate % of products providing each feature
        prov_counts = prov_mask.loc[top_indices].sum()
        prov_pct = (prov_counts / len(top_indices) * 100).round(1)
        
        # Take Top 15 most commonly provided features among successful products
        top_15 = prov_pct.sort_values(ascending=False).head(15).to_dict()
        return top_15

    top_features_dict["ALL"] = calc_top_provided_features(df, provided_df)
    
    for cat in df["Danh Mục Sản Phẩm"].unique():
        cat_df = df[df["Danh Mục Sản Phẩm"] == cat]
        top_features_dict[cat] = calc_top_provided_features(cat_df, provided_df)

    top_feats_json_str = json.dumps(top_features_dict, ensure_ascii=False)

    # Select columns & dump JSON for scatter/bar chart rendering
    select_cols = ["Danh Mục Sản Phẩm", "sales_volume_num", "missing_count"]
    export_df = df[select_cols].copy()
    data_json = export_df.to_dict(orient="records")
    data_json_str = json.dumps(data_json, ensure_ascii=False)

    html_code = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(19, 26, 42, 0.7);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-emerald: #10b981;
            --accent-purple: #8b5cf6;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --accent-cyan: #06b6d4;
            --font-display: 'Outfit', sans-serif;
            --font-body: 'Inter', sans-serif;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
            color: var(--text-main);
            font-family: var(--font-body);
            height: 100vh;
            overflow: hidden;
            padding: 12px 16px;
        }}

        .dashboard-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}

        .title-group h1 {{
            font-family: var(--font-display);
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(to right, #60a5fa, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }}

        .title-group p {{
            font-size: 13px;
            color: var(--text-muted);
            max-width: 600px;
        }}

        .filter-container {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 6px 12px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }}

        .filter-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        select {{
            background: rgba(15, 23, 42, 0.8);
            color: white;
            border: 1px solid var(--card-border);
            padding: 6px 10px;
            border-radius: 6px;
            font-family: var(--font-body);
            font-size: 13px;
            outline: none;
            cursor: pointer;
            transition: all 0.2s;
        }}

        select:hover, select:focus {{
            border-color: var(--accent-blue);
        }}

        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }}

        .kpi-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
            border-radius: 4px 0 0 4px;
        }}

        .kpi-card.blue::before {{ background: var(--accent-blue); }}
        .kpi-card.purple::before {{ background: var(--accent-purple); }}
        .kpi-card.amber::before {{ background: var(--accent-amber); }}

        .kpi-title {{
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .kpi-val {{
            font-family: var(--font-display);
            font-size: 28px;
            font-weight: 700;
        }}

        .kpi-sub {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .trend-up {{ color: var(--accent-emerald); font-weight: 600; }}
        .trend-down {{ color: var(--accent-rose); font-weight: 600; }}

        .charts-wrapper {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: calc(100vh - 210px);
            gap: 16px;
        }}

        .chart-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .chart-header {{
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .chart-title {{
            font-family: var(--font-display);
            font-size: 16px;
            font-weight: 600;
            color: #fff;
        }}

        .chart-subtitle {{
            font-size: 11px;
            color: var(--text-muted);
        }}
        
        .chart-container {{
            flex: 1;
            position: relative;
            min-height: 0;
            width: 100%;
        }}
    </style>
</head>
<body>

    <div class="dashboard-header">
        <div class="title-group">
            <h1>Phân Tích Thông Tin Sản Phẩm Đạt Top Doanh Số</h1>
            <p>Khám phá liên kết trực tiếp giữa sự đầy đủ thông tin (Feature Completeness) và Doanh thu của sản phẩm (Sales Volume), cũng như đặc điểm thông tin chung của các Best Seller (Top 20% doanh thu).</p>
        </div>
        <div class="filter-container">
            <span class="filter-label">Danh Mục</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả danh mục sản phẩm</option>
            </select>
        </div>
    </div>

    <!-- KPI ROW -->
    <div class="kpi-row">
        <div class="kpi-card blue">
            <div class="kpi-title">DOANH SỐ TB (S.PHẨM THÔNG TIN KỸ LƯỠNG)</div>
            <div class="kpi-val" id="kpi_sales_good">0</div>
            <div class="kpi-sub">
                So với SP Sơ sài: <span id="kpi_sales_diff">-</span>
            </div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-title">MỨC BỎ TRỐNG TRUNG BÌNH TOÀN NGÀNH</div>
            <div class="kpi-val" id="kpi_missing_avg">0</div>
            <div class="kpi-sub">
                Trên tổng số {total_features} trường thông tin (Features)
            </div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-title">FEATURE QUAN TRỌNG NHẤT (TOP DOANH SỐ)</div>
            <div class="kpi-val" style="font-size: 20px" id="kpi_top_feat">-</div>
            <div class="kpi-sub">
                Hầu như có mặt trên tất cả các SP Top Doanh số
            </div>
        </div>
    </div>

    <!-- CHARTS -->
    <div class="charts-wrapper" style="grid-template-columns: 1fr 1.2fr 1.2fr;">
        
        <!-- Chart 1: Doanh số theo mức độ hoàn thiện -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Doanh Số Theo Mức Độ Chi Tiết</div>
                    <div class="chart-subtitle">Trung bình lượt bán / tháng (Phân nhóm theo số lượng Missing)</div>
                </div>
            </div>
            <div class="chart-container"><canvas id="c_sales"></canvas></div>
        </div>

        <!-- Chart 2: Top Features of Top Selling Products -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Mô Típ Của "Người Chiến Thắng"</div>
                    <div class="chart-subtitle">Tỷ lệ % cung cấp các Trường Thông Tin này của TOP 20% Doanh Thu</div>
                </div>
            </div>
            <div class="chart-container"><canvas id="c_top_feats"></canvas></div>
        </div>

        <!-- Chart 3: Scatter / Bubble Missing vs Sales -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Phân Bổ Doanh Số Theo Thông Tin Khuyết</div>
                    <div class="chart-subtitle">Trục X: Số lượng thông tin thiếu | Trục Y: Lượt bán TB | Trọng số: Lượng SP</div>
                </div>
            </div>
            <div class="chart-container"><canvas id="c_scatter"></canvas></div>
        </div>

    </div>

<script>
    const RAW_DATA = {data_json_str};
    const TOP_FEATS_DATA = {top_feats_json_str};
    const TOTAL_FEATS = {total_features};
    let CHARTS = {{}};

    // Formatters
    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));

    function setup() {{
        Chart.register(ChartDataLabels);
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";
        
        // Populate Filter
        let cats = new Set();
        RAW_DATA.forEach(d => {{ if(d['Danh Mục Sản Phẩm'] && d['Danh Mục Sản Phẩm'] !== 'Không Rõ') cats.add(d['Danh Mục Sản Phẩm']); }});
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option'); opt.value = c; opt.innerText = c; sel.appendChild(opt);
        }});

        initCharts();
        applyFilters();
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let data = RAW_DATA.filter(d => (cat === 'ALL' || d['Danh Mục Sản Phẩm'] === cat));
        processData(data, cat);
    }}

    function getCompletenessTier(missingCount) {{
        if (missingCount <= 15) return 0; // Kỹ Lưỡng (Rất ít thiếu)
        if (missingCount <= 30) return 1; // Khá Đầy Đủ
        if (missingCount <= 39) return 2; // Cơ Bản
        return 3; // Sơ Sài (Thiếu > 39)
    }}

    function processData(data, cat) {{
        const TIER_NAMES = ['Kỹ Lưỡng (Thiếu ≤15)', 'Khá (16-30)', 'Cơ Bản (31-39)', 'Sơ Sài (≥40)'];
        
        let bins = [
            {{ sales: 0, count: 0 }},
            {{ sales: 0, count: 0 }},
            {{ sales: 0, count: 0 }},
            {{ sales: 0, count: 0 }}
        ];

        let totalMissing = 0;
        let scatterMap = new Map();

        data.forEach(d => {{
            let m = d.missing_count;
            totalMissing += m;
            let t = getCompletenessTier(m);
            
            bins[t].count++;
            bins[t].sales += (d.sales_volume_num || 0);

            // Scatter mapping (Group by missing count to form bubbles)
            let scGroup = Math.floor(m / 2) * 2; // Group every 2 points
            if(!scatterMap.has(scGroup)) scatterMap.set(scGroup, {{s:0, c:0}});
            let sc = scatterMap.get(scGroup);
            sc.s += (d.sales_volume_num || 0);
            sc.c++;
        }});

        let avgMissing = data.length ? totalMissing / data.length : 0;
        let avgSales = bins.map(b => b.count ? b.sales / b.count : 0);

        // Update KPIs
        let good_idx = 0; // Kỹ Lưỡng
        let bad_idx = 3;  // Sơ Sài

        document.getElementById('kpi_missing_avg').innerText = Math.round(avgMissing);

        // Sales KPI
        document.getElementById('kpi_sales_good').innerText = fmtN(avgSales[good_idx]);
        let sales_diff = avgSales[good_idx] - avgSales[bad_idx];
        let sales_diff_el = document.getElementById('kpi_sales_diff');
        if (sales_diff > 0) {{
            let multiplier = avgSales[bad_idx] > 0 ? (avgSales[good_idx]/avgSales[bad_idx]).toFixed(1) + 'x' : 'N/A';
            sales_diff_el.innerHTML = `<span class="trend-up">Gấp ${{multiplier}} lần</span>`;
        }} else {{
            sales_diff_el.innerHTML = `<span class="trend-down">Thấp hơn</span>`;
        }}

        // Features Info KPI for selected Category
        let topFeatDataForCat = TOP_FEATS_DATA[cat] || {{}};
        let topFeatLabels = Object.keys(topFeatDataForCat);
        let topFeatStats = Object.values(topFeatDataForCat);
        
        let topFeatName = topFeatLabels.length > 0 ? topFeatLabels[0] : "N/A";
        let topFeatPct = topFeatStats.length > 0 ? topFeatStats[0] : 0;
        
        document.getElementById('kpi_top_feat').innerText = topFeatName.toUpperCase() + ` (${{topFeatPct}}%)`;

        // UPDATE CHARTS
        updateSalesChart(TIER_NAMES, avgSales);
        updateTopFeatsChart(topFeatLabels.slice(0, 10), topFeatStats.slice(0, 10)); // Draw Top 10 Features
        updateScatterChart(scatterMap);
    }}

    function updateSalesChart(labels, data) {{
        CHARTS.sales.data.labels = labels;
        CHARTS.sales.data.datasets[0].data = data;
        CHARTS.sales.update();
    }}

    function updateTopFeatsChart(labels, data) {{
        CHARTS.topFeats.data.labels = labels;
        CHARTS.topFeats.data.datasets[0].data = data;
        CHARTS.topFeats.update();
    }}

    function updateScatterChart(scatterMap) {{
        let sortedKeys = Array.from(scatterMap.keys()).sort((a,b)=>a-b);
        let scData = sortedKeys.map(k => {{
            let st = scatterMap.get(k);
            let avgS = st.s / st.c;
            // Radius scales logrithmically based on frequency
            let r = Math.min(Math.max(Math.log(st.c) * 4, 3), 30);
            return {{ x: k, y: avgS, r: r, count: st.c }};
        }});

        CHARTS.scatter.data.datasets[0].data = scData;
        CHARTS.scatter.update();
    }}

    const baseConfig = {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }}
    }};

    function initCharts() {{
        // 1. Sales Chart (Bar)
        let ctxSales = document.getElementById('c_sales').getContext('2d');
        let gradSales = ctxSales.createLinearGradient(0, 0, 0, 400);
        gradSales.addColorStop(0, 'rgba(56, 189, 248, 0.8)');
        gradSales.addColorStop(1, 'rgba(2, 132, 199, 0.8)');

        CHARTS.sales = new Chart(ctxSales, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'Doanh Số TB',
                    data: [],
                    backgroundColor: gradSales,
                    borderRadius: 6
                }}]
            }},
            options: {{
                ...baseConfig,
                scales: {{
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ callback: (v)=>fmtN(v) }} }},
                    x: {{ grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    datalabels: {{ color: '#fff', font: {{ weight: 'bold' }}, formatter: (v)=>fmtN(v), anchor: 'end', align: 'end', offset: -4 }}
                }}
            }}
        }});

        // 2. Top Features Chart (Horizontal Bar)
        let ctxTop = document.getElementById('c_top_feats').getContext('2d');
        let gradTop = ctxTop.createLinearGradient(400, 0, 0, 0);
        gradTop.addColorStop(0, 'rgba(245, 158, 11, 0.8)'); // Amber
        gradTop.addColorStop(1, 'rgba(217, 119, 6, 0.8)');

        CHARTS.topFeats = new Chart(ctxTop, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [{{
                    label: '% Cung Cấp',
                    data: [],
                    backgroundColor: gradTop,
                    borderRadius: 4
                }}]
            }},
            options: {{
                ...baseConfig,
                indexAxis: 'y',
                scales: {{
                    x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, max: 100, ticks: {{ callback: (v)=>v+'%' }} }},
                    y: {{ grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    datalabels: {{ color: '#fff', font: {{ weight: 'bold' }}, formatter: (v)=>v+'%', anchor: 'end', align: 'right', offset: 2 }}
                }}
            }}
        }});

        // 3. Scatter Chart (Missing count vs Sales)
        let ctxScatter = document.getElementById('c_scatter').getContext('2d');
        CHARTS.scatter = new Chart(ctxScatter, {{
            type: 'bubble',
            data: {{
                datasets: [{{
                    label: 'Sales vs Missing',
                    data: [],
                    backgroundColor: 'rgba(139, 92, 246, 0.6)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                ...baseConfig,
                scales: {{
                    x: {{ 
                        title: {{ display: true, text: 'Số lượng Features Thiếu', color: '#94a3b8' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }} 
                    }},
                    y: {{ 
                        title: {{ display: true, text: 'Lượt Bán TB', color: '#94a3b8' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }} 
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    datalabels: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(ctx) {{
                                let d = ctx.raw;
                                return `Thiếu ${{d.x}} | Lượt Bán TB: ${{fmtN(d.y)}} | SL SP Ghi nhận: ${{d.count}}`;
                            }}
                        }}
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
    
    components.html(html_code, height=900, scrolling=False)
