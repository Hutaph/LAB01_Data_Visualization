import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import re

def render(df_raw):
    df = df_raw.copy()

    # Preprocessing
    df["is_prime"] = df.get("is_prime", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    df["delivery_fee"] = pd.to_numeric(df.get("delivery_fee", 0.0), errors="coerce").fillna(0.0).clip(lower=0)
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0).astype(int)
    df["current_price"] = pd.to_numeric(df.get("price", 0.0), errors="coerce").fillna(0.0).clip(lower=0)
    df["rating_val"] = pd.to_numeric(df.get("rating", 0.0), errors="coerce").fillna(0.0)

    # Categories
    CATEGORY_MAP = {
        "electronics_laptops": "Laptop", "electronics_tablets": "Máy Tính Bảng", "electronics_smartphones": "Điện Thoại",
        "electronics_monitors": "Màn Hình", "electronics_headphones": "Tai Nghe", "electronics_keyboards": "Bàn Phím",
        "electronics_storage_ssd": "Ổ Cứng & SSD", "electronics_networking": "Thiết Bị Mạng", "electronics_gaming_consoles": "Máy Chơi Game",
        "home_kitchen_appliances": "Thiết Bị Bếp", "home_cleaning": "Dụng Cụ Vệ Sinh", "home_air_quality": "Máy Lọc Khí",
        "home_furniture": "Nội Thất", "office_supplies": "Văn Phòng Phẩm", "office_stationery": "Dụng Cụ VP",
        "fashion_mens": "Thời Trang Nam", "fashion_womens": "Thời Trang Nữ", "fashion_shoes": "Giày Dép",
        "fashion_bags": "Túi Xách", "beauty_skincare": "Chăm Sóc Da", "beauty_makeup": "Trang Điểm",
        "health_personal_care": "Chăm Sóc Cá Nhân", "health_supplements": "TPCN & Vitamin", "baby_products": "Sản Phẩm Cho Bé",
        "toys_games": "Đồ Chơi & Game", "sports_outdoors": "Thể Thao", "sports_fitness": "Dụng Cụ Gym",
        "pet_supplies": "Thú Cưng", "automotive_accessories": "Phụ Kiện Ô Tô", "tools_home_improvement": "Dụng Cụ Sửa Nhà",
    }
    
    if "crawl_category" in df.columns:
        df["Danh Mục"] = df["crawl_category"].map(CATEGORY_MAP).fillna(df["crawl_category"])
    else:
        df["Danh Mục"] = "Không Rõ"

    def parse_est_days(text):
        if pd.isna(text): return None
        s = str(text)
        m = re.search(r'\w+,\s*Apr\s+(\d+)', s)
        if m: return max(1, int(m.group(1)) - 6)
        m2 = re.search(r'Apr\s+(\d+)\s*-\s*(\d+)', s)
        if m2: return max(1, round((int(m2.group(1)) + int(m2.group(2))) / 2.0 - 6))
        return None

    if "delivery_date_text" in df.columns:
        df["est_delivery_days"] = df["delivery_date_text"].apply(parse_est_days)
    else:
        df["est_delivery_days"] = None

    select_cols = [
        "Danh Mục", "delivery_fee", "sales_volume_num", "current_price", 
        "rating_val", "is_prime", "est_delivery_days"
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
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 8px;
            --font-family: 'Inter', sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            font-family: var(--font-family);
            color: var(--text-primary);
            padding: 10px 20px;
            overflow: hidden;
        }}
        .filter-bar {{
            display: flex; align-items: center; gap: 24px; margin-bottom: 20px;
            background: var(--card-bg); padding: 12px 20px; border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        }}
        .f-item {{ display: flex; align-items: center; gap: 10px; }}
        .f-label {{ font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; }}
        select {{
            padding: 8px 12px; border: 1px solid #D1D5DB; border-radius: 6px;
            font-family: inherit; color: var(--text-primary); outline: none; cursor: pointer; width: 220px; font-weight: 500;
        }}
        select:focus {{ border-color: var(--primary); }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            height: calc(100vh - 85px);
        }}
        .col-wrapper {{ display: flex; flex-direction: column; gap: 20px; height: 100%; }}
        .chart-card {{
            background: var(--card-bg); border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); padding: 16px;
            flex: 1; display: flex; flex-direction: column; justify-content: flex-start;
        }}
        .col-title {{ font-size: 15px; font-weight: 700; color: var(--text-primary); text-align: center; margin-bottom: 0px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid var(--primary); padding-bottom: 10px; }}
        .chart-title {{ font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 15px; color: var(--text-secondary); }}
        .chart-wrapper {{ position: relative; width: 100%; flex-grow: 1; min-height: 0; }}
    </style>
</head>
<body>

    <!-- Filter -->
    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Danh mục sản phẩm</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Tất cả danh mục</option>
            </select>
        </div>
    </div>

    <!-- Layout -->
    <div class="main-grid">
        <!-- COL 1 -->
        <div class="col-wrapper">
            <div class="col-title">Định Giá & Phí Vận Chuyển</div>
            <div class="chart-card">
                <div class="chart-title">Miễn Phí Ship so với Có Phí</div>
                <div class="chart-wrapper"><canvas id="c1_bar"></canvas></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Cơ Cấu Doanh Thu Toàn Ngành</div>
                <div class="chart-wrapper"><canvas id="c1_donut"></canvas></div>
            </div>
        </div>
        
        <!-- COL 2 -->
        <div class="col-wrapper">
            <div class="col-title">Top Seller & Prime</div>
            <div class="chart-card">
                <div class="chart-title">Tỷ Lệ Prime Nhóm Top 20% Bán Chạy</div>
                <div class="chart-wrapper"><canvas id="c2_donut"></canvas></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Chênh Lệch Doanh Số Bán Hàng</div>
                <div class="chart-wrapper"><canvas id="c2_bar"></canvas></div>
            </div>
        </div>

        <!-- COL 3 -->
        <div class="col-wrapper">
            <div class="col-title">Tốc Độ Giao & Rating</div>
            <div class="chart-card">
                <div class="chart-title">Trải Nghiệm Khách Hàng (Tốc Độ vs Đánh Giá)</div>
                <div class="chart-wrapper"><canvas id="c3_combo"></canvas></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Tỷ Trọng Cam Kết Thời Gian Giao</div>
                <div class="chart-wrapper"><canvas id="c3_donut"></canvas></div>
            </div>
        </div>
    </div>

<script>
    const RAW_DATA = {data_json_str};
    let GI = {{}};
    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));

    function setup() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.size = 11;
        
        let cats = new Set();
        RAW_DATA.forEach(d => {{ if(d['Danh Mục'] && d['Danh Mục'] !== 'Không Rõ') cats.add(d['Danh Mục']); }});
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option'); opt.value = c; opt.innerText = c; sel.appendChild(opt);
        }});
        
        initCharts();
        applyFilters();
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let data = RAW_DATA.filter(d => (cat === 'ALL' || d['Danh Mục'] === cat));
        updateData(data);
    }}

    function updateData(data) {{
        let p_cheap=[], p_mid=[], p_high=[];
        if(data.length > 0) {{
            let sortedP = [...data].sort((a,b)=>a.current_price - b.current_price);
            let third = Math.floor(sortedP.length/3);
            p_cheap = sortedP.slice(0, third).map(d=>d.current_price);
            p_mid = sortedP.slice(third, third*2).map(d=>d.current_price);
            p_high = sortedP.slice(third*2).map(d=>d.current_price);
        }}
        let maxC = p_cheap.length>0 ? p_cheap[p_cheap.length-1] : 0;
        let maxM = p_mid.length>0 ? p_mid[p_mid.length-1] : 0;

        let agg = {{}};
        ['Giá Thấp','Giá Tầm Trung','Giá Cao Cấp'].forEach(k=> {{
            agg[k] = {{ freeS:0, freeC:0, paidS:0, paidC:0, freeRev:0, paidRev:0 }};
        }});

        data.forEach(d => {{
            let seg = 'Giá Tầm Trung';
            if(d.current_price <= maxC) seg = 'Giá Thấp';
            else if(d.current_price > maxM) seg = 'Giá Cao Cấp';
            
            if(d.delivery_fee === 0) {{
                agg[seg].freeS += (d.sales_volume_num||0); agg[seg].freeC++;
                agg[seg].freeRev += (d.sales_volume_num||0)*d.current_price;
            }} else {{
                agg[seg].paidS += (d.sales_volume_num||0); agg[seg].paidC++;
                agg[seg].paidRev += (d.sales_volume_num||0)*d.current_price;
            }}
        }});

        GI.c1_bar.data.labels = ['Giá Thấp','Giá Tầm Trung','Giá Cao Cấp'];
        GI.c1_bar.data.datasets[0].data = [agg['Giá Thấp'].freeC>0?agg['Giá Thấp'].freeS/agg['Giá Thấp'].freeC:0, agg['Giá Tầm Trung'].freeC>0?agg['Giá Tầm Trung'].freeS/agg['Giá Tầm Trung'].freeC:0, agg['Giá Cao Cấp'].freeC>0?agg['Giá Cao Cấp'].freeS/agg['Giá Cao Cấp'].freeC:0];
        GI.c1_bar.data.datasets[1].data = [agg['Giá Thấp'].paidC>0?agg['Giá Thấp'].paidS/agg['Giá Thấp'].paidC:0, agg['Giá Tầm Trung'].paidC>0?agg['Giá Tầm Trung'].paidS/agg['Giá Tầm Trung'].paidC:0, agg['Giá Cao Cấp'].paidC>0?agg['Giá Cao Cấp'].paidS/agg['Giá Cao Cấp'].paidC:0];
        GI.c1_bar.update();

        let tF=0, tP=0;
        ['Giá Thấp','Giá Tầm Trung','Giá Cao Cấp'].forEach(k=> {{ tF+=agg[k].freeRev; tP+=agg[k].paidRev; }});
        GI.c1_donut.data.datasets[0].data = [tF, tP];
        GI.c1_donut.update();

        let sortedS = [...data].sort((a,b)=>(b.sales_volume_num||0) - (a.sales_volume_num||0));
        let top20count = Math.max(1, Math.floor(data.length*0.2));
        let top20 = sortedS.slice(0, top20count);
        let primeT = top20.filter(d=>d.is_prime).length;
        let nonT = top20.length - primeT;
        
        GI.c2_donut.data.datasets[0].data = [primeT, nonT];
        GI.c2_donut.update();

        let sPr=0, cPr=0, sNp=0, cNp=0;
        data.forEach(d=> {{
            if(d.is_prime) {{ sPr+=(d.sales_volume_num||0); cPr++; }}
            else {{ sNp+=(d.sales_volume_num||0); cNp++; }}
        }});
        GI.c2_bar.data.datasets[0].data = [cPr>0?sPr/cPr:0, cNp>0?sNp/cNp:0];
        GI.c2_bar.update();

        let dAgg = {{'1-3d':{{s:0,r:0,c:0}},'4-7d':{{s:0,r:0,c:0}},'8-14d':{{s:0,r:0,c:0}},'>14d':{{s:0,r:0,c:0}}}};
        let fastC=0, slowC=0;
        data.forEach(d=> {{
            if(d.est_delivery_days != null) {{
                let k = '>14d';
                if(d.est_delivery_days <= 3) k='1-3d';
                else if(d.est_delivery_days <= 7) k='4-7d';
                else if(d.est_delivery_days <= 14) k='8-14d';
                dAgg[k].s += (d.sales_volume_num||0); dAgg[k].r += (d.rating_val||0); dAgg[k].c++;
                
                if(d.est_delivery_days <= 7) fastC++; else slowC++;
            }}
        }});
        let dl = ['1-3d','4-7d','8-14d','>14d'];
        GI.c3_combo.data.labels = dl;
        GI.c3_combo.data.datasets[0].data = dl.map(k=> dAgg[k].c>0?dAgg[k].s/dAgg[k].c:0);
        GI.c3_combo.data.datasets[1].data = dl.map(k=> dAgg[k].c>0?dAgg[k].r/dAgg[k].c:0);
        GI.c3_combo.update();

        GI.c3_donut.data.datasets[0].data = [fastC, slowC];
        GI.c3_donut.update();
    }}

    function initCharts() {{
        const tbOpts = {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}}}, scales:{{y:{{grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback:fmtN}}}}}}, animation: {{ duration: 1000 }} }};
        const tdOpts = {{ responsive:true, maintainAspectRatio:false, cutout:'60%', plugins:{{legend:{{position:'bottom'}}}}, animation: {{ duration: 1000, animateScale: true }} }};

        GI.c1_bar = new Chart(document.getElementById('c1_bar').getContext('2d'), {{
            type:'bar', data: {{ labels:[], datasets:[{{label:'Miễn Phí Ship', data:[], backgroundColor:'#3b82f6', borderRadius:4}},{{label:'Có Phí Ship', data:[], backgroundColor:'#f97316', borderRadius:4}}] }}, options: tbOpts
        }});
        
        GI.c1_donut = new Chart(document.getElementById('c1_donut').getContext('2d'), {{
            type:'doughnut', data: {{ labels:['Miễn Phí Ship','Có Phí Ship'], datasets:[{{data:[], backgroundColor:['#3b82f6','#f97316'], borderWidth:0}}] }},
            options: tdOpts
        }});
        
        GI.c2_donut = new Chart(document.getElementById('c2_donut').getContext('2d'), {{
            type:'doughnut', data: {{ labels:['Có Prime','Không Prime'], datasets:[{{data:[], backgroundColor:['#10b981','#cbd5e1'], borderWidth:0}}] }},
            options: tdOpts
        }});

        GI.c2_bar = new Chart(document.getElementById('c2_bar').getContext('2d'), {{
            type:'bar', data: {{ labels:['Có Prime','Không Prime'], datasets:[{{label:'Doanh Số TB', data:[], backgroundColor:['#10b981','#cbd5e1'], borderRadius:4}}] }},
            options: {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}}, scales:{{x: {{grid: {{display:false}}}}, y:{{grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback:fmtN}}}}}}, animation: {{ duration: 1000 }} }}
        }});

        GI.c3_combo = new Chart(document.getElementById('c3_combo').getContext('2d'), {{
            type:'bar', data: {{ labels:[], datasets:[{{type:'bar',label:'Doanh Số',data:[],backgroundColor:'#facc15',yAxisID:'yl', borderRadius:4}},{{type:'line',label:'Đánh Giá',data:[],borderColor:'#ef4444',backgroundColor:'#ef4444',tension:0.3,yAxisID:'yr',borderWidth:3,pointRadius:4}}] }},
            options: {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}}}, scales:{{x:{{grid:{{display:false}}}}, yl:{{position:'left',grid:{{color:'rgba(0,0,0,0.05)'}},ticks:{{callback:fmtN}}}}, yr:{{position:'right',grid:{{display:false}},min:3.0,max:5.0}} }}, animation: {{ duration: 1000 }} }}
        }});

        GI.c3_donut = new Chart(document.getElementById('c3_donut').getContext('2d'), {{
            type:'doughnut', data: {{ labels:['Giao Nhanh (<=7 ng)','Giao Chậm'], datasets:[{{data:[], backgroundColor:['#facc15','#cbd5e1'], borderWidth:0}}] }},
            options: tdOpts
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
    """
    
    components.html(html_code, height=860, scrolling=False)
