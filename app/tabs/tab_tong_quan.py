"""
Tab Tổng quan — Overview dashboard rebuilt dynamically with robust Custom HTML/CSS/JS stack using Chart.js.
It matches the complex UI configuration previously provided.
"""

import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def render(state):
    df_raw = state["df"]

    df = df_raw.copy()
    
    required_bools = ["is_amazon_choice", "is_climate_friendly", "has_variations"]
    for b in required_bools:
        if b not in df.columns:
            df[b] = False
        else:
            df[b] = df[b].fillna(False).astype(bool)

    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"
    df["crawl_category"] = df["crawl_category"].fillna("Không rõ")

    if "price" in df.columns:
        df["current_price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    else:
        df["current_price"] = 0.0

    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    else:
        df["rating"] = 0.0
        
    if "reviews" in df.columns:
        df["reviews"] = pd.to_numeric(df["reviews"], errors="coerce").fillna(0)
    else:
        df["reviews"] = 0

    if "sales_volume_num" in df.columns:
        df["sales_volume_num"] = pd.to_numeric(df["sales_volume_num"], errors="coerce").fillna(0)
    else:
        df["sales_volume_num"] = 0

    if "title" not in df.columns:
         df["title"] = "Sản phẩm ẩn danh"
    else:
         df["title"] = df["title"].fillna("Sản phẩm ẩn danh")

    select_cols = [
        "title", "crawl_category", "current_price", "rating", "reviews", 
        "sales_volume_num", "is_amazon_choice", "is_climate_friendly", "has_variations"
    ]
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
    <style>
        :root {{
            --primary: #F97316;
            --secondary: #F97316;
            --dark: #9A3412;
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 8px;
            --font-family: 'Inter', sans-serif;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            background-color: var(--bg);
            font-family: var(--font-family);
            color: var(--text-primary);
            padding: 20px;
            overflow-y: auto;
            overflow-x: hidden;
        }}

        .filter-bar {{
            display: flex;
            align-items: center;
            gap: 24px;
            margin-bottom: 24px;
            background: var(--card-bg);
            padding: 16px 20px;
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            flex-wrap: wrap;
        }}
        .f-item {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .f-label {{
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}
        select {{
            padding: 8px 12px;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-family: inherit;
            color: var(--text-primary);
            outline: none;
            cursor: pointer;
            width: 200px;
        }}
        select:focus {{ border-color: var(--primary); }}
        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%; background: #FFFFFF;
            border: 2.5px solid #F97316; box-shadow: 0 1px 4px rgba(245,158,11,0.4); cursor: grab; pointer-events: auto;
        }}
        input[type=range]::-webkit-slider-thumb:hover {{ box-shadow: 0 2px 8px rgba(245,158,11,0.6); }}
        input[type=range]::-webkit-slider-thumb:active {{ cursor: grabbing; transform: scale(1.15); }}
        input[type=range]::-moz-range-thumb {{
            width: 20px; height: 20px; border-radius: 50%; background: #FFFFFF;
            border: 2.5px solid #F97316; box-shadow: 0 1px 4px rgba(245,158,11,0.4); cursor: grab; pointer-events: auto; border: none;
        }}
        input[type=range]::-moz-range-thumb:hover {{ box-shadow: 0 2px 8px rgba(245,158,11,0.6); }}
        input[type=range]::-moz-range-thumb:active {{ cursor: grabbing; transform: scale(1.15); }}; font-weight: 500;}}

        .toggle-group {{ display: flex; gap: 8px; align-items: center; cursor: pointer; }}
        .toggle-switch {{
            position: relative; width: 36px; height: 20px;
            background-color: #E5E7EB; border-radius: 20px; transition: 0.3s;
        }}
        .toggle-knob {{
            position: absolute; top: 2px; left: 2px;
            width: 16px; height: 16px; background: white;
            border-radius: 50%; transition: 0.3s;
        }}
        .toggle-checkbox {{ display: none; }}
        .toggle-checkbox:checked + .toggle-switch {{ background-color: var(--primary); }}
        .toggle-checkbox:checked + .toggle-switch .toggle-knob {{ transform: translateX(16px); }}
        .toggle-lbl {{ font-size: 14px; font-weight: 500; }}

        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            padding: 16px;
            border-left: 4px solid var(--primary);
            display: flex; flex-direction: column; gap: 4px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;
        }}
        .kpi-title {{ font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kpi-value {{ font-size: 26px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kpi-sub {{ font-size: 12px; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

        .chart-row-1 {{
            display: grid;
            grid-template-columns: 55% calc(45% - 20px);
            gap: 20px;
            margin-bottom: 24px;
        }}
        .chart-row-2 {{
            margin-bottom: 24px;
        }}
        .chart-card {{
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            padding: 20px;
        }}
        .chart-title {{
            font-size: 15px; font-weight: 600; margin-bottom: 16px; color: var(--text-primary);
        }}
        .chart-wrapper {{
            position: relative;
            width: 100%;
        }}

        .donut-legend {{
            display: flex; justify-content: center; gap: 16px; margin-top: 16px;
        }}
        .dl-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 500; }}
        .dl-sq {{ width: 10px; height: 10px; border-radius: 2px; }}
        
        .combo-legend {{ display: flex; justify-content: flex-end; gap: 16px; margin-bottom: 12px; font-size:12px;font-weight:500;}}
        .cl-item {{display:flex;align-items:center;gap:6px;}}
        .cl-line {{width:16px; height:2px; background:var(--text-primary); position:relative;}}
        .cl-line::after {{content:''; position:absolute; width:6px; height:6px; border-radius:50%; background:var(--text-primary); left:5px; top:-2px;}}

        table {{
            width: 100%; border-collapse: collapse; font-size: 13px;
            table-layout: fixed;
        }}
        th {{
            background: var(--primary); color: #FFFFFF; font-weight: 500; font-size: 13px;
            text-align: left; padding: 12px;
        }}
        th:first-child {{ border-top-left-radius: 6px; width: 35%; }}
        th:nth-child(2) {{ width: 25%; }}
        th:nth-child(3) {{ width: 10%; }}
        th:nth-child(4) {{ width: 15%; }}
        th:last-child {{ border-top-right-radius: 6px; width: 15%; }}
        td {{ padding: 12px; }}
        tbody tr:nth-child(even) {{ background: #FEF3E2; }}
        tbody tr:nth-child(odd) {{ background: #FFFAF5; }}
        tr {{ border-bottom: 1px solid #E5E7EB; }}
        .truncate-col {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    </style>
</head>
<body>

    <!-- Filters -->
    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Danh mục</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả</option>
            </select>
        </div>
        <div class="f-item">
            <div style="display:flex;flex-direction:column;min-width:200px">
                <span style="font-size:11px;font-weight:600;color:#78716C;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:6px">KHOẢNG GIÁ ($)</span>
                <div style="position:relative;height:20px;display:flex;align-items:center">
                    <div id="price_track" style="position:absolute;left:0;right:0;height:4px;border-radius:999px;background:#E5E7EB"></div>
                    <input type="range" id="price_min" min="0" max="3400" step="1" value="0" oninput="updateSliderUI(this); applyFilters()" style="margin:0;position:absolute;width:100%;pointer-events:none;background:transparent;appearance:none;-webkit-appearance:none">
                    <input type="range" id="price_max" min="0" max="3400" step="1" value="3400" oninput="updateSliderUI(this); applyFilters()" style="margin:0;position:absolute;width:100%;pointer-events:none;background:transparent;appearance:none;-webkit-appearance:none">
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:500;color:#1C1917;margin-top:6px">
                    <span id="val_min">$0</span><span id="val_max">$3,400</span>
                </div>
            </div>
        </div>
        <label class="toggle-group" style="margin-left: 12px;">
            <input type="checkbox" id="chkChoice" class="toggle-checkbox" onchange="applyFilters()">
            <div class="toggle-switch"><div class="toggle-knob"></div></div>
            <span class="toggle-lbl">Amazon's Choice</span>
        </label>
        <label class="toggle-group" style="margin-left:12px;">
            <input type="checkbox" id="chkClimate" class="toggle-checkbox" onchange="applyFilters()">
            <div class="toggle-switch"><div class="toggle-knob"></div></div>
            <span class="toggle-lbl">Climate Friendly</span>
        </label>
    </div>

    <!-- KPIs -->
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-title">TỔNG SẢN PHẨM</div><div class="kpi-value" id="kpi_t_prod">0</div><div class="kpi-sub" id="kpi_sub_prod">-</div></div>
        <div class="kpi-card"><div class="kpi-title">GIÁ TRUNG BÌNH</div><div class="kpi-value" id="kpi_avg_price">$0</div><div class="kpi-sub" id="kpi_sub_price">-</div></div>
        <div class="kpi-card"><div class="kpi-title">ĐÁNH GIÁ TB</div><div class="kpi-value" id="kpi_avg_rating">0★</div><div class="kpi-sub" id="kpi_sub_rating">-</div></div>
        <div class="kpi-card"><div class="kpi-title">AMAZON'S CHOICE</div><div class="kpi-value" id="kpi_choice">0</div><div class="kpi-sub" id="kpi_sub_choice">-</div></div>
        <div class="kpi-card"><div class="kpi-title">DOANH SỐ TB/THÁNG</div><div class="kpi-value" id="kpi_sales">0</div><div class="kpi-sub" id="kpi_sub_sales">-</div></div>
    </div>

    <!-- Charts Row 1 -->
    <div class="chart-row-1">
        <div class="chart-card">
            <div class="chart-title">Top 10 Danh mục nhiều sản phẩm nhất</div>
            <div class="chart-wrapper" style="height: 420px;">
                <canvas id="cBarTop"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <div class="chart-title">Tỉ lệ cờ/nhãn đặc biệt</div>
            <div class="chart-wrapper" style="height: 330px; display:flex; justify-content:center;">
                <canvas id="cDonut"></canvas>
            </div>
            <div class="donut-legend">
                <div class="dl-item"><div class="dl-sq" style="background:#FED7AA"></div>Amazon's Choice <span id="lg_choice">0</span></div>
                <div class="dl-item"><div class="dl-sq" style="background:#F97316"></div>Climate Friendly <span id="lg_climate">0</span></div>
                <div class="dl-item"><div class="dl-sq" style="background:#9A3412"></div>Has Variations <span id="lg_vars">0</span></div>
            </div>
        </div>
    </div>

    <!-- Charts Row 2 -->
    <div class="chart-row-2">
        <div class="chart-card">
            <div class="chart-title">Giá trung bình & Doanh số (Top 8 Danh mục)</div>
            <div class="combo-legend">
                <div class="cl-item"><div class="dl-sq" style="background:#F97316"></div>Giá TB ($)</div>
                <div class="cl-item"><div class="cl-line"></div>Doanh số TB (lượt)</div>
            </div>
            <div class="chart-wrapper" style="height: 350px;">
                <canvas id="cCombo"></canvas>
            </div>
        </div>
    </div>

    <!-- Table -->
    <div class="chart-card" style="margin-bottom:40px;">
        <div class="chart-title">Top 5 Sản Phẩm Doanh Số Cao Nhất</div>
        <table>
            <thead>
                <tr>
                    <th>Tên sản phẩm</th>
                    <th>Danh mục</th>
                    <th>Giá ($)</th>
                    <th>Đánh giá (★)</th>
                    <th>Doanh số (lượt)</th>
                </tr>
            </thead>
            <tbody id="tbTop5">
                <!-- Rendered JS -->
            </tbody>
        </table>
    </div>

<script>
    const RAW_DATA = {data_json_str};
    let globalInstances = {{}};

    // Format helpers
    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR = (n) => Number(n).toFixed(2);

    // Initial setup
    function setup() {{
        let cats = new Set();
        let maxP = 0;
        RAW_DATA.forEach(d => {{
            if(d.crawl_category && d.crawl_category !== 'Không rõ') cats.add(d.crawl_category);
            if(d.current_price > maxP) maxP = d.current_price;
        }});
        
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option');
            opt.value = c; opt.innerText = c;
            sel.appendChild(opt);
        }});
        
        let roundedMax = Math.ceil(maxP);
        if(roundedMax <= 0) roundedMax = 1000;
        
        document.getElementById('price_min').max = roundedMax;
        document.getElementById('price_max').max = roundedMax;
        document.getElementById('price_max').value = roundedMax;
        
        updateSliderUI(null);

        initCharts();
        applyFilters();
    }}

    const MIN_GAP = 1;
    function updateSliderUI(activeElem) {{
        let minE = document.getElementById('price_min');
        let maxE = document.getElementById('price_max');
        let track = document.getElementById('price_track');
        let minV = Number(minE.value);
        let maxV = Number(maxE.value);
        
        if (minV > maxV - MIN_GAP) {{
            if (activeElem && activeElem.id === 'price_min') {{ minE.value = maxV - MIN_GAP; minV = maxV - MIN_GAP; }}
            else {{ maxE.value = minV + MIN_GAP; maxV = minV + MIN_GAP; }}
        }}
        
        let maxLimit = Number(minE.max) || 3400;
        let pMin = (minV / maxLimit) * 100;
        let pMax = (maxV / maxLimit) * 100;
        
        track.style.background = 'linear-gradient(to right, #E5E7EB ' + pMin + '%, #F97316 ' + pMin + '%, #F97316 ' + pMax + '%, #E5E7EB ' + pMax + '%)';
        document.getElementById('val_min').textContent = '$' + Number(minV).toLocaleString('en-US');
        document.getElementById('val_max').textContent = '$' + Number(maxV).toLocaleString('en-US');
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let pMin = Number(document.getElementById('price_min').value);
        let pMax = Number(document.getElementById('price_max').value);
        let chkAmz = document.getElementById('chkChoice').checked;
        let chkCli = document.getElementById('chkClimate').checked;

        let filtered = RAW_DATA.filter(d => {{
            if(cat !== 'ALL' && d.crawl_category !== cat) return false;
            if(d.current_price < pMin || d.current_price > pMax) return false;
            if(chkAmz && d.is_amazon_choice !== true) return false;
            if(chkCli && d.is_climate_friendly !== true) return false;
            return true;
        }});

        updateKPIs(filtered);
        updateData(filtered);
    }}

    function updateKPIs(data) {{
        let tProd = data.length;
        let unqCat = new Set(data.map(d => d.crawl_category)).size;
        
        let prices = data.map(d => d.current_price).filter(p => !isNaN(p) && p > 0);
        prices.sort((a,b)=>a-b);
        let sP = prices.reduce((a,b)=>a+b, 0);
        let aP = prices.length ? sP/prices.length : 0;
        let mP = prices.length ? (prices.length%2===0 ? (prices[prices.length/2-1]+prices[prices.length/2])/2 : prices[Math.floor(prices.length/2)]) : 0;

        let rt = data.map(d=>d.rating).filter(p => !isNaN(p) && p > 0);
        let aR = rt.length ? rt.reduce((a,b)=>a+b,0)/rt.length : 0;
        let sRev = data.reduce((a,b)=>a+(b.reviews||0), 0);

        let amzCount = data.filter(d => d.is_amazon_choice).length;
        let amzPct = tProd ? (amzCount / tProd * 100) : 0;

        let sVol = data.reduce((a,b)=>a+(b.sales_volume_num||0), 0);
        let aVs = data.length ? sVol / data.length : 0;

        document.getElementById('kpi_t_prod').innerText = fmtN(tProd);
        document.getElementById('kpi_sub_prod').innerText = "thuộc " + fmtN(unqCat) + " danh mục";

        document.getElementById('kpi_avg_price').innerText = "$" + fmtR(aP);
        document.getElementById('kpi_sub_price').innerText = "median: $" + fmtR(mP);

        document.getElementById('kpi_avg_rating').innerText = fmtR(aR) + "★";
        document.getElementById('kpi_sub_rating').innerText = "từ " + fmtN(sRev) + " lượt review";

        document.getElementById('kpi_choice').innerText = fmtN(amzCount);
        document.getElementById('kpi_sub_choice').innerText = "chiếm " + fmtR(amzPct) + "% tổng SP";

        document.getElementById('kpi_sales').innerText = fmtN(aVs);
        document.getElementById('kpi_sub_sales').innerText = "tổng: " + fmtN(sVol) + " lượt/tháng";
    }}

    function updateData(data) {{
        // 1. Chart Horizontal Top 10
        let catCount = {{}};
        data.forEach(d => {{ 
            if(d.crawl_category && d.crawl_category !== 'Không rõ') {{
                catCount[d.crawl_category] = (catCount[d.crawl_category]||0) + 1; 
            }}
        }});
        let arr = Object.keys(catCount).map(k => ({{c: k, count: catCount[k]}})).sort((a,b)=>b.count-a.count).slice(0,10);
        // reverse to make highest at top in horizontal chart
        arr.reverse(); 

        globalInstances.cBarTop.data.labels = arr.map(x => x.c);
        globalInstances.cBarTop.data.datasets[0].data = arr.map(x => x.count);
        globalInstances.cBarTop.update();

        // 2. Chart Donut
        let numAmz = data.filter(d => d.is_amazon_choice === true).length;
        let numCli = data.filter(d => d.is_climate_friendly === true).length;
        let numVar = data.filter(d => d.has_variations === true).length;
        globalInstances.cDonut.data.datasets[0].data = [numAmz, numCli, numVar];
        globalInstances.cDonut.update();
        document.getElementById('lg_choice').innerText = fmtN(numAmz);
        document.getElementById('lg_climate').innerText = fmtN(numCli);
        document.getElementById('lg_vars').innerText = fmtN(numVar);

        // 3. Chart Combo
        let catAgg = {{}};
        let topCatsList = arr.map(x=>x.c).reverse().slice(0,8);
        topCatsList.forEach(c => {{ catAgg[c] = {{ sumP:0, countP:0, sumS:0 }}; }});
        
        data.forEach(d => {{
            let c = d.crawl_category;
            if(catAgg[c]) {{
                if(d.current_price > 0) {{ catAgg[c].sumP += d.current_price; catAgg[c].countP++; }}
                if(d.sales_volume_num > 0) {{ catAgg[c].sumS += d.sales_volume_num; }}
            }}
        }});
        
        let cLabels = topCatsList;
        let cPrices = cLabels.map(c => catAgg[c].countP ? (catAgg[c].sumP / catAgg[c].countP) : 0);
        // Average sales requires tracking count of generic products too, estimating via known.
        let catsArrFull = data.filter(d=>cLabels.includes(d.crawl_category));
        let salesMapCount = {{}};
        catsArrFull.forEach(d => salesMapCount[d.crawl_category] = (salesMapCount[d.crawl_category]||0)+1);
        let cSales = cLabels.map(c => salesMapCount[c] ? (catAgg[c].sumS / salesMapCount[c]) : 0);

        globalInstances.cCombo.data.labels = cLabels.map(c => c.length > 25 ? c.substring(0, 25) + '...' : c);
        globalInstances.cCombo.data.datasets[0].data = cPrices;
        globalInstances.cCombo.data.datasets[1].data = cSales;
        globalInstances.cCombo.update();

        // 4. HTML Table Top 5
        let sorted = [...data].sort((a,b) => (b.sales_volume_num||0) - (a.sales_volume_num||0)).slice(0,5);
        let tb = document.getElementById('tbTop5');
        tb.innerHTML = "";
        sorted.forEach(s => {{
            let title = s.title || "";
            if(title.length > 55) title = title.substring(0, 55) + "...";
            let tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="truncate-col" title="${{s.title}}">${{title}}</td>
                <td>${{s.crawl_category}}</td>
                <td>${{s.current_price > 0 ? ('$'+fmtR(s.current_price)) : '—'}}</td>
                <td>★ ${{fmtR(s.rating)}}</td>
                <td>${{fmtN(s.sales_volume_num || 0)}}</td>
            `;
            tb.appendChild(tr);
        }});
    }}

    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';

        // Bar Top 10
        let ctxBar = document.getElementById('cBarTop').getContext('2d');
        globalInstances.cBarTop = new Chart(ctxBar, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'Số lượng SP',
                    data: [],
                    backgroundColor: '#F97316',
                    borderRadius: 4
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
                }}
            }}
        }});

        // Donut
        let ctxDonut = document.getElementById('cDonut').getContext('2d');
        globalInstances.cDonut = new Chart(ctxDonut, {{
            type: 'doughnut',
            data: {{
                labels: ["Amazon's Choice", "Climate Friendly", "Has Variations"],
                datasets: [{{
                    data: [0,0,0],
                    backgroundColor: ['#FED7AA', '#F97316', '#9A3412'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ callbacks: {{ label: (c) => " " + c.label + ": " + fmtN(c.raw) }} }}
                }}
            }}
        }});

        // Combo
        let ctxCombo = document.getElementById('cCombo').getContext('2d');
        globalInstances.cCombo = new Chart(ctxCombo, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{
                        type: 'bar',
                        label: 'Giá TB ($)',
                        data: [],
                        backgroundColor: '#F97316',
                        yAxisID: 'yLeft',
                        borderRadius: 3
                    }},
                    {{
                        type: 'line',
                        label: 'Doanh số TB (lượt)',
                        data: [],
                        borderColor: '#1C1917',
                        borderWidth: 2,
                        pointRadius: 5,
                        tension: 0.3,
                        yAxisID: 'yRight'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{ padding: {{ right: 5 }} }},
                plugins: {{ legend: {{ display: false }}, tooltip: {{ mode: 'index', intersect: false }} }},
                scales: {{
                    yLeft: {{ type: 'linear', position: 'left', title: {{ display: false }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                    yRight: {{ type: 'linear', position: 'right', title: {{ display: false }}, grid: {{ drawOnChartArea: false }}, ticks: {{ callback: function(val) {{ return fmtN(val); }} }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }}, maxRotation: 20 }} }}
                }}
            }}
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
    </script>
</body>
</html>
    """
    
    components.html(html_code, height=1600, scrolling=False)
