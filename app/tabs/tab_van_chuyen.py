import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import re

def render(df_raw):
    df = df_raw.copy()

    # Preprocessing
    df["is_prime"] = df.get("is_prime", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    df["is_amazon_choice"] = df.get("is_amazon_choice", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    df["delivery_fee"] = pd.to_numeric(df.get("delivery_fee", 0.0), errors="coerce").fillna(0.0).clip(lower=0)
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0).astype(int)
    df["current_price"] = pd.to_numeric(df.get("price", 0.0), errors="coerce").fillna(0.0).clip(lower=0)
    df["rating_val"] = pd.to_numeric(df.get("rating", 0.0), errors="coerce").fillna(0.0)

    from utils.constants import CATEGORY_MAP
    
    if "crawl_category" in df.columns:
        df["Danh Mục Sản Phẩm"] = df["crawl_category"].map(CATEGORY_MAP).fillna(df["crawl_category"])
    else:
        df["Danh Mục Sản Phẩm"] = "Không Rõ"

    def parse_est_days_row(row):
        text = row.get("delivery_date_text")
        date_str = "2026-03-24"
        if "date" in row and not pd.isna(row["date"]):
            date_str = row["date"]
            
        if pd.isna(text): return None
        s = str(text).lower()
        
        try:
            base_date = pd.to_datetime(date_str)
        except:
            return None
            
        months = {'jan': 1, 'feb': 2, 'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        month_pattern = r'(jan|feb|mar|march|apr|april|may|jun|jul|aug|sep|oct|nov|dec)'
        
        m_range = re.search(month_pattern + r'\s+(\d+)\s*-\s*(\d+)', s)
        if m_range:
            m_val = months[m_range.group(1)]
            d1 = int(m_range.group(2))
            d2 = int(m_range.group(3))
            try:
                target_date1 = pd.to_datetime(f"{base_date.year}-{m_val}-{d1}")
                target_date2 = pd.to_datetime(f"{base_date.year}-{m_val}-{d2}")
                days1 = (target_date1 - base_date).days
                days2 = (target_date2 - base_date).days
                if days1 < 0: days1 += 365
                if days2 < 0: days2 += 365
                return max(1, round((days1 + days2) / 2.0))
            except:
                pass
                
        m_single = re.search(month_pattern + r'\s+(\d+)', s)
        if m_single:
            m_val = months[m_single.group(1)]
            d1 = int(m_single.group(2))
            try:
                target_date = pd.to_datetime(f"{base_date.year}-{m_val}-{d1}")
                days = (target_date - base_date).days
                if days < 0: days += 365
                return max(1, days)
            except:
                pass
                
        return None

    if "delivery_date_text" in df.columns:
        df["est_delivery_days"] = df.apply(parse_est_days_row, axis=1)
    else:
        df["est_delivery_days"] = None

    select_cols = [
        "Danh Mục Sản Phẩm", "delivery_fee", "sales_volume_num", "current_price", 
        "rating_val", "is_prime", "est_delivery_days", "is_amazon_choice"
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
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        :root {{
            --primary: #F97316;
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 6px;
            --font-family: 'Inter', sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            font-family: var(--font-family);
            color: var(--text-primary);
            padding: 5px;
            overflow: hidden;
        }}
        .filter-bar {{
            display: flex; align-items: center; gap: 15px; margin-bottom: 5px;
            background: var(--card-bg); padding: 4px 10px; border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        }}
        .f-item {{ display: flex; align-items: center; gap: 8px; }}
        .f-label {{ font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; }}
        select {{
            padding: 2px 6px; border: 1px solid #D1D5DB; border-radius: 4px; height: 26px;
            font-family: inherit; font-size: 11px; color: var(--text-primary); outline: none; cursor: pointer; width: 180px; font-weight: 500;
        }}
        select:focus {{ border-color: var(--primary); }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }}
        .col-wrapper {{ display: flex; flex-direction: column; gap: 6px; }}
        .header-title-box {{
            background: var(--card-bg);
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            padding: 4px;
            text-align: center;
            border-bottom: 2px solid var(--primary);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        .col-title {{ font-size: 11px; font-weight: 700; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }}
        .chart-card {{
            background: var(--card-bg);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); padding: 6px 8px;
            border-radius: 0 0 var(--border-radius) var(--border-radius);
            display: flex; flex-direction: column;
        }}
        .chart-title {{ font-size: 11px; font-weight: 600; text-align: center; margin-bottom: 4px; color: var(--text-secondary); }}
        .chart-wrapper {{ position: relative; width: 100%; height: 220px; }}
    </style>
</head>
<body>

    <!-- Filter -->
    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Danh mục Sản Phẩm:</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả danh mục</option>
            </select>
        </div>
    </div>

    <!-- Layout -->
    <div class="main-grid">
        <!-- COL 1 -->
        <div class="col-wrapper">
            <div class="header-title-box"><div class="col-title">Định Giá & Phí Vận Chuyển</div></div>
            <div class="chart-card" style="border-radius: 0">
                <div class="chart-title">Tác Động Của Tỷ Trọng Phí Vận Chuyển Lên Sức Bán (Phí / Giá)</div>
                <div class="chart-wrapper" style="height: 486px;"><canvas id="c1_ratio"></canvas></div>
            </div>
            <div class="chart-card" style="background:#f8fafc; border: 1px solid #e2e8f0;">
                <div class="chart-title">Định Giá Phí Trong Top 10% Doanh Số</div>
                <div class="chart-wrapper"><canvas id="c1_top10"></canvas></div>
            </div>
        </div>
        
        <!-- COL 2 -->
        <div class="col-wrapper">
            <div class="header-title-box"><div class="col-title">Top Ưa Chuộng (Sellers) & Prime</div></div>
            <div class="chart-card" style="border-radius: 0">
                <div class="chart-title">Thị Phần Doanh Số Nhãn Prime (Nhóm Top 20%)</div>
                <div class="chart-wrapper"><canvas id="c2_donut"></canvas></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Mức Giá Của Mặt Hàng Có Prime và Không Prime</div>
                <div class="chart-wrapper"><canvas id="c2_bar"></canvas></div>
            </div>
            <div class="chart-card" style="background:#f8fafc; border: 1px solid #e2e8f0;">
                <div class="chart-title">Tỷ Lệ Prime Trong Top 10% Doanh Số</div>
                <div class="chart-wrapper"><canvas id="c2_top10"></canvas></div>
            </div>
        </div>

        <!-- COL 3 -->
        <div class="col-wrapper">
            <div class="header-title-box"><div class="col-title">Tốc Độ Giao & Doanh Số</div></div>
            <div class="chart-card" style="border-radius: 0">
                <div class="chart-title">Tỷ Lệ Doanh Số Trung Bình</div>
                <div class="chart-wrapper"><canvas id="c3_combo"></canvas></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Phân Bổ Ngày Giao Của Top 20 Sản Phẩm Bán Chạy Nhất</div>
                <div class="chart-wrapper"><canvas id="c3_donut"></canvas></div>
            </div>
            <div class="chart-card" style="background:#f8fafc; border: 1px solid #e2e8f0;">
                <div class="chart-title">Tốc Độ Giao Hàng Trong Top 10% Doanh Số</div>
                <div class="chart-wrapper"><canvas id="c3_top10"></canvas></div>
            </div>
        </div>

    </div>

<script>
    const RAW_DATA = {data_json_str};
    let GI = {{}};
    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR = (n) => typeof n === 'number' ? Number(n).toFixed(2) : n;

    function setup() {{
        Chart.register(ChartDataLabels);
        Chart.defaults.plugins.datalabels = {{ display: false }};
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.size = 10;
        
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
        updateData(data);
    }}

    function updateData(data) {{
        let ratioList = ['0%', '1 - 50%', '51 - 100%', '> 100%'];
        let rAgg = {{}};
        ratioList.forEach(k => {{ rAgg[k] = {{s:0,c:0}}; }});

        data.forEach(d => {{
            if (d.current_price > 0) {{
                let ratio = (d.delivery_fee / d.current_price) * 100;
                let rK = '> 100%';
                if (ratio === 0) rK = '0%';
                else if (ratio <= 50) rK = '1 - 50%';
                else if (ratio <= 100) rK = '51 - 100%';
                
                rAgg[rK].s += (d.sales_volume_num || 0);
                rAgg[rK].c++;
            }}
        }});

        window.rAggData = rAgg;
        GI.c1_ratio.data.labels = ratioList;
        GI.c1_ratio.data.datasets[0].data = ratioList.map(k => rAgg[k].c > 0 ? rAgg[k].s / rAgg[k].c : 0);
        GI.c1_ratio.update();

        let sortedS = [...data].sort((a,b)=>(b.sales_volume_num||0) - (a.sales_volume_num||0));
        let top20count = Math.max(1, Math.floor(data.length*0.2));
        let top20 = sortedS.slice(0, top20count);
        let pSales = 0, npSales = 0;
        top20.forEach(d => {{
            if(d.is_prime) pSales += (d.sales_volume_num||0);
            else npSales += (d.sales_volume_num||0);
        }});
        
        GI.c2_donut.data.datasets[0].data = [pSales, npSales];
        GI.c2_donut.update();

        let pPriceSum = 0, pPriceC = 0;
        let npPriceSum = 0, npPriceC = 0;
        data.forEach(d => {{
            if(d.is_prime) {{ pPriceSum += d.current_price; pPriceC++; }}
            else {{ npPriceSum += d.current_price; npPriceC++; }}
        }});
        GI.c2_bar.data.datasets[0].data = [pPriceC>0 ? pPriceSum/pPriceC : 0, npPriceC>0 ? npPriceSum/npPriceC : 0];
        GI.c2_bar.update();

        let c_fast=0, c_slow=0, s_fast=0, s_slow=0;
        data.forEach(d=> {{
            if(d.est_delivery_days != null && !isNaN(d.est_delivery_days)) {{
                if(d.est_delivery_days <= 20) {{ c_fast++; s_fast += (d.sales_volume_num||0); }}
                else {{ c_slow++; s_slow += (d.sales_volume_num||0); }}
            }}
        }});
        
        GI.c3_combo.data.labels = [`≤ 20 ngày (${{fmtN(c_fast)}} sp)`, `> 20 ngày (${{fmtN(c_slow)}} sp)`];
        GI.c3_combo.data.datasets[0].data = [c_fast>0?s_fast/c_fast:0, c_slow>0?s_slow/c_slow:0];
        GI.c3_combo.update();

        let validItems = data.filter(d=>d.est_delivery_days != null && !isNaN(d.est_delivery_days));
        validItems.sort((a,b) => (b.sales_volume_num||0) - (a.sales_volume_num||0));
        let top20Items = validItems.slice(0, 20);
        let top20Agg = {{}};
        top20Items.forEach(d => {{
            let k = d.est_delivery_days + ' ngày';
            top20Agg[k] = (top20Agg[k]||0) + 1;
        }});
        
        let t20Labels = Object.keys(top20Agg).sort((a,b)=> parseInt(a)-parseInt(b));
        let t20Data = t20Labels.map(k=>top20Agg[k]);
        
        GI.c3_donut.data.labels = t20Labels;
        GI.c3_donut.data.datasets[0].data = t20Data;
        GI.c3_donut.data.datasets[0].backgroundColor = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        GI.c3_donut.update();

        // TOP 10% Sales Data Insights
        let top10count = Math.max(1, Math.floor(validItems.length * 0.1));
        let top10Data = validItems.slice(0, top10count);
        
        let c1_r0=0, c1_r50=0, c1_r100=0, c1_ro=0;
        let c2_p=0, c2_np=0;
        let c3_fast=0, c3_slow=0;

        top10Data.forEach(d => {{
            if (d.current_price > 0) {{
                let ratio = (d.delivery_fee / d.current_price) * 100;
                if (ratio === 0) c1_r0++;
                else if (ratio <= 50) c1_r50++;
                else if (ratio <= 100) c1_r100++;
                else c1_ro++;
            }} else if (d.delivery_fee === 0) {{
                c1_r0++;
            }} else {{
                c1_ro++;
            }}

            if(d.is_prime) c2_p++; else c2_np++;
            if(d.est_delivery_days != null && !isNaN(d.est_delivery_days)) {{
                if(d.est_delivery_days <= 20) c3_fast++; else c3_slow++;
            }}
        }});

        GI.c1_top10.data.labels = ['0%', '1 - 50%', '51 - 100%', '> 100%'];
        GI.c1_top10.data.datasets[0].data = [c1_r0, c1_r50, c1_r100, c1_ro];
        GI.c1_top10.update();

        GI.c2_top10.data.labels = ['Gắn Prime', 'Không Prime'];
        GI.c2_top10.data.datasets[0].data = [c2_p, c2_np];
        GI.c2_top10.update();

        GI.c3_top10.data.labels = ['≤ 20 ngày', '> 20 ngày'];
        GI.c3_top10.data.datasets[0].data = [c3_fast, c3_slow];
        GI.c3_top10.update();

    }}

    function initCharts() {{
        const legOpts = {{ position:'bottom', labels:{{boxWidth:10, padding:5, font:{{size:9}}}} }};
        const baseOpts = {{ responsive:true, maintainAspectRatio:false, layout:{{padding:0}}, animation: {{ duration: 1000 }} }};

        GI.c1_ratio = new Chart(document.getElementById('c1_ratio').getContext('2d'), {{
            type:'bar', data: {{ labels:[], datasets:[{{label:'Doanh Số Trung Bình', data:[], backgroundColor:'#f97316', borderRadius:4}}] }}, 
            options: {{ ...baseOpts, plugins:{{
                legend:{{display:false}}, 
                datalabels: {{
                    display: true, align: 'end', anchor: 'end', color: '#f97316', font: {{weight: 'bold', size: 10}},
                    formatter: function(value) {{ return fmtN(value) + '\\nLượt bán/tháng'; }},
                    textAlign: 'center'
                }},
                tooltip:{{callbacks:{{label: function(c){{ 
                    if(!window.rAggData) return '';
                    let labelStr = c.label;
                    let count = window.rAggData[labelStr] ? window.rAggData[labelStr].c : 0;
                    return fmtN(count) + ' số sản phẩm được bán'; 
                }}}}}}
            }}, scales:{{x: {{grid: {{display:false}}, ticks:{{font:{{size:10, weight:'bold'}}}}}}, y:{{grace:'30%', grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback:function(v){{return fmtN(v);}}, font:{{size:9}}}}}}}} }}
        }});
        
        GI.c2_donut = new Chart(document.getElementById('c2_donut').getContext('2d'), {{
            type:'doughnut', data: {{ labels:['Có Prime','Không Nhãn Prime'], datasets:[{{data:[], backgroundColor:['#10b981','#cbd5e1'], borderWidth:0}}] }},
            options: {{ ...baseOpts, cutout:'60%', plugins:{{legend:legOpts, tooltip:{{callbacks:{{label: function(c){{ return c.label + ': ' + fmtN(c.raw) + ' Lượt Tương Tác/Bán'; }}}}}}}}, animation: {{ duration: 1000, animateScale: true }} }}
        }});

        GI.c2_bar = new Chart(document.getElementById('c2_bar').getContext('2d'), {{
            type:'bar', data: {{ labels:['Được gắn Prime','Chưa Gắn Prime'], datasets:[{{label:'Giá Trung Bình', data:[], backgroundColor:['#10b981','#cbd5e1'], borderRadius:4}}] }},
            options: {{ ...baseOpts, plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label: function(c){{ return 'Trung Bình: $' + fmtR(c.raw); }}}}}}}}, scales:{{x: {{grid: {{display:false}}, ticks:{{font:{{size:9}}}}}}, y:{{grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback:function(v){{return '$' + fmtN(v);}}, font:{{size:9}}}}}}}} }}
        }});

        GI.c3_combo = new Chart(document.getElementById('c3_combo').getContext('2d'), {{
            type:'bar', data: {{ labels:[], datasets:[{{type:'bar',label:'Doanh Số Trung Bình',data:[],backgroundColor:'#facc15', borderRadius:4}}] }},
            options: {{ ...baseOpts, plugins:{{legend:legOpts, tooltip:{{callbacks:{{label: function(c){{ return 'Doanh Số: ' + fmtN(c.raw) + ' Lượt Bán Mỗi Tháng'; }}}}}}}}, scales:{{x:{{grid:{{display:false}}, ticks:{{font:{{size:9}}}}}}, y:{{grid:{{color:'rgba(0,0,0,0.05)'}},ticks:{{callback:function(v){{return fmtN(v) + ' Lượt Bán';}}, font:{{size:9}}}}}} }} }}
        }});

        GI.c3_donut = new Chart(document.getElementById('c3_donut').getContext('2d'), {{
            type:'doughnut', data: {{ labels:[], datasets:[{{data:[], backgroundColor:['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'], borderWidth:0}}] }},
            options: {{ ...baseOpts, cutout:'60%', plugins:{{legend:legOpts, tooltip:{{callbacks:{{label: function(c){{ return c.label + ': ' + fmtN(c.raw) + ' Sản Phẩm'; }}}}}}}}, animation: {{ duration: 1000, animateScale: true }} }}
        }});

        GI.c1_top10 = new Chart(document.getElementById('c1_top10').getContext('2d'), {{
            type:'doughnut', data: {{ labels:[], datasets:[{{data:[], backgroundColor:['#3b82f6', '#10b981', '#f59e0b', '#ef4444'], borderWidth:0}}] }},
            options: {{ ...baseOpts, cutout:'65%', plugins:{{legend:legOpts, tooltip:{{callbacks:{{label: function(c){{ return c.label + ': ' + fmtN(c.raw) + ' SP'; }}}}}}}}, animation: {{ duration: 1000, animateScale: true }} }}
        }});

        GI.c2_top10 = new Chart(document.getElementById('c2_top10').getContext('2d'), {{
            type:'doughnut', data: {{ labels:[], datasets:[{{data:[], backgroundColor:['#10b981','#cbd5e1'], borderWidth:0}}] }},
            options: {{ ...baseOpts, cutout:'65%', plugins:{{legend:legOpts, tooltip:{{callbacks:{{label: function(c){{ return c.label + ': ' + fmtN(c.raw) + ' SP'; }}}}}}}}, animation: {{ duration: 1000, animateScale: true }} }}
        }});

        GI.c3_top10 = new Chart(document.getElementById('c3_top10').getContext('2d'), {{
            type:'doughnut', data: {{ labels:[], datasets:[{{data:[], backgroundColor:['#facc15','#cbd5e1'], borderWidth:0}}] }},
            options: {{ ...baseOpts, cutout:'65%', plugins:{{legend:legOpts, tooltip:{{callbacks:{{label: function(c){{ return c.label + ': ' + fmtN(c.raw) + ' SP'; }}}}}}}}, animation: {{ duration: 1000, animateScale: true }} }}
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
    """
    
    components.html(html_code, height=900, scrolling=False)
