import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def render(df_raw):
    df = df_raw.copy()

    # ══════════════════════════════════════════════════════════════
    # 1. TIỀN XỬ LÝ DỮ LIỆU & MAPPING DANH MỤC
    # ══════════════════════════════════════════════════════════════
    from utils.constants import CATEGORY_MAP

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

    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"
    else:
        df["crawl_category"] = df["crawl_category"].fillna("Không rõ").map(CATEGORY_MAP).fillna("Khác")

    df["current_price"] = pd.to_numeric(df.get("price", 0), errors="coerce").fillna(0.0)
    df["sales_volume_num"] = pd.to_numeric(df.get("sales_volume_num", 0), errors="coerce").fillna(0)
    df["rating_val"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0.0)
    df["reviews_val"] = pd.to_numeric(df.get("reviews", 0), errors="coerce").fillna(0)
    
    if "title" not in df.columns:
        df["title"] = "Sản phẩm ẩn danh"
    else:
        df["title"] = df["title"].fillna("Sản phẩm ẩn danh")

    # Tạo phân khúc giá
    def get_price_tier(p):
        if p < 25: return "1. Bình dân (<$25)"
        elif p < 50: return "2. Phổ thông ($25-$50)"
        elif p < 100: return "3. Trung cấp ($50-$100)"
        else: return "4. Cao cấp (>$100)"
    df["price_tier"] = df["current_price"].apply(get_price_tier)

    # ══════════════════════════════════════════════════════════════
    # 2. XUẤT JSON CHO CHART.JS
    # ══════════════════════════════════════════════════════════════
    select_cols = [
        "title", "crawl_category", "is_amazon_choice", "is_best_seller", 
        "current_price", "sales_volume_num", "rating_val", "reviews_val", "is_prime", "price_tier"
    ]
    export_df = df[select_cols].copy()
    data_json_str = export_df.to_json(orient="records", force_ascii=False)

    # ══════════════════════════════════════════════════════════════
    # 3. HTML/CSS/JS CHUẨN ĐỒNG BỘ
    # ══════════════════════════════════════════════════════════════
    _HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root{--pr:#F97316;--dk:#9A3412;--bg:#FEF3E2;--card:#FFFFFF;--t1:#1C1917;--t2:#78716C;--t3:#A8A29E;--bd:#E7E5E4;--r:8px;--fn:'Inter',sans-serif;--ft:'Montserrat',sans-serif}
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:var(--bg);font-family:var(--fn);color:var(--t1);padding:6px 14px 8px;height:100vh;overflow:hidden;display:flex;flex-direction:column;gap:8px}

        /* ── FILTER BAR ── */
        .fb{
          display:grid;grid-template-columns:1fr;gap:14px;
          background:#fff;border:1px solid var(--bd);border-radius:10px;
          padding:12px 16px 14px;box-shadow:0 1px 4px rgba(0,0,0,.06);flex-shrink:0;
        }
        .fb-item label{
          display:block;font-size:10px;font-weight:700;color:var(--t2);
          text-transform:uppercase;letter-spacing:.6px;margin-bottom:5px;
        }
        .fb-item select{
          width:100%;padding:7px 30px 7px 10px;
          border:1px solid var(--bd);border-radius:6px;
          font-size:13px;font-family:var(--fn);color:var(--t1);
          background:#fafaf9 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716C' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat right 10px center;
          appearance:none;cursor:pointer;outline:none;transition:border-color .15s;
        }
        .fb-item select:hover{border-color:var(--pr);}
        .fb-item select:focus{border-color:var(--pr);box-shadow:0 0 0 3px rgba(249,115,22,.12);}

        /* ── KPI ── */
        .kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;flex-shrink:0}
        .kc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:10px 14px;border-left:3px solid var(--t3);}
        .kc.hi{border-left-color:var(--pr);background:#FFF7ED}
        .kt{font-size:10px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
        .kv{font-family:var(--ft);font-size:20px;font-weight:700;color:var(--t1);margin-bottom:2px}
        .ks{font-size:10.5px;color:var(--t3)}
        .kc.hi .kv{color:var(--dk)}

        /* ── CHARTS ── */
        .g2{display:grid;grid-template-columns:1fr 1fr;gap:10px;flex:1;min-height:0}
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

<!-- FILTER BAR -->
<div class="fb">
  <div class="fb-item">
    <label>Danh mục</label>
    <select id="selCategory" onchange="applyFilters()">
      <option value="ALL">Tất cả Danh mục</option>
    </select>
  </div>
</div>

<!-- KPI -->
<div class="kpi-row" id="kpiRow"></div>

<!-- CHARTS -->
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
    const COLORS = { choice: '#F97316', non: '#9A3412' };
    const SC = {"Amazon's Choice": '#F97316', "Thường": '#9A3412'};
    
    Chart.defaults.font.family="'Inter',sans-serif"; Chart.defaults.color='#78716C';
    const fN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fP = n => Number(n).toFixed(1) + '%';
    const fmtN = n => Number(n).toLocaleString('vi-VN');

    function destroy() { Object.values(charts).forEach(c=>c&&c.destroy()); charts={}; }

    function setup() {
        let cats = new Set();
        RAW.forEach(d => { if(d.crawl_category && d.crawl_category !== 'Không rõ' && d.crawl_category !== 'Khác') cats.add(d.crawl_category); });
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {
            let opt = document.createElement('option');
            opt.value = c; opt.innerText = c;
            sel.appendChild(opt);
        });
        applyFilters();
    }

    function applyFilters() {
        let cat = document.getElementById('selCategory').value;
        let data = RAW.filter(d => cat === 'ALL' || d.crawl_category === cat);
        updateDashboard(data);
    }

    function updateDashboard(data) {
        destroy();
        if(data.length === 0) return;
        
        let G_choice = data.filter(d => d.is_amazon_choice);
        let G_non = data.filter(d => !d.is_amazon_choice);
        
        // --- KPIs ---
        let s_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.sales_volume_num,0)/G_choice.length : 0;
        let s_n = G_non.length > 0 ? G_non.reduce((a,b)=>a+b.sales_volume_num,0)/G_non.length : 0;
        let s_pct = s_n > 0 ? ((s_c - s_n) / s_n) * 100 : 0;
        
        let r_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.rating_val,0)/G_choice.length : 0;
        let rev_c = G_choice.length > 0 ? G_choice.reduce((a,b)=>a+b.reviews_val,0)/G_choice.length : 0;
        
        const kpis = [
            {t:'Chênh lệch Doanh số TB', v:(s_pct>=0?'+':'')+fP(s_pct), s:'TB: '+fN(s_c)+' (Choice) vs '+fN(s_n)+' (Thường)', hi:1},
            {t:'Rating Trung Bình (Choice)', v:r_c.toFixed(1)+' ⭐', s:'Chất lượng đánh giá'},
            {t:'Số Review TB (Choice)', v:fmtN(rev_c), s:'Độ nhận diện sản phẩm'},
            {t:'Tổng Sản Phẩm', v:fmtN(data.length), s:G_choice.length+' Choice / '+G_non.length+' Thường'}
        ];
        document.getElementById('kpiRow').innerHTML = kpis.map(x=>`<div class="kc${x.hi?' hi':''}"><div class="kt">${x.t}</div><div class="kv">${x.v}</div><div class="ks">${x.s}</div></div>`).join('');
        
        // --- 1. Donut Chart ---
        const dCounts = [G_choice.length, G_non.length];
        const dLabels = ["Amazon's Choice", "Thường"];
        const dColors = [COLORS.choice, COLORS.non];
        const dTotal  = data.length;
        document.getElementById('dLeg').innerHTML = dLabels.map((lb,i)=>`<span class="li"><span class="ld" style="background:${dColors[i]}"></span>${lb} (${dTotal?(dCounts[i]/dTotal*100).toFixed(1):0}%)</span>`).join('');
        charts.donut = new Chart(document.getElementById('cDonut'),{type:'doughnut',
            data:{labels:dLabels,datasets:[{data:dCounts,backgroundColor:dColors,borderWidth:0}]},
            options:{responsive:true,maintainAspectRatio:false,cutout:'65%',
            plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${fmtN(c.raw)} SP`}}}}});

        // --- 2. Bar Chart (Sales) ---
        charts.bar = new Chart(document.getElementById('cBarSales'),{type:'bar',
            data:{labels:["Amazon's Choice", "Thường"],datasets:[{data:[s_c, s_n],backgroundColor:[COLORS.choice, COLORS.non],borderRadius:6}]},
            options:{responsive:true,maintainAspectRatio:false,
            plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.raw)} đơn`}}},
            scales:{x:{grid:{display:false}},y:{grid:{color:'rgba(0,0,0,0.04)'}}}}});

        // --- 3. Price Tier ---
        let tiers = ["1. Bình dân (<$25)", "2. Phổ thông ($25-$50)", "3. Trung cấp ($50-$100)", "4. Cao cấp (>$100)"];
        let tierChData = [], tierNoData = [];
        tiers.forEach(t => {
            let t_data = data.filter(d => d.price_tier === t);
            if (t_data.length === 0) { tierChData.push(0); tierNoData.push(0); }
            else { 
                let p = (t_data.filter(d => d.is_amazon_choice).length / t_data.length) * 100;
                tierChData.push(p); tierNoData.push(100 - p); 
            }
        });
        charts.tier = new Chart(document.getElementById('cPriceTier'),{type:'bar',
            data:{labels:tiers,datasets:[{label:"Choice (%)",data:tierChData,backgroundColor:COLORS.choice,borderRadius:3},{label:"Thường (%)",data:tierNoData,backgroundColor:COLORS.non,borderRadius:3}]},
            options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
            plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8,font:{size:10}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${c.raw.toFixed(1)}%`}}},
            scales:{x:{stacked:true,max:100,grid:{display:false},ticks:{callback:v=>v+'%'}},y:{stacked:true,grid:{display:false}}}}});

        // --- 4. Scatter ---
        document.getElementById('sLeg').innerHTML = dLabels.map(sg=>`<span class="li"><span class="ld" style="background:${SC[sg]}"></span>${sg}</span>`).join('');
        let renderData = data.length > 500 ? [...data].sort(() => 0.5 - Math.random()).slice(0, 500) : data;
        let scatterCh = [], scatterNo = [];
        renderData.forEach(d => {
            let pt = {x: d.current_price, y: d.sales_volume_num};
            if (d.is_amazon_choice) scatterCh.push(pt); else scatterNo.push(pt);
        });
        charts.scat = new Chart(document.getElementById('cScatter'),{type:'scatter',
            data:{datasets:[
                {label:"Amazon's Choice",data:scatterCh,backgroundColor:COLORS.choice+'80',pointRadius:4},
                {label:"Thường",data:scatterNo,backgroundColor:COLORS.non+'50',pointRadius:3}
            ]},
            options:{responsive:true,maintainAspectRatio:false,
            plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` $${c.parsed.x} | ${fmtN(c.parsed.y)} đơn`}}},
            scales:{x:{title:{display:true,text:'Giá ($)'},grid:{color:'rgba(0,0,0,0.04)'}},
                    y:{title:{display:true,text:'Doanh số'},grid:{color:'rgba(0,0,0,0.04)'},ticks:{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v}}}}});
    }

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
"""
    st.markdown("<style>.block-container{padding-top:.4rem!important;}</style>", unsafe_allow_html=True)
    html_final = _HTML.replace("__DATA_JSON__", data_json_str)
    components.html(html_final, height=650, scrolling=False)


