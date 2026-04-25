import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# Import category mapping from utility script
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.category_mapping import CATEGORY_MAP, add_display_column

def render(df_raw):
    df = df_raw.copy()

    # 1. Feature Engineering
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    else:
        df["price"] = 0.0

    if "original_price" not in df.columns or df["original_price"].isnull().all():
        df["original_price"] = df["price"]
    else:
        df["original_price"] = pd.to_numeric(df["original_price"], errors="coerce").fillna(df["price"])

    df["discount"] = df["original_price"] - df["price"]
    df["discount_rate"] = np.where(df["original_price"] > 0, (df["discount"] / df["original_price"]) * 100, 0.0)
    df["discount_rate"] = df["discount_rate"].clip(0, 100)

    if "sales_volume_num" not in df.columns:
        df["sales_volume_num"] = 0
    else:
        df["sales_volume_num"] = pd.to_numeric(df["sales_volume_num"], errors="coerce").fillna(0)

    if "is_prime" not in df.columns:
        df["is_prime"] = False
    else:
        df["is_prime"] = df["is_prime"].fillna(False).astype(bool)

    if "crawl_category" not in df.columns:
        if "category" in df.columns:
            df["crawl_category"] = df["category"]
        else:
            df["crawl_category"] = "Không rõ"
    df["crawl_category"] = df["crawl_category"].fillna("Không rõ")

    # 2. Map category names (does NOT modify crawl_category — safe for other tabs)
    df = add_display_column(df, source_col="crawl_category", target_col="display_category")

    # 3. Export clean JSON data
    export_cols = ["display_category", "price", "original_price", "discount_rate", "sales_volume_num", "is_prime"]
    existing_cols = [c for c in export_cols if c in df.columns]
    data_json_str = df[existing_cols].to_json(orient="records")

    html_code = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #F97316;
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 12px;
            --font-family: 'Inter', sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background-color: var(--bg); font-family: var(--font-family); color: var(--text-primary); padding: 8px; }}

        .filter-bar {{
            display: flex; align-items: flex-end; gap: 24px;
            background: var(--card-bg); padding: 12px 20px;
            border-radius: var(--border-radius); margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            flex-wrap: wrap;
        }}
        .f-item {{ display: flex; flex-direction: column; gap: 6px; }}
        .f-label {{ font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; }}
        select {{
            padding: 8px 12px; border: 1px solid #D1D5DB; border-radius: 6px;
            font-family: inherit; color: var(--text-primary); outline: none; cursor: pointer; width: 200px;
        }}
        select:focus {{ border-color: var(--primary); }}

        .toggle-group {{ display: flex; gap: 10px; align-items: center; cursor: pointer; user-select: none; padding-bottom: 2px; }}
        .toggle-track {{
            position: relative; width: 50px; height: 28px;
            background-color: #E5E7EB; border-radius: 20px; transition: background-color 0.3s;
        }}
        .toggle-track.active {{ background-color: var(--primary); }}
        .toggle-thumb {{
            position: absolute; top: 2px; left: 2px;
            width: 24px; height: 24px; background: white;
            border-radius: 50%; transition: transform 0.3s;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}
        .toggle-track.active .toggle-thumb {{ transform: translateX(22px); }}
        .toggle-lbl {{ font-size: 15px; font-weight: 600; }}

        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px; }}
        .kpi-card {{ background: var(--card-bg); padding: 10px 15px; border-radius: var(--border-radius); border-left: 4px solid var(--primary); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .kpi-title {{ font-size: 9px; color: var(--text-secondary); text-transform: uppercase; font-weight: 700; margin-bottom: 2px; }}
        .kpi-value {{ font-size: 20px; font-weight: 700; }}

        .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
        .bottom-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}

        .chart-card {{ background: var(--card-bg); padding: 12px; border-radius: var(--border-radius); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .chart-title {{ font-size: 13px; font-weight: 600; margin-bottom: 8px; color: #444; }}
        .chart-container {{ position: relative; height: 210px; width: 100%; }}
        .chart-container-large {{ position: relative; height: 260px; width: 100%; }}
    </style>
</head>
<body>
    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Danh mục</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả</option>
            </select>
        </div>
        <div class="toggle-group" onclick="togglePrime()">
            <div class="toggle-track" id="primeTrack"><div class="toggle-thumb"></div></div>
            <span class="toggle-lbl">Prime</span>
        </div>
    </div>

    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-title">Mức giảm giá TB</div><div class="kpi-value" id="kpi_avg_discount">0%</div></div>
        <div class="kpi-card"><div class="kpi-title">SP đang khuyến mãi</div><div class="kpi-value" id="kpi_sale_count">0%</div></div>
        <div class="kpi-card"><div class="kpi-title">Giá bán trung bình</div><div class="kpi-value" id="kpi_avg_price">$0</div></div>
        <div class="kpi-card"><div class="kpi-title">Tổng doanh số</div><div class="kpi-value" id="kpi_sales_impact">0</div></div>
    </div>

    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title" id="histTitle">Phân phối Mức giảm giá (%)</div>
            <div class="chart-container"><canvas id="histChart"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-title">Hiệu quả theo mức giảm</div>
            <div class="chart-container"><canvas id="salesBarChart"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-title">Phân khúc Ưu đãi thị trường</div>
            <div class="chart-container"><canvas id="discountPieChart"></canvas></div>
        </div>
    </div>

    <div class="bottom-grid">
        <div class="chart-card">
            <div class="chart-title" id="bottomLeftTitle">Top 5 Ngành hàng giảm giá sâu nhất</div>
            <div class="chart-container-large"><canvas id="bottomLeftChart"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-title" id="bottomRightTitle">Top 5 Ngành hàng Doanh số cao nhất</div>
            <div class="chart-container-large"><canvas id="bottomRightChart"></canvas></div>
        </div>
    </div>

    <script>
        const RAW_DATA = {data_json_str};
        let charts = {{}};
        let primeOn = false;
        let selectedBin = -1;
        const BINS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101];
        const BIN_LABELS = ['0-10%','10-20%','20-30%','30-40%','40-50%','50-60%','60-70%','70-80%','80-90%','>90%'];

        // Compact number: 1500 -> 1.5K
        function fmtK(val) {{
            if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
            if (val >= 1e3) return (val / 1e3).toFixed(1) + 'K';
            return val.toString();
        }}

        // Prime toggle via JS (avoids checkbox click issues in Streamlit iframe)
        function togglePrime() {{
            primeOn = !primeOn;
            document.getElementById('primeTrack').classList.toggle('active', primeOn);
            applyFilters();
        }}

        function applyFilters() {{
            const cat = document.getElementById('selCategory').value;
            let data = RAW_DATA;
            if (primeOn) data = data.filter(d => d.is_prime);
            if (cat !== 'ALL') data = data.filter(d => d.display_category === cat);
            updateDashboard(data, cat);
        }}

        function selectBin(idx) {{
            selectedBin = (selectedBin === idx) ? -1 : idx;

            // Update histogram bar colors directly
            const ds = charts.hist.data.datasets[0];
            const n = ds.data.length;
            
            if (selectedBin === -1) {{
                ds.backgroundColor = new Array(n).fill('#F97316');
                document.getElementById('histTitle').innerText = 'Phân phối Mức giảm giá (%)';
            }} else {{
                // Fade others, highlight selected
                const newColors = new Array(n).fill('rgba(249,115,22,0.25)');
                newColors[selectedBin] = '#EA580C';
                ds.backgroundColor = newColors;
                document.getElementById('histTitle').innerText = 'Phân phối Mức giảm giá (%) — lọc: ' + BIN_LABELS[selectedBin];
            }}
            
            charts.hist.update();
            applyFilters();
        }}

        function handleHistClick(e) {{
            const points = charts.hist.getElementsAtEventForMode(e, 'index', {{ intersect: false }}, true);
            if (points.length > 0) {{
                selectBin(points[0].index);
            }}
        }}


        function updateDashboard(fullData, selectedCat) {{
            // Histogram always uses full data (not bin-filtered)
            const counts = new Array(10).fill(0), sumS = new Array(10).fill(0), cntS = new Array(10).fill(0);
            fullData.forEach(d => {{
                for (let i = 0; i < 10; i++) {{
                    if (d.discount_rate >= BINS[i] && d.discount_rate < BINS[i + 1]) {{
                        counts[i]++;
                        if (d.sales_volume_num > 0) {{ sumS[i] += d.sales_volume_num; cntS[i]++; }}
                        break;
                    }}
                }}
            }});
            charts.hist.data.datasets[0].data = counts;
            // Re-apply bin highlight colors
            const n = counts.length;
            if (selectedBin === -1) {{
                charts.hist.data.datasets[0].backgroundColor = new Array(n).fill('#F97316');
            }} else {{
                const cols = new Array(n).fill('rgba(249,115,22,0.2)');
                cols[selectedBin] = '#EA580C';
                charts.hist.data.datasets[0].backgroundColor = cols;
            }}
            charts.hist.update();

            // Filter data by selected bin for all other charts
            let data = fullData;
            if (selectedBin >= 0) {{
                const lo = BINS[selectedBin], hi = BINS[selectedBin + 1];
                data = fullData.filter(d => d.discount_rate >= lo && d.discount_rate < hi);
            }}

            // KPIs (use bin-filtered data)
            const withD = data.filter(x => x.discount_rate > 0);
            const avgD = data.length ? data.reduce((a, b) => a + b.discount_rate, 0) / data.length : 0;
            const avgP = data.length ? data.reduce((a, b) => a + b.price, 0) / data.length : 0;
            const totalS = data.reduce((a, b) => a + (b.sales_volume_num || 0), 0);
            document.getElementById('kpi_avg_discount').innerText = avgD.toFixed(1) + '%';
            document.getElementById('kpi_sale_count').innerText = (data.length ? (withD.length / data.length * 100) : 0).toFixed(1) + '%';
            document.getElementById('kpi_avg_price').innerText = '$' + avgP.toFixed(2);
            document.getElementById('kpi_sales_impact').innerText = '$' + totalS.toLocaleString();

            // Line chart (use bin-filtered data)
            charts.sales.data.datasets[0].data = sumS.map((s, i) => cntS[i] ? Math.round(s / cntS[i]) : 0);
            charts.sales.update();

            // Pie (use bin-filtered data)
            const seg = [
                data.filter(x => x.discount_rate <= 0).length,
                data.filter(x => x.discount_rate > 0 && x.discount_rate <= 20).length,
                data.filter(x => x.discount_rate > 20 && x.discount_rate <= 50).length,
                data.filter(x => x.discount_rate > 50).length
            ];
            charts.pie.data.datasets[0].data = seg;
            charts.pie.update();

            // Bottom charts (use bin-filtered data)
            renderBottom(data, selectedCat);
        }}

        function renderBottom(data, selectedCat) {{

            // Category selected → category detail
            if (selectedCat !== 'ALL') {{
                document.getElementById('bottomLeftTitle').innerText = 'Phân bố giá — ' + selectedCat;
                document.getElementById('bottomRightTitle').innerText = 'Giảm giá vs Doanh số — ' + selectedCat;
                const prices = data.map(d => d.price).filter(p => p > 0);
                const maxP = prices.length ? Math.max(...prices) : 100;
                const step = Math.ceil(maxP / 5) || 1;
                const pL = [], pC = [];
                for (let i = 0; i < 5; i++) {{ const lo=i*step, hi=(i+1)*step; pL.push('$'+lo+'-'+hi); pC.push(prices.filter(p=>p>=lo&&p<hi).length); }}
                charts.bLeft.data.labels = pL; charts.bLeft.data.datasets[0].data = pC;
                charts.bLeft.options.scales.x.ticks.callback = function(v) {{ return v; }};
                charts.bLeft.update();
                const dL = ['0-20%','20-40%','40-60%','60-80%','80-100%'], dB = [0,20,40,60,80,101];
                const dS = new Array(5).fill(0), dN = new Array(5).fill(0);
                data.forEach(d => {{ for(let i=0;i<5;i++) {{ if(d.discount_rate>=dB[i]&&d.discount_rate<dB[i+1]) {{ if(d.sales_volume_num>0){{dS[i]+=d.sales_volume_num;dN[i]++;}} break; }} }} }});
                charts.bRight.data.labels = dL; charts.bRight.data.datasets[0].data = dS.map((s,i)=>dN[i]?Math.round(s/dN[i]):0);
                charts.bRight.options.scales.x.ticks.callback = function(v) {{ return fmtK(v); }};
                charts.bRight.update();
                return;
            }}

            // Default: Top 5 overview
            document.getElementById('bottomLeftTitle').innerText = 'Top 5 Ngành hàng giảm giá sâu nhất';
            document.getElementById('bottomRightTitle').innerText = 'Top 5 Ngành hàng Doanh số cao nhất';
            const aggC = {{}};
            data.forEach(d => {{
                const cat = d.display_category || 'Không rõ';
                if (!aggC[cat]) aggC[cat] = {{ sumD: 0, cntD: 0, sumS: 0 }};
                aggC[cat].sumD += d.discount_rate; aggC[cat].cntD++;
                aggC[cat].sumS += (d.sales_volume_num || 0);
            }});
            const catArr = Object.keys(aggC).map(k => ({{ n: k, avgD: aggC[k].sumD / aggC[k].cntD, totalS: aggC[k].sumS }}));
            const topD = [...catArr].sort((a,b) => b.avgD - a.avgD).slice(0, 5);
            charts.bLeft.data.labels = topD.map(x=>x.n); charts.bLeft.data.datasets[0].data = topD.map(x=>x.avgD);
            charts.bLeft.options.scales.x.ticks.callback = function(v) {{ return v.toFixed(0)+'%'; }};
            charts.bLeft.update();
            const topS = [...catArr].sort((a,b) => b.totalS - a.totalS).slice(0, 5);
            charts.bRight.data.labels = topS.map(x=>x.n); charts.bRight.data.datasets[0].data = topS.map(x=>x.totalS);
            charts.bRight.options.scales.x.ticks.callback = function(v) {{ return fmtK(v); }};
            charts.bRight.update();
        }}

        function initCharts() {{
            Chart.defaults.font.family = "'Inter', sans-serif";
            Chart.defaults.color = '#78716C';
            const opt = {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }};
            const labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '>90%'];

            charts.hist = new Chart(document.getElementById('histChart'), {{
                type: 'bar',
                data: {{ labels, datasets: [{{ data: [], backgroundColor: '#F97316', borderRadius: 4 }}] }},
                options: {{ ...opt, scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: 'Số sản phẩm', font: {{ size: 11 }} }} }}, x: {{ grid: {{ display: false }} }} }} }}
            }});
            charts.sales = new Chart(document.getElementById('salesBarChart'), {{
                type: 'line',
                data: {{ labels, datasets: [{{ data: [], borderColor: '#9A3412', backgroundColor: 'rgba(154,52,18,0.1)', fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: '#9A3412', pointBorderColor: '#fff', pointBorderWidth: 2 }}] }},
                options: {{ ...opt, scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: 'Doanh số TB/SP', font: {{ size: 11 }} }} }}, x: {{ grid: {{ display: false }} }} }} }}
            }});
            charts.pie = new Chart(document.getElementById('discountPieChart'), {{
                type: 'doughnut',
                data: {{ labels: ['Gốc', '<20%', '20-50%', '>50%'], datasets: [{{ data: [], backgroundColor: ['#78716C', '#FED7AA', '#F97316', '#9A3412'], borderWidth: 0 }}] }},
                options: {{ ...opt, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 9 }} }} }} }} }}
            }});

            // Bottom charts (reusable — content changes based on selection)
            charts.bLeft = new Chart(document.getElementById('bottomLeftChart'), {{
                type: 'bar',
                data: {{ labels: [], datasets: [{{ data: [], backgroundColor: '#EA580C', borderRadius: 4 }}] }},
                options: {{ ...opt, indexAxis: 'y', scales: {{ x: {{ beginAtZero: true, title: {{ display: true, text: 'Giảm giá TB (%)', font: {{ size: 11 }} }}, ticks: {{ callback: function(v) {{ return v; }} }} }}, y: {{ ticks: {{ font: {{ size: 11 }} }} }} }} }}
            }});
            charts.bRight = new Chart(document.getElementById('bottomRightChart'), {{
                type: 'bar',
                data: {{ labels: [], datasets: [{{ data: [], backgroundColor: '#9A3412', borderRadius: 4 }}] }},
                options: {{ ...opt, indexAxis: 'y', scales: {{ x: {{ beginAtZero: true, title: {{ display: true, text: 'Tổng doanh số (lượt)', font: {{ size: 11 }} }}, ticks: {{ callback: function(v) {{ return fmtK(v); }} }} }}, y: {{ ticks: {{ font: {{ size: 11 }} }} }} }} }}
            }});
        }}

        function setup() {{
            // Populate category dropdown
            const cats = [...new Set(RAW_DATA.map(d => d.display_category))].sort();
            const sel = document.getElementById('selCategory');
            cats.forEach(c => {{
                if (c && c !== 'Không rõ') {{
                    const o = document.createElement('option');
                    o.value = c; o.innerText = c;
                    sel.appendChild(o);
                }}
            }});
            initCharts();
            
            // Native click listener on histogram canvas
            document.getElementById('histChart').addEventListener('click', handleHistClick);

            applyFilters();
        }}

        document.addEventListener('DOMContentLoaded', setup);
    </script>
</body>
</html>
    """
    components.html(html_code, height=900, scrolling=False)
