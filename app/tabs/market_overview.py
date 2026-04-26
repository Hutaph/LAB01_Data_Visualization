"""
Tab Tổng quan — Overview dashboard rebuilt dynamically with robust Custom HTML/CSS/JS stack using Chart.js.
Updated to be 100% charts as requested (removed table).
"""

import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def render(state):
    df_raw = state["df"]
    df = df_raw.copy()
    
    # Preprocessing
    required_bools = ["is_amazon_choice", "is_climate_friendly", "has_variations"]
    for b in required_bools:
        if b not in df.columns:
            df[b] = False
        else:
            df[b] = df[b].fillna(False).astype(bool)

    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"
    df["crawl_category"] = df["crawl_category"].fillna("Không rõ")

    # Categories logic (matching tab_thong_tin)
    from utils.constants import CATEGORY_MAP
    df["category"] = df["crawl_category"].map(CATEGORY_MAP).fillna(df["crawl_category"])

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

    select_cols = [
        "category", "current_price", "rating", "reviews", 
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --pr: #F97316;
            --dk: #9A3412;
            --bg: #FEF3E2;
            --card: #FFFFFF;
            --t1: #1C1917;
            --t2: #78716C;
            --t3: #A8A29E;
            --bd: #E7E5E4;
            --r: 8px;
            --fn: 'Inter', sans-serif;
            --ft: 'Montserrat', sans-serif;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            background-color: var(--bg);
            font-family: var(--fn);
            color: var(--t1);
            padding: 6px 14px 8px;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        /* ── FILTER BAR ── */
        .fb {{
            display: flex; align-items: center; gap: 20px;
            background: #fff; border: 1px solid var(--bd); border-radius: 12px;
            padding: 12px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.06); flex-shrink: 0;
        }}
        .fb-item {{ display: flex; flex-direction: column; gap: 5px; }}
        .fb-item label {{
            font-size: 11px; font-weight: 700; color: var(--t2);
            text-transform: uppercase; letter-spacing: .8px;
        }}
        .fb-item select {{
            padding: 8px 12px;
            border: 1px solid var(--bd); border-radius: 8px;
            font-size: 13px; font-family: var(--fn); color: var(--t1);
            background: #fafaf9 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716C' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat right 10px center;
            appearance: none; cursor: pointer; outline: none; transition: border-color .15s;
            min-width: 190px;
        }}
        .fb-item select:hover {{ border-color: var(--pr); }}
        .fb-item select:focus {{ border-color: var(--pr); box-shadow: 0 0 0 3px rgba(249,115,22,.12); }}

        .toggle-group {{ display: flex; background: #F3F4F6; border-radius: 8px; padding: 3px; gap: 2px; }}
        .toggle-btn {{
            border: none; background: transparent; font-family: inherit; font-size: 12px;
            font-weight: 600; color: var(--t2); padding: 6px 14px; border-radius: 6px;
            cursor: pointer; transition: all 0.2s;
        }}
        .toggle-btn.active {{
            background: #FFFFFF; color: var(--pr); box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}

        /* ── KPI ── */
        .kpi-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; flex-shrink: 0; }}
        .kc {{ background: var(--card); border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); padding: 12px 16px; border-left: 4px solid var(--pr); }}
        .kc.hi {{ border-left-color: var(--dk); background: #FFF7ED; }}
        .kt {{ font-size: 10px; font-weight: 700; color: var(--t2); text-transform: uppercase; letter-spacing: .6px; margin-bottom: 6px; }}
        .kv {{ font-family: var(--ft); font-size: 22px; font-weight: 700; color: var(--t1); margin-bottom: 2px; }}
        .ks {{ font-size: 11px; color: var(--t3); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .kc.hi .kv {{ color: var(--dk); }}

        /* ── CHARTS ── */
        .g2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; flex: 1; min-height: 0; }}
        .cc {{ background: var(--card); border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,.04); padding: 16px; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }}
        .ct {{ font-size: 14px; font-weight: 700; color: var(--t1); margin-bottom: 4px; }}
        .cs {{ font-size: 11px; color: var(--t2); margin-bottom: 12px; line-height: 1.4; }}
        .cw {{ position: relative; flex: 1; min-height: 0; }}
        
        .leg {{ display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 12px; justify-content: center; }}
        .li {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--t2); font-weight: 600; }}
        .ld {{ width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }}
    </style>
</head>
<body>

    <!-- FILTER BAR -->
    <div class="fb">
        <div class="fb-item">
            <label>Danh Mục Sản Phẩm</label>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả danh mục sản phẩm</option>
            </select>
        </div>
        <div class="fb-item">
            <label>Bộ Lọc Đặc Biệt</label>
            <select id="selSpecial" onchange="applyFilters()">
                <option value="ALL">Tất cả sản phẩm</option>
                <option value="choice">Amazon's Choice</option>
                <option value="climate">Climate Friendly</option>
                <option value="variations">Có biến thể (Variations)</option>
            </select>
        </div>
        <div class="fb-item">
            <label>Chỉ Số Doanh Số</label>
            <div class="toggle-group">
                <button class="toggle-btn active" id="btn_mean" onclick="setMetric('mean')">Mean</button>
                <button class="toggle-btn" id="btn_median" onclick="setMetric('median')">Median</button>
            </div>
        </div>
        <div style="margin-left:auto; display:flex; flex-direction:column; align-items:flex-end; justify-content:center;">
            <div style="font-size:16px; font-weight:800; color:var(--dk); font-family:var(--ft);">TỔNG QUAN THỊ TRƯỜNG</div>
            <div style="font-size:11px; color:var(--t2); font-weight:500;">Báo cáo tổng hợp hiệu quả kinh doanh đa danh mục</div>
        </div>
    </div>

    <!-- KPI ROW -->
    <div class="kpi-row" id="kpiRow"></div>

    <!-- CHARTS GRID -->
    <div class="g2">
        <div class="cc">
            <div class="ct">Quy mô các danh mục dẫn đầu</div>
            <div class="cs">Top 10 danh mục có số lượng sản phẩm niêm yết lớn nhất</div>
            <div class="cw"><canvas id="cBarTop"></canvas></div>
        </div>
        <div class="cc">
            <div class="ct">Phân bổ đặc điểm sản phẩm</div>
            <div class="cs">Tỷ lệ sản phẩm đạt các chứng chỉ hoặc có đặc tính bổ trợ</div>
            <div class="leg" id="dLeg"></div>
            <div class="cw"><canvas id="cDonut"></canvas></div>
        </div>
        <div class="cc">
            <div class="ct" id="titleCombo">Giá trị & Hiệu suất theo danh mục</div>
            <div class="cs">Tương quan giữa mức giá và doanh số bán hàng</div>
            <div class="cw"><canvas id="cCombo"></canvas></div>
        </div>
        <div class="cc">
            <div class="ct">Phân bổ điểm đánh giá</div>
            <div class="cs">Tỉ lệ số lượng sản phẩm theo các mức điểm đánh giá (Rating)</div>
            <div class="cw"><canvas id="cRating"></canvas></div>
        </div>
    </div>

<script>
    const RAW_DATA = {data_json_str};
    let CHARTS = {{}};
    let METRIC = 'mean';

    const fmtN = (n) => new Intl.NumberFormat('vi-VN').format(Math.round(n));
    const fmtC = (n) => '$' + Number(n).toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
    const avg = a => a.length ? a.reduce((x,y)=>x+y,0)/a.length : 0;
    const median = a => {{ if(!a.length) return 0; const s=[...a].sort((x,y)=>x-y),m=Math.floor(s.length/2); return s.length%2?s[m]:(s[m-1]+s[m])/2; }};

    function setMetric(m) {{
        METRIC = m;
        document.getElementById('btn_mean').classList.toggle('active', m === 'mean');
        document.getElementById('btn_median').classList.toggle('active', m === 'median');
        document.getElementById('titleCombo').innerText = m === 'mean' ? 'Giá trị & Hiệu suất trung bình' : 'Giá trị & Hiệu suất trung vị';
        applyFilters();
    }}

    function setup() {{
        let cats = new Set();
        RAW_DATA.forEach(d => {{ if(d.category && d.category !== 'Không rõ') cats.add(d.category); }});
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option'); opt.value = c; opt.innerText = c; sel.appendChild(opt);
        }});

        initCharts();
        applyFilters();
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let spec = document.getElementById('selSpecial').value;

        let filtered = RAW_DATA.filter(d => {{
            if(cat !== 'ALL' && d.category !== cat) return false;
            if(spec === 'choice' && !d.is_amazon_choice) return false;
            if(spec === 'climate' && !d.is_climate_friendly) return false;
            if(spec === 'variations' && !d.has_variations) return false;
            return true;
        }});

        updateDashboard(filtered);
    }}

    function updateDashboard(data) {{
        // KPI Calculations
        const t = data.length;
        const totalSales = data.reduce((s, d) => s + d.sales_volume_num, 0);
        const avgSales = t ? (METRIC === 'mean' ? totalSales / t : median(data.map(d=>d.sales_volume_num))) : 0;
        const avgPrice = t ? (METRIC === 'mean' ? data.reduce((s, d) => s + d.current_price, 0) / t : median(data.map(d=>d.current_price))) : 0;
        const avgRating = t ? data.reduce((s, d) => s + d.rating, 0) / t : 0;
        const choiceCount = data.filter(d => d.is_amazon_choice).length;
        
        const kpis = [
            {{ t: 'Tổng sản phẩm', v: fmtN(t), s: 'Sản phẩm trong bộ lọc' }},
            {{ t: 'Giá ' + (METRIC === 'mean' ? 'TB' : 'Trung vị'), v: fmtC(avgPrice), s: 'Giá niêm yết hiện tại', hi: 1 }},
            {{ t: 'Doanh số ' + (METRIC === 'mean' ? 'TB' : 'Trung vị'), v: fmtN(avgSales), s: 'Lượt bán / tháng' }},
            {{ t: 'Đánh giá trung bình', v: avgRating.toFixed(1) + ' ★', s: 'Trên thang điểm 5.0' }},
            {{ t: "Amazon's Choice", v: fmtN(choiceCount), s: 'Chiếm ' + (t ? (choiceCount/t*100).toFixed(1) : 0) + '% tổng số', hi: 1 }}
        ];
        
        document.getElementById('kpiRow').innerHTML = kpis.map(x => `
            <div class="kc ${{x.hi ? 'hi' : ''}}">
                <div class="kt">${{x.t}}</div>
                <div class="kv">${{x.v}}</div>
                <div class="ks">${{x.s}}</div>
            </div>
        `).join('');

        // 1. Chart Bar Top Categories
        let catCount = {{}};
        data.forEach(d => {{ catCount[d.category] = (catCount[d.category] || 0) + 1; }});
        let topCats = Object.keys(catCount).map(k => ({{ k, v: catCount[k] }})).sort((a,b) => b.v - a.v).slice(0, 10);
        
        CHARTS.bar.data.labels = topCats.map(x => x.k.length > 20 ? x.k.slice(0, 20) + '...' : x.k);
        CHARTS.bar.data.datasets[0].data = topCats.map(x => x.v);
        CHARTS.bar.update();

        // 2. Chart Donut
        let numAmz = data.filter(d => d.is_amazon_choice).length;
        let numCli = data.filter(d => d.is_climate_friendly).length;
        let numVar = data.filter(d => d.has_variations).length;
        let donutData = [numAmz, numCli, numVar];
        
        CHARTS.donut.data.datasets[0].data = donutData;
        CHARTS.donut.update();
        
        const dLabels = ["Amazon's Choice", "Climate Friendly", "Variations"];
        const dColors = ['#FED7AA', '#F97316', '#9A3412'];
        document.getElementById('dLeg').innerHTML = dLabels.map((l, i) => `
            <span class="li"><span class="ld" style="background:${{dColors[i]}}"></span>${{l}} (${{fmtN(donutData[i])}})</span>
        `).join('');

        // 3. Chart Combo
        let top8Cats = topCats.slice(0, 8).map(x => x.k);
        let comboData = top8Cats.map(c => {{
            let sub = data.filter(d => d.category === c);
            let pArr = sub.map(d => d.current_price);
            let sArr = sub.map(d => d.sales_volume_num);
            return {{
                p: METRIC === 'mean' ? avg(pArr) : median(pArr),
                s: METRIC === 'mean' ? avg(sArr) : median(sArr)
            }};
        }});

        CHARTS.combo.data.labels = top8Cats.map(x => x.length > 15 ? x.slice(0, 15) + '...' : x);
        CHARTS.combo.data.datasets[0].data = comboData.map(x => x.p);
        CHARTS.combo.data.datasets[1].data = comboData.map(x => x.s);
        CHARTS.combo.update();

        // 4. Chart Rating Distribution
        let rBins = [0,0,0,0,0]; // 0-1, 1-2, 2-3, 3-4, 4-5
        data.forEach(d => {{
            let r = d.rating;
            if(r > 0 && r <= 1) rBins[0]++;
            else if(r <= 2) rBins[1]++;
            else if(r <= 3) rBins[2]++;
            else if(r <= 4) rBins[3]++;
            else if(r <= 5) rBins[4]++;
        }});
        CHARTS.rating.data.datasets[0].data = rBins;
        CHARTS.rating.update();
    }}

    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';

        CHARTS.bar = new Chart(document.getElementById('cBarTop'), {{
            type: 'bar',
            data: {{ labels: [], datasets: [{{ label: 'Số lượng SP', data: [], backgroundColor: '#F97316', borderRadius: 4 }}] }},
            options: {{
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ x: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.04)' }} }}, y: {{ grid: {{ display: false }} }} }}
            }}
        }});

        CHARTS.donut = new Chart(document.getElementById('cDonut'), {{
            type: 'doughnut',
            data: {{ labels: ["Choice", "Climate", "Variations"], datasets: [{{ data: [], backgroundColor: ['#FED7AA', '#F97316', '#9A3412'], borderWidth: 0 }}] }},
            options: {{
                responsive: true, maintainAspectRatio: false, cutout: '70%',
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        CHARTS.combo = new Chart(document.getElementById('cCombo'), {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: 'Giá', type: 'bar', data: [], backgroundColor: '#F9731660', yAxisID: 'y', borderRadius: 2 }},
                    {{ label: 'Doanh số', type: 'line', data: [], borderColor: '#9A3412', borderWidth: 2, pointRadius: 3, tension: 0.3, yAxisID: 'y1' }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ position: 'left', grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ callback: v => '$' + v }} }},
                    y1: {{ position: 'right', grid: {{ display: false }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});

        CHARTS.rating = new Chart(document.getElementById('cRating'), {{
            type: 'bar',
            data: {{
                labels: ['1★', '2★', '3★', '4★', '5★'],
                datasets: [{{ label: 'Số lượng SP', data: [], backgroundColor: '#9A3412', borderRadius: 4 }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.04)' }} }}, x: {{ grid: {{ display: false }} }} }}
            }}
        }});
    }}

    setup();
</script>
</body>
</html>
    """
    
    st.markdown("<style>.block-container{padding-top:.4rem!important;}</style>", unsafe_allow_html=True)
    components.html(html_code, height=650, scrolling=False)
