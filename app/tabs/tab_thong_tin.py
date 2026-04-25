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
    
    def is_missing_series(series):
        s_str = series.astype(str).str.strip()
        return s_str.isin(["", "nan", "NaN", "None", "[]", "{}"]) | series.isna()

    missing_df = df[eval_cols].apply(is_missing_series)
    provided_df = ~missing_df

    df["missing_count"] = missing_df.sum(axis=1)
    total_features = len(eval_cols)
    
    # --- Pre-calculate Top Features for TOP 10% Sales products ---
    # We calculate both for top 10% AND for ALL products, to enable comparison
    top_features_dict = {}
    all_features_dict = {}

    def calc_provided_features(sub_df, prov_mask):
        if len(sub_df) == 0: return {}
        prov_counts = prov_mask.loc[sub_df.index].sum()
        prov_pct = (prov_counts / len(sub_df) * 100).round(1)
        return prov_pct.sort_values(ascending=False).to_dict()

    def calc_top_provided_features(sub_df, prov_mask):
        if len(sub_df) == 0: return {}
        top_n = max(1, int(len(sub_df) * 0.1))
        top_indices = sub_df.nlargest(top_n, "sales_volume_num").index
        if len(top_indices) == 0: return {}
        prov_counts = prov_mask.loc[top_indices].sum()
        prov_pct = (prov_counts / len(top_indices) * 100).round(1)
        return prov_pct.sort_values(ascending=False).to_dict()

    top_features_dict["ALL"] = calc_top_provided_features(df, provided_df)
    all_features_dict["ALL"] = calc_provided_features(df, provided_df)
    
    for cat in df["Danh Mục Sản Phẩm"].unique():
        cat_df = df[df["Danh Mục Sản Phẩm"] == cat]
        top_features_dict[cat] = calc_top_provided_features(cat_df, provided_df)
        all_features_dict[cat] = calc_provided_features(cat_df, provided_df)

    top_feats_json_str = json.dumps(top_features_dict, ensure_ascii=False)
    all_feats_json_str = json.dumps(all_features_dict, ensure_ascii=False)

    # Select columns & dump JSON
    select_cols = ["Danh Mục Sản Phẩm", "sales_volume_num", "missing_count"]
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
            padding: 16px 20px;
        }}

        .filter-bar {{
            display: flex;
            align-items: center;
            gap: 24px;
            margin-bottom: 16px;
            background: var(--card-bg);
            padding: 14px 20px;
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

        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}

        .kpi-card {{
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            padding: 14px 16px;
            border-left: 4px solid var(--primary);
            display: flex;
            flex-direction: column;
            gap: 3px;
        }}

        .kpi-title {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kpi-val {{ font-size: 22px; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kpi-sub {{ font-size: 11px; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 4px; }}
        .trend-up {{ color: var(--accent-emerald); font-weight: 700; }}
        .trend-down {{ color: var(--accent-rose); font-weight: 700; }}

        .charts-wrapper {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: calc(100vh - 230px);
            gap: 14px;
        }}

        .chart-card {{
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            padding: 18px 20px;
            display: flex;
            flex-direction: column;
        }}

        .chart-header {{ margin-bottom: 10px; }}
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
        <div style="margin-left:auto; display:flex; flex-direction:column; align-items:flex-end;">
            <div style="font-size:15px; font-weight:700; color:var(--text-primary);">Phân Tích Thông Tin Sản Phẩm & Doanh Số</div>
            <div style="font-size:11px; color:var(--text-secondary);">Mối liên hệ giữa mức độ thiếu thông tin và hiệu quả bán hàng</div>
        </div>
    </div>

    <!-- KPI ROW -->
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Doanh Số TB (Ít Thiếu)</div>
            <div class="kpi-val" id="kpi_sales_good">0</div>
            <div class="kpi-sub">So với SP Thiếu Nhiều: <span id="kpi_sales_diff">-</span></div>
        </div>
        <div class="kpi-card" style="border-left-color: #9A3412;">
            <div class="kpi-title">Bỏ Trống TB Toàn Ngành</div>
            <div class="kpi-val" id="kpi_missing_avg">0</div>
            <div class="kpi-sub">Trên tổng {total_features} trường thông tin</div>
        </div>
        <div class="kpi-card" style="border-left-color: #F59E0B;">
            <div class="kpi-title">Feature #1 Của Top Doanh Số</div>
            <div class="kpi-val" style="font-size: 17px" id="kpi_top_feat">-</div>
            <div class="kpi-sub">Xuất hiện nhiều nhất ở SP bán chạy</div>
        </div>
        <div class="kpi-card" style="border-left-color: var(--accent-blue);">
            <div class="kpi-title">Tổng SP Đang Phân Tích</div>
            <div class="kpi-val" id="kpi_total_products">0</div>
            <div class="kpi-sub">Tổng sản phẩm theo bộ lọc</div>
        </div>
    </div>

    <!-- CHARTS -->
    <div class="charts-wrapper">
        
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">📉 Sự Chuyển Biến Doanh Số Theo Mức Thiếu Thông Tin</div>
                <div class="chart-subtitle">Trục X: Số Features Thiếu &nbsp;|&nbsp; Trục Y: Doanh Số TB (lượt bán) &nbsp;|&nbsp; Cột: Số lượng SP</div>
            </div>
            <div class="chart-container"><canvas id="c_trend"></canvas></div>
            <div class="legend-row">
                <div class="legend-item"><div class="legend-dot" style="background: rgba(249,115,22,0.85);"></div>Doanh số TB (Line)</div>
                <div class="legend-item"><div class="legend-dot" style="background: rgba(251,146,60,0.35);"></div>Số lượng SP (Bar)</div>
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">🏆 Feature Phân Hoá: Top 10% Doanh Số vs Toàn Bộ</div>
                <div class="chart-subtitle">Ưu tiên hiển thị các trường thông tin có độ chênh lệch cao nhất</div>
            </div>
            <div class="chart-container"><canvas id="c_features"></canvas></div>
        </div>

    </div>

<script>
    const RAW_DATA = {data_json_str};
    const TOP_FEATS_DATA = {top_feats_json_str};
    const ALL_FEATS_DATA = {all_feats_json_str};
    const TOTAL_FEATS = {total_features};
    let CHARTS = {{}};

    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));

    function setup() {{
        Chart.register(ChartDataLabels);
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.family = "'Inter', sans-serif";
        
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

    function processData(data, cat) {{
        // --- KPIs ---
        let totalMissing = 0;
        data.forEach(d => totalMissing += d.missing_count);
        let avgMissing = data.length ? totalMissing / data.length : 0;

        // Quartile split for KPI comparison
        let sortedByMissing = [...data].sort((a,b) => a.missing_count - b.missing_count);
        let q1End = Math.floor(data.length * 0.25);
        let q4Start = Math.floor(data.length * 0.75);
        
        let lowMissing = sortedByMissing.slice(0, Math.max(1, q1End));
        let highMissing = sortedByMissing.slice(q4Start);
        
        let avgSalesLow = lowMissing.reduce((s,d) => s + d.sales_volume_num, 0) / (lowMissing.length || 1);
        let avgSalesHigh = highMissing.reduce((s,d) => s + d.sales_volume_num, 0) / (highMissing.length || 1);

        document.getElementById('kpi_missing_avg').innerText = Math.round(avgMissing);
        document.getElementById('kpi_sales_good').innerText = fmtN(avgSalesLow);
        document.getElementById('kpi_total_products').innerText = fmtN(data.length);
        
        let diff_el = document.getElementById('kpi_sales_diff');
        if (avgSalesHigh > 0 && avgSalesLow > avgSalesHigh) {{
            let mult = (avgSalesLow / avgSalesHigh).toFixed(1);
            diff_el.innerHTML = `<span class="trend-up">Gấp ${{mult}}x</span>`;
        }} else if (avgSalesLow <= avgSalesHigh) {{
            diff_el.innerHTML = `<span class="trend-down">Thấp hơn</span>`;
        }} else {{
            diff_el.innerHTML = `<span style="color:#9CA3AF">N/A</span>`;
        }}

        let topFeatData = TOP_FEATS_DATA[cat] || {{}};
        let allFeatData = ALL_FEATS_DATA[cat] || {{}};
        
        let diffsList = Object.keys(topFeatData).map(f => {{
            return {{
                f: f, 
                diff: (topFeatData[f] || 0) - (allFeatData[f] || 0),
                t: topFeatData[f] || 0
            }};
        }}).filter(item => item.t > 5); // Tồn tại ít nhất 5%
        
        diffsList.sort((a,b) => b.diff - a.diff);
        
        let kpiFeatEl = document.getElementById('kpi_top_feat');
        let kpiTitleEl = kpiFeatEl.previousElementSibling;
        let kpiSubEl = kpiFeatEl.nextElementSibling;
        
        if (diffsList.length > 0 && diffsList[0].diff > 0.1) {{
            kpiTitleEl.innerText = "Feature Tạo Sự Khác Biệt";
            kpiFeatEl.innerText = diffsList[0].f.toUpperCase();
            kpiFeatEl.style.fontSize = "16px";
            kpiSubEl.innerHTML = `Chênh lệch <span class="trend-up">+${{diffsList[0].diff.toFixed(1)}}%</span> so với trung bình`;
        }} else {{
            kpiTitleEl.innerText = "Feature #1 Của Top Doanh Số";
            kpiFeatEl.innerText = Object.keys(topFeatData).length ? Object.keys(topFeatData)[0].toUpperCase() : 'N/A';
            kpiSubEl.innerText = "Xuất hiện nhiều nhất ở SP bán chạy";
        }}

        // --- Chart 1: Trend line (sales transition vs missing count) ---
        let bucketMap = new Map();
        let bucketSize = 3; // group every 3 missing counts
        data.forEach(d => {{
            let bucket = Math.floor(d.missing_count / bucketSize) * bucketSize;
            if (!bucketMap.has(bucket)) bucketMap.set(bucket, {{ totalSales: 0, count: 0 }});
            let b = bucketMap.get(bucket);
            b.totalSales += d.sales_volume_num;
            b.count++;
        }});

        let sortedBuckets = Array.from(bucketMap.keys()).sort((a,b) => a - b);
        let trendLabels = sortedBuckets.map(b => b + '-' + (b + bucketSize - 1));
        let trendSales = sortedBuckets.map(b => {{
            let bk = bucketMap.get(b);
            return bk.count > 0 ? Math.round(bk.totalSales / bk.count) : 0;
        }});
        let trendCounts = sortedBuckets.map(b => bucketMap.get(b).count);

        updateTrendChart(trendLabels, trendSales, trendCounts);

        // --- Chart 2: Feature distribution comparison ---
        let topFeats = TOP_FEATS_DATA[cat] || {{}};
        let allFeats = ALL_FEATS_DATA[cat] || {{}};
        
        // Calculate diff to find the features with highest gap
        let diffList = Object.keys(topFeats).map(f => {{
            let t = topFeats[f] || 0;
            let a = allFeats[f] || 0;
            return {{ f: f, t: t, a: a, diff: t - a }};
        }});
        
        // Sort by biggest positive difference, then by max Top%
        diffList.sort((a,b) => {{
            if (Math.abs(b.diff - a.diff) > 0.1) return b.diff - a.diff; 
            return b.t - a.t;
        }});
        
        // Take top 14 features that matter most
        let topDiffs = diffList.slice(0, 14);
        
        let featLabels = topDiffs.map(d => d.f);
        let topValues = topDiffs.map(d => d.t);
        let allValues = topDiffs.map(d => d.a);

        updateFeaturesChart(featLabels, topValues, allValues);
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

    function updateFeaturesChart(labels, topData, allData) {{
        CHARTS.features.data.labels = labels;
        CHARTS.features.data.datasets[0].data = topData;
        CHARTS.features.data.datasets[1].data = allData;
        CHARTS.features.update();
    }}

    function initCharts() {{
        // --- Chart 1: Dual-axis Area + Bar (Trend) ---
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
                        label: 'Doanh Số TB',
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
                            offset: 4
                        }}
                    }},
                    {{
                        label: 'Số Lượng SP',
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
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                scales: {{
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 0 }},
                        title: {{ display: true, text: 'Số Features Thiếu', color: '#78716C', font: {{ size: 11, weight: '600' }} }}
                    }},
                    y: {{
                        position: 'left',
                        grid: {{ color: 'rgba(0,0,0,0.04)' }},
                        ticks: {{ callback: (v) => fmtN(v), font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Doanh Số TB (lượt bán)', color: '#ea580c', font: {{ size: 11, weight: '600' }} }}
                    }},
                    y1: {{
                        position: 'right',
                        grid: {{ drawOnChartArea: false }},
                        ticks: {{ font: {{ size: 10 }} }},
                        title: {{ display: true, text: 'Số Lượng SP', color: 'rgba(251,146,60,0.8)', font: {{ size: 11, weight: '600' }} }},
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
                                return 'Thiếu ' + tooltipItems[0].label + ' features';
                            }},
                            label: function(ctx) {{
                                if (ctx.datasetIndex === 0) return '  Doanh Số TB: ' + fmtN(ctx.raw) + ' lượt';
                                return '  Số SP: ' + fmtN(ctx.raw) + ' sản phẩm';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // --- Chart 2: Grouped Horizontal Bar (Feature comparison) ---
        let ctxFeats = document.getElementById('c_features').getContext('2d');
        CHARTS.features = new Chart(ctxFeats, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'Top 10% Doanh Số',
                        data: [],
                        backgroundColor: 'rgba(249, 115, 22, 0.75)',
                        borderColor: '#ea580c',
                        borderWidth: 1,
                        borderRadius: 3,
                        barPercentage: 0.7,
                        categoryPercentage: 0.8
                    }},
                    {{
                        label: 'Tất Cả Sản Phẩm',
                        data: [],
                        backgroundColor: 'rgba(59, 130, 246, 0.45)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        borderRadius: 3,
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
                        grid: {{ color: 'rgba(0,0,0,0.04)' }},
                        max: 100,
                        ticks: {{ callback: (v) => v + '%', font: {{ size: 10 }} }},
                        title: {{ display: true, text: '% Sản Phẩm Cung Cấp Feature Này', color: '#78716C', font: {{ size: 11, weight: '600' }} }}
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ font: {{ size: 10, weight: '500' }}, color: '#44403C' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'bottom',
                        labels: {{
                            boxWidth: 12,
                            boxHeight: 12,
                            borderRadius: 3,
                            useBorderRadius: true,
                            padding: 16,
                            font: {{ size: 11, weight: '500' }},
                            color: '#44403C'
                        }}
                    }},
                    datalabels: {{
                        display: function(ctx) {{
                            return ctx.datasetIndex === 0; // Only show labels for top 20%
                        }},
                        color: '#9A3412',
                        font: {{ weight: '700', size: 10 }},
                        formatter: (v) => v + '%',
                        anchor: 'end',
                        align: 'right',
                        offset: 2
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(28,25,23,0.92)',
                        titleFont: {{ size: 12, weight: '600' }},
                        bodyFont: {{ size: 11 }},
                        padding: 10,
                        cornerRadius: 6,
                        callbacks: {{
                            label: function(ctx) {{
                                let dsLabel = ctx.dataset.label;
                                return `  ${{dsLabel}}: ${{ctx.raw}}%`;
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
    
    components.html(html_code, height=680, scrolling=False)
