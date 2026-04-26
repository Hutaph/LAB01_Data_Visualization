import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def render(df_raw):
    # Hiển thị tab Phân tích Nhãn Amazon's Choice.
    df = df_raw.copy()

    # 1. TIỀN XỬ LÝ DỮ LIỆU & MAPPING
    from utils.constants import CATEGORY_MAP

    # Khởi tạo các cột quan trọng
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

    # Mapping danh mục
    if "crawl_category" in df.columns:
        df["crawl_category"] = df["crawl_category"].fillna("Không rõ").map(CATEGORY_MAP).fillna("Khác")
    else:
        df["crawl_category"] = "Không rõ"

    # Chuyển đổi kiểu dữ liệu số
    df["current_price"] = pd.to_numeric(df.get("price", 0), errors="coerce").fillna(0.0)
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0)
    df["rating_val"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0.0)
    df["reviews_val"] = pd.to_numeric(df.get("reviews", 0), errors="coerce").fillna(0)
    
    if "title" not in df.columns:
        df["title"] = "Sản phẩm ẩn danh"
    else:
        df["title"] = df["title"].fillna("Sản phẩm ẩn danh")

    # Định nghĩa phân khúc giá
    def get_price_tier(p):
        if p <= 17.99: return "1. Bình dân (≤ $17.99)"
        if p <= 46.99: return "2. Trung cấp ($17.99-$46.99)"
        return "3. Cao cấp (≥ $46.99)"
        
    df["price_tier"] = df["current_price"].apply(get_price_tier)

    # 2. XUẤT DỮ LIỆU SANG JSON
    select_cols = [
        "title", "crawl_category", "is_amazon_choice", "is_best_seller", 
        "current_price", "sales_volume_num", "rating_val", "reviews_val", "is_prime", "price_tier"
    ]
    export_df = df[select_cols].copy()
    data_json_str = export_df.to_json(orient="records", force_ascii=False)

    # 3. TRỰC QUAN HÓA (HTML/CSS/JS)
    _HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root{--pr:#F97316;--dk:#9A3412;--bg:#FEF3E2;--card:#FFFFFF;--t1:#1C1917;--t2:#78716C;--t3:#A8A29E;--bd:#E7E5E4;--r:8px;--fn:'Inter',sans-serif}
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:var(--bg);font-family:var(--fn);color:var(--t1);padding:6px 14px 8px;height:100vh;overflow:hidden;display:flex;flex-direction:column;gap:8px}

        /* Filter Bar */
        .fb{
            display:flex;align-items:center;gap:24px;
            background:#fff;border:1px solid var(--bd);border-radius:10px;
            padding:12px 20px;box-shadow:0 1px 4px rgba(0,0,0,.06);flex-shrink:0;flex-wrap:wrap;
        }
        .fb-item label{
            display:block;font-size:10px;font-weight:700;color:var(--t2);
            text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;
        }
        .fb-item select{
            padding:7px 30px 7px 10px;border:1px solid var(--bd);border-radius:6px;
            font-size:13px;font-family:var(--fn);color:var(--t1);min-width:180px;
            background:#fafaf9 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716C' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat right 10px center;
            appearance:none;cursor:pointer;outline:none;
        }
        
        /* Toggle Switch (Matched with deal_impact.py) */
        .toggle-lbl { font-size: 11px; font-weight: 700; color: var(--t2); text-transform: uppercase; letter-spacing: 0.5px; }
        .toggle-group { display: flex; gap: 10px; align-items: center; cursor: pointer; user-select: none; }
        .toggle-track {
            position: relative; width: 44px; height: 24px;
            background-color: #E5E7EB; border-radius: 20px; transition: background-color 0.3s;
        }
        .toggle-track.active { background-color: var(--pr); }
        .toggle-thumb {
            position: absolute; top: 2px; left: 2px;
            width: 20px; height: 20px; background: white;
            border-radius: 50%; transition: transform 0.3s;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .toggle-track.active .toggle-thumb { transform: translateX(20px); }

        /* KPI Cards */
        .kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;flex-shrink:0}
        .kc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:14px 16px;border-left:4px solid var(--t3);}
        .kc.hi{border-left-color:var(--pr);background:#FFF7ED}
        .kt{font-size:10px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
        .kv{font-size:22px;font-weight:800;color:var(--t1)}
        .ks{font-size:10.5px;color:var(--t3);margin-top:2px}
        .kc.hi .kv{color:var(--dk)}

        /* Charts Layout */
        .g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;min-height:0}
        .cc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:10px 14px;display:flex;flex-direction:column;min-height:0;overflow:hidden}
        .ct{font-size:13px;font-weight:600;color:var(--t1);margin-bottom:2px}
        .cs{font-size:11px;color:var(--t2);margin-bottom:10px}
        .cw{position:relative;flex:1;min-height:0}
        .leg{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px}
        .li{display:flex;align-items:center;gap:4px;font-size:11px;color:var(--t2);font-weight:500}
        .ld{width:10px;height:10px;border-radius:2px;flex-shrink:0}
    </style>
</head>
<body>

<!-- 1. HEADER & FILTERS -->
<div class="fb">
  <div class="fb-item">
    <label>Danh mục</label>
    <select id="selCategory" onchange="applyFilters()">
      <option value="ALL">Tất cả Danh mục</option>
    </select>
  </div>

  <div class="fb-item">
    <span class="tg-lbl" style="display:block;font-size:10px;font-weight:700;color:var(--t2);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Bộ lọc Prime</span>
    <div class="toggle-group" onclick="togglePrime()" style="height: 32px;">
      <div class="toggle-track" id="primeTrack"><div class="toggle-thumb"></div></div>
      <span class="toggle-lbl">Chỉ Prime</span>
    </div>
  </div>

  <div style="margin-left:auto; display:flex; flex-direction:column; align-items:flex-end; justify-content:center;">
      <div style="font-size:16px; font-weight:800; color:var(--dk); font-family:var(--ft);">PHÂN TÍCH NHÃN AMAZON'S CHOICE</div>
      <div style="font-size:11px; color:var(--t2); font-weight:500;">Đánh giá tác động của nhãn uy tín đến hiệu suất sản phẩm</div>
  </div>
</div>

<!-- 2. KPI SUMMARY -->
<div class="kpi-row" id="kpiRow"></div>

<!-- 3. DASHBOARD CHARTS -->
<div class="g2">
  <div class="cc">
    <div class="ct">Thị phần theo Nhãn Uy Tín</div>
    <div class="cs">Tỷ trọng số lượng sản phẩm có nhãn Amazon's Choice</div>
    <div class="leg" id="dLeg"></div>
    <div class="cw"><canvas id="cDonut"></canvas></div>
  </div>
  <div class="cc">
    <div class="ct">So sánh hiệu suất bán ra (Doanh số)</div>
    <div class="cs">Doanh số trung bình giữa nhóm có và không có nhãn</div>
    <div class="cw"><canvas id="cBarSales"></canvas></div>
  </div>
  <div class="cc">
    <div class="ct">Tỷ lệ Amazon's Choice theo mức giá</div>
    <div class="cs">Phân bổ nhãn uy tín theo từng phân khúc giá</div>
    <div class="cw"><canvas id="cPriceTier"></canvas></div>
  </div>
  <div class="cc">
    <div class="ct">Ma trận Giá vs. Doanh Số Bán</div>
    <div class="cs">Mỗi điểm = 1 sản phẩm. Tương quan theo nhãn uy tín.</div>
    <div class="leg" id="sLeg"></div>
    <div class="cw"><canvas id="cScatter"></canvas></div>
  </div>
</div>

<script>
    const RAW = __DATA_JSON__;
    let charts = {};
    const COLORS = { choice: '#F97316', non: '#3266ad' };
    const SC = {"Amazon's Choice": '#F97316', "Thường": '#3266ad'};
    let primeOnly = false;
    
    Chart.defaults.font.family="'Inter',sans-serif"; 
    Chart.defaults.color='#78716C';

    const fN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fP = n => Number(n).toFixed(1) + '%';
    const fmtN = n => new Intl.NumberFormat('en-US').format(n);
    const fF = (n, d = 1) => new Intl.NumberFormat('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);

    function destroy() { Object.values(charts).forEach(c=>c&&c.destroy()); charts={}; }

    function setup() {
        let cats = new Set();
        RAW.forEach(d => { 
            if(d.crawl_category && d.crawl_category !== 'Không rõ' && d.crawl_category !== 'Khác') cats.add(d.crawl_category); 
        });

        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {
            let opt = document.createElement('option');
            opt.value = c; opt.innerText = c;
            sel.appendChild(opt);
        });

        applyFilters();
    }

    function togglePrime() {
        primeOnly = !primeOnly;
        document.getElementById('primeTrack').classList.toggle('active', primeOnly);
        applyFilters();
    }

    function applyFilters() {
        let cat = document.getElementById('selCategory').value;
        let data = RAW.filter(d => {
            if(cat !== 'ALL' && d.crawl_category !== cat) return false;
            if(primeOnly && !d.is_prime) return false;
            return true;
        });
        updateDashboard(data);
    }

    function updateDashboard(data) {
        destroy();
        if(data.length === 0) {
            document.getElementById('kpiRow').innerHTML = '<div style="grid-column:span 4;text-align:center;padding:20px;color:var(--t2)">Không có dữ liệu phù hợp bộ lọc</div>';
            return;
        }

        let G_choice = data.filter(d => d.is_amazon_choice);
        let G_non = data.filter(d => !d.is_amazon_choice);

        // Calculate KPIs
        let s_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.sales_volume_num,0)/G_choice.length : 0;
        let s_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.sales_volume_num,0)/G_non.length : 0;
        let s_pct = s_n > 0 ? ((s_c - s_n) / s_n) * 100 : 0;
        let r_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.rating_val,0)/G_choice.length : 0;
        let rev_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.reviews_val,0)/G_choice.length : 0;
        
        const kpis = [
            {t:'Tổng Sản Phẩm', v:fmtN(data.length), s:fN(G_choice.length)+' Choice / '+fN(G_non.length)+' Thường'},
            {t:'Chênh lệch Doanh số TB', v:(s_pct>=0?'+':'')+fP(s_pct), s:'TB: '+fN(s_c)+' (Choice) vs '+fN(s_n)+' (Thường)', hi:1},
            {t:'Rating Trung Bình (Choice)', v:fF(r_c, 1)+' ⭐', s:'Chất lượng đánh giá'},
            {t:'Số Review TB (Choice)', v:fN(rev_c), s:'Độ nhận diện sản phẩm'}
        ];
        document.getElementById('kpiRow').innerHTML = kpis.map(x=>`
            <div class="kc${x.hi?' hi':''}">
                <div class="kt">${x.t}</div>
                <div class="kv">${x.v}</div>
                <div class="ks">${x.s}</div>
            </div>`).join('');
        
        // Donut Chart
        const dCounts = [G_choice.length, G_non.length], dLabels = ["Amazon's Choice", "Thường"], dColors = [COLORS.choice, COLORS.non], dTotal = data.length;
        document.getElementById('dLeg').innerHTML = dLabels.map((lb,i)=>`<span class="li"><span class="ld" style="background:${dColors[i]}"></span>${lb} (${dTotal?fF(dCounts[i]/dTotal*100, 1):0}%)</span>`).join('');
        charts.donut = new Chart(document.getElementById('cDonut'),{type:'doughnut',data:{labels:dLabels,datasets:[{data:dCounts,backgroundColor:dColors,borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,cutout:'65%',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${fmtN(c.raw)} SP`}}}}});

        // Bar Chart - Sales Comparison
        charts.bar = new Chart(document.getElementById('cBarSales'),{type:'bar',data:{labels:["Amazon's Choice", "Thường"],datasets:[{data:[s_c, s_n],backgroundColor:[COLORS.choice, COLORS.non],borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.raw)} đơn`}}},scales:{x:{grid:{display:false}},y:{grid:{color:'rgba(0,0,0,0.04)'}}}}});

        // Price Tier Comparison
        let tiers = ["1. Bình dân (≤ $17.99)", "2. Trung cấp ($17.99-$46.99)", "3. Cao cấp (≥ $46.99)"], tierChData = [], tierNoData = [];
        tiers.forEach(t => { 
            let t_data = data.filter(d => d.price_tier === t); 
            if (t_data.length === 0) { tierChData.push(0); tierNoData.push(0); } 
            else { 
                let p = (t_data.filter(d => d.is_amazon_choice).length / t_data.length) * 100; 
                tierChData.push(p); tierNoData.push(100 - p); 
            } 
        });
        charts.tier = new Chart(document.getElementById('cPriceTier'),{type:'bar',data:{labels:tiers,datasets:[{label:"Choice (%)",data:tierChData,backgroundColor:COLORS.choice,borderRadius:3},{label:"Thường (%)",data:tierNoData,backgroundColor:COLORS.non,borderRadius:3}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8,font:{size:10}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${fF(c.raw, 1)}%`}}},scales:{x:{stacked:true,max:100,grid:{display:false},ticks:{callback:v=>v+'%'}},y:{stacked:true,grid:{display:false}}}}});

        // Scatter Chart - Price vs Sales
        document.getElementById('sLeg').innerHTML = dLabels.map(sg=>`<span class="li"><span class="ld" style="background:${SC[sg]}"></span>${sg}</span>`).join('');
        let rd = data.length > 500 ? [...data].sort(() => 0.5 - Math.random()).slice(0, 500) : data, scCh = [], scNo = [];
        rd.forEach(d => { let pt = {x: d.current_price, y: d.sales_volume_num}; if (d.is_amazon_choice) scCh.push(pt); else scNo.push(pt); });
        charts.scat = new Chart(document.getElementById('cScatter'),{type:'scatter',data:{datasets:[{label:"Amazon's Choice",data:scCh,backgroundColor:COLORS.choice+'80',pointRadius:4},{label:"Thường",data:scNo,backgroundColor:COLORS.non+'50',pointRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` $${fF(c.parsed.x, 2)} | ${fmtN(c.parsed.y)} đơn`}}},scales:{x:{title:{display:true,text:'Giá ($)'},grid:{color:'rgba(0,0,0,0.04)'}},y:{title:{display:true,text:'Doanh số'},grid:{color:'rgba(0,0,0,0.04)'},ticks:{callback:v=>v>=1000?fF(v/1000, 0)+'K':v}}}}});
    }

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
"""
    st.markdown("<style>.block-container{padding-top:.4rem!important;}</style>", unsafe_allow_html=True)
    html_final = _HTML.replace("__DATA_JSON__", data_json_str)
    components.html(html_final, height=720, scrolling=False)
