import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

def render(df_raw):
    df = df_raw.copy()

    # 1. Robust Feature Engineering & Type Conversion
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

    # 2. Export clean JSON data
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
            --text-secondary: #78716C;
            --border-radius: 12px;
            --font-family: 'Inter', sans-serif;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{ 
            background-color: var(--bg); 
            font-family: var(--font-family); 
            color: var(--text-primary); 
            padding: 10px 15px; 
            overflow-x: hidden; 
        }}
        
        .kpi-row {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 15px; 
            margin-bottom: 15px; 
        }}
        
        .kpi-card {{ 
            background: var(--card-bg); 
            padding: 15px; 
            border-radius: var(--border-radius); 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
            border-left: 5px solid var(--primary); 
        }}
        
        .kpi-title {{ 
            font-size: 10px; 
            font-weight: 700; 
            color: var(--text-secondary); 
            text-transform: uppercase; 
            margin-bottom: 5px; 
            letter-spacing: 0.05em;
        }}
        
        .kpi-value {{ 
            font-size: 22px; 
            font-weight: 700; 
            color: var(--text-primary); 
        }}

        .chart-grid {{ 
            display: grid; 
            grid-template-columns: 1fr 1.2fr; 
            gap: 15px; 
            margin-bottom: 15px; 
        }}
        
        .chart-card {{ 
            background: var(--card-bg); 
            padding: 15px; 
            border-radius: var(--border-radius); 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        }}
        
        .chart-title {{ 
            font-size: 14px; 
            font-weight: 600; 
            margin-bottom: 15px; 
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .chart-container {{ 
            position: relative; 
            height: 240px; 
            width: 100%;
        }}
        
        .full-row {{ grid-column: span 2; }}
    </style>
</head>
<body>
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Mức giảm giá TB</div>
            <div class="kpi-value" id="kpi_avg_discount">0%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">SP đang khuyến mãi</div>
            <div class="kpi-value" id="kpi_sale_count">0%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Giá bán trung bình</div>
            <div class="kpi-value" id="kpi_avg_price">$0</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Tổng doanh số (ước tính)</div>
            <div class="kpi-value" id="kpi_sales_impact">0</div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">Phân phối Mức giảm giá (%)</div>
            <div class="chart-container"><canvas id="histChart"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-title">Hiệu quả doanh số theo mức giảm</div>
            <div class="chart-container"><canvas id="salesBarChart"></canvas></div>
        </div>
        <div class="chart-card full-row">
            <div class="chart-title">Chiến lược Giá & Hiệu quả: Amazon Prime</div>
            <div class="chart-container" style="height: 180px;"><canvas id="primeChart"></canvas></div>
        </div>
    </div>

    <script>
        const rawData = {data_json_str};

        function formatN(n) {{ return n.toLocaleString(); }}

        function init() {{
            const withDiscount = rawData.filter(d => d.discount_rate > 0);
            const avgDiscount = rawData.length ? rawData.reduce((a, b) => a + b.discount_rate, 0) / rawData.length : 0;
            const salePct = rawData.length ? (withDiscount.length / rawData.length) * 100 : 0;
            const avgPrice = rawData.length ? rawData.reduce((a, b) => a + b.price, 0) / rawData.length : 0;
            const totalSales = rawData.reduce((a, b) => a + (b.sales_volume_num || 0), 0);

            document.getElementById('kpi_avg_discount').innerText = avgDiscount.toFixed(1) + "%";
            document.getElementById('kpi_sale_count').innerText = salePct.toFixed(1) + "%";
            document.getElementById('kpi_avg_price').innerText = "$" + avgPrice.toFixed(2);
            document.getElementById('kpi_sales_impact').innerText = formatN(totalSales);

            renderCharts();
        }}

        function renderCharts() {{
            const bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101];
            const labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '>90%'];
            
            const counts = new Array(labels.length).fill(0);
            const sumSales = new Array(labels.length).fill(0);
            const countSales = new Array(labels.length).fill(0);
            
            rawData.forEach(d => {{
                for(let i=0; i<bins.length-1; i++) {{
                    if(d.discount_rate >= bins[i] && d.discount_rate < bins[i+1]) {{
                        counts[i]++;
                        if(d.sales_volume_num > 0) {{
                            sumSales[i] += d.sales_volume_num;
                            countSales[i]++;
                        }}
                        break;
                    }}
                }}
            }});

            const avgSalesByBin = sumSales.map((sum, i) => countSales[i] ? Math.round(sum / countSales[i]) : 0);

            // 1. Histogram
            new Chart(document.getElementById('histChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{ label: 'Số lượng SP', data: counts, backgroundColor: '#F97316', borderRadius: 6 }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ 
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Số lượng sản phẩm' }} }}, 
                        x: {{ grid: {{ display: false }} }} 
                    }}
                }}
            }});

            // 2. Sales Bar
            new Chart(document.getElementById('salesBarChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{ label: 'Doanh số TB', data: avgSalesByBin, backgroundColor: '#9A3412', borderRadius: 6 }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ 
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Lượt bán trung bình' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            // 3. Original Merged Prime Chart
            renderPrimeChart();
        }}

        function renderPrimeChart() {{
            const prime = rawData.filter(d => d.is_prime);
            const nonPrime = rawData.filter(d => !d.is_prime);
            const avgP = [
                prime.length ? prime.reduce((a,b)=>a+b.price,0)/prime.length : 0,
                nonPrime.length ? nonPrime.reduce((a,b)=>a+b.price,0)/nonPrime.length : 0
            ];
            const avgS = [
                prime.length ? prime.reduce((a,b)=>a+(b.sales_volume_num||0),0)/prime.length : 0,
                nonPrime.length ? nonPrime.reduce((a,b)=>a+(b.sales_volume_num||0),0)/nonPrime.length : 0
            ];

            new Chart(document.getElementById('primeChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: ['Amazon Prime', 'Thường'],
                    datasets: [
                        {{ label: 'Giá bán TB ($)', data: avgP, backgroundColor: '#F97316', borderRadius: 6 }},
                        {{ label: 'Lượt bán TB', data: avgS, backgroundColor: '#9A3412', borderRadius: 6 }}
                    ]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ beginAtZero: true, grid: {{ display: false }} }},
                        y: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});
        }}

        init();
    </script>
</body>
</html>
    """
    components.html(html_code, height=750, scrolling=False)
