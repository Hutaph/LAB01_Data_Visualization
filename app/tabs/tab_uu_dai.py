import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

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

    # 2. Data for Category Analysis
    cat_stats = df.groupby("crawl_category")["discount_rate"].mean().sort_values(ascending=False).head(5)
    cat_data = {
        "labels": cat_stats.index.tolist(),
        "values": cat_stats.values.tolist()
    }

    # 3. Export clean JSON data
    select_cols = ["crawl_category", "price", "original_price", "discount_rate", "sales_volume_num", "is_prime"]
    existing_cols = [c for c in select_cols if c in df.columns]
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
            --border-radius: 12px;
            --font-family: 'Inter', sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background-color: var(--bg); font-family: var(--font-family); color: var(--text-primary); padding: 8px; overflow: hidden; }}
        
        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px; }}
        .kpi-card {{ background: var(--card-bg); padding: 10px 15px; border-radius: var(--border-radius); border-left: 4px solid var(--primary); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .kpi-title {{ font-size: 9px; color: #78716C; text-transform: uppercase; font-weight: 700; margin-bottom: 2px; }}
        .kpi-value {{ font-size: 20px; font-weight: 700; }}

        .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
        .bottom-grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 10px; }}
        
        .chart-card {{ background: var(--card-bg); padding: 12px; border-radius: var(--border-radius); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .chart-title {{ font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #444; }}
        .chart-container {{ position: relative; height: 180px; width: 100%; }}
        .chart-container-large {{ height: 210px; }}
    </style>
</head>
<body>
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-title">Mức giảm giá TB</div><div class="kpi-value" id="kpi_avg_discount">0%</div></div>
        <div class="kpi-card"><div class="kpi-title">SP đang khuyến mãi</div><div class="kpi-value" id="kpi_sale_count">0%</div></div>
        <div class="kpi-card"><div class="kpi-title">Giá bán trung bình</div><div class="kpi-value" id="kpi_avg_price">$0</div></div>
        <div class="kpi-card"><div class="kpi-title">Tổng doanh số</div><div class="kpi-value" id="kpi_sales_impact">0</div></div>
    </div>

    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">Phân phối Mức giảm giá (%)</div>
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
            <div class="chart-title">Top 5 Ngành hàng giảm giá sâu nhất (%)</div>
            <div class="chart-container-large"><canvas id="catChart"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-title">Chiến lược Giá & Hiệu quả: Prime</div>
            <div class="chart-container-large"><canvas id="primeChart"></canvas></div>
        </div>
    </div>

    <script>
        const rawData = {data_json_str};
        const catData = {json.dumps(cat_data)};

        function formatN(n) {{ return n.toLocaleString(); }}

        function init() {{
            const withDiscount = rawData.filter(d => d.discount_rate > 0);
            const avgDiscount = rawData.length ? rawData.reduce((a, b) => a + b.discount_rate, 0) / rawData.length : 0;
            const avgPrice = rawData.length ? rawData.reduce((a, b) => a + b.price, 0) / rawData.length : 0;
            const totalSales = rawData.reduce((a, b) => a + (b.sales_volume_num || 0), 0);

            document.getElementById('kpi_avg_discount').innerText = avgDiscount.toFixed(1) + "%";
            document.getElementById('kpi_sale_count').innerText = ((withDiscount.length / rawData.length) * 100).toFixed(1) + "%";
            document.getElementById('kpi_avg_price').innerText = "$" + avgPrice.toFixed(2);
            document.getElementById('kpi_sales_impact').innerText = formatN(totalSales);

            renderCharts();
        }}

        function renderCharts() {{
            const labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '>90%'];
            const bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101];
            const counts = new Array(10).fill(0), sumS = new Array(10).fill(0), cntS = new Array(10).fill(0);
            
            rawData.forEach(d => {{
                for(let i=0; i<10; i++) {{
                    if(d.discount_rate >= bins[i] && d.discount_rate < bins[i+1]) {{
                        counts[i]++;
                        if(d.sales_volume_num > 0) {{ sumS[i] += d.sales_volume_num; cntS[i]++; }}
                        break;
                    }}
                }}
            }});
            const avgS = sumS.map((s, i) => cntS[i] ? Math.round(s/cntS[i]) : 0);

            // 1. Histogram
            new Chart(document.getElementById('histChart'), {{
                type: 'bar',
                data: {{ labels, datasets: [{{ label: 'SP', data: counts, backgroundColor: '#F97316', borderRadius: 4 }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }} }}
            }});

            // 2. Sales Bar
            new Chart(document.getElementById('salesBarChart'), {{
                type: 'bar',
                data: {{ labels, datasets: [{{ label: 'Sales', data: avgS, backgroundColor: '#9A3412', borderRadius: 4 }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }} }}
            }});

            // 3. Market Pie
            const d = rawData;
            const seg = [d.filter(x=>x.discount_rate<=0).length, d.filter(x=>x.discount_rate>0&&x.discount_rate<=20).length, d.filter(x=>x.discount_rate>20&&x.discount_rate<=50).length, d.filter(x=>x.discount_rate>50).length];
            new Chart(document.getElementById('discountPieChart'), {{
                type: 'doughnut',
                data: {{ labels: ['Gốc', '<20%', '20-50%', '>50%'], datasets: [{{ data: seg, backgroundColor: ['#78716C', '#FED7AA', '#F97316', '#9A3412'], borderWidth: 0 }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 9 }} }} }} }} }}
            }});

            // 4. Category Analysis (Horizontal)
            new Chart(document.getElementById('catChart'), {{
                type: 'bar',
                data: {{ labels: catData.labels, datasets: [{{ label: 'Giảm giá TB (%)', data: catData.values, backgroundColor: '#EA580C', borderRadius: 6 }}] }},
                options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: {{ x: {{ beginAtZero: true }} }} }}
            }});

            // 5. Prime Comparison
            const p = rawData.filter(x=>x.is_prime), n = rawData.filter(x=>!x.is_prime);
            const pS = [p.length?p.reduce((a,b)=>a+b.price,0)/p.length:0, n.length?n.reduce((a,b)=>a+b.price,0)/n.length:0];
            const sS = [p.length?p.reduce((a,b)=>a+(b.sales_volume_num||0),0)/p.length:0, n.length?n.reduce((a,b)=>a+(b.sales_volume_num||0),0)/n.length:0];
            new Chart(document.getElementById('primeChart'), {{
                type: 'bar',
                data: {{ labels: ['Prime', 'Thường'], datasets: [{{ label: 'Giá ($)', data: pS, backgroundColor: '#F97316' }}, {{ label: 'Sales', data: sS, backgroundColor: '#9A3412' }}] }},
                options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: {{ x: {{ beginAtZero: true }} }} }}
            }});
        }}
        init();
    </script>
</body>
</html>
    """
    components.html(html_code, height=750, scrolling=False)
