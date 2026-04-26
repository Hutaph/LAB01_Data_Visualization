import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils.constants import CATEGORY_MAP

def _prep_data(df: pd.DataFrame):
    # Dọn dẹp và chuẩn bị dữ liệu cho biểu đồ
    data = df.copy()
    
    # Đảm bảo các cột cần thiết tồn tại và có kiểu dữ liệu số
    cols_to_fix = [
        ("current_price", 0.0),
        ("original_price", 0.0),
        ("rating", 0.0),
        ("reviews", 0),
        ("sales_volume_num", 0)
    ]
    
    for col, fallback in cols_to_fix:
        if col == "current_price":
            src_col = "price" if "price" in data.columns else "current_price"
            data[col] = data[src_col] if src_col in data.columns else fallback
        elif col not in data.columns:
            data[col] = fallback
            
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(fallback)

    # Xử lý danh mục
    if "crawl_category" not in data.columns:
        data["crawl_category"] = "Không rõ"
    else:
        data["crawl_category"] = data["crawl_category"].fillna("Không rõ").map(CATEGORY_MAP).fillna("Khác")
    
    data["title"] = data.get("title", pd.Series(["Sản phẩm ẩn danh"] * len(data))).fillna("Sản phẩm ẩn danh")

    select_cols = [
        "title", "crawl_category",
        "current_price", "original_price",
        "rating", "reviews", "sales_volume_num",
    ]
    export = data[select_cols].copy()

    # Chuẩn hóa kiểu dữ liệu trước khi serialize
    for c in ["current_price", "original_price", "rating", "reviews", "sales_volume_num"]:
        export[c] = pd.to_numeric(export[c], errors="coerce").fillna(0)
    
    export["sales_volume_num"] = export["sales_volume_num"].astype(float)
    export["reviews"] = export["reviews"].astype(float)
    
    return export.to_dict(orient="records")

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
    --primary:        #F97316;
    --dark:           #9A3412;
    --bg:             #FEF3E2;
    --card-bg:        #FFFFFF;
    --text-primary:   #1C1917;
    --text-secondary: #78716C;
    --border-radius:  12px;
    --font:           'Inter', sans-serif;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background: var(--bg);
    font-family: var(--font);
    color: var(--text-primary);
    padding: 16px;
    overflow-y: auto;
    overflow-x: hidden;
}

body::-webkit-scrollbar { display: none; }

.fb {
    display: flex; align-items: center; gap: 20px; background: #fff;
    border: 1px solid #E7E5E4; border-radius: var(--border-radius);
    padding: 12px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
    margin-bottom: 16px;
}
.fb-item { display: flex; flex-direction: column; gap: 4px; }
.fb-item label { font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: .8px; }
.fb-item select {
    padding: 8px 12px; border: 1px solid #E7E5E4; border-radius: 8px;
    font-size: 13px; font-family: var(--font); color: var(--text-primary);
    background: #fafaf9 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716C' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat right 10px center;
    appearance: none; cursor: pointer; outline: none; min-width: 190px;
}
.toggle-group { display: flex; background: #F3F4F6; border-radius: 8px; padding: 3px; gap: 2px; }
.toggle-btn {
    border: none; background: transparent; font-family: var(--font); font-size: 11px;
    font-weight: 600; color: var(--text-secondary); padding: 6px 12px; border-radius: 6px; cursor: pointer;
}
.toggle-btn.active { background: #FFFFFF; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.kc {
    background: var(--card-bg); border-left: 4px solid var(--primary);
    border-radius: var(--border-radius); box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;
}
.kc.accent { border-left-color: var(--dark); background: linear-gradient(135deg, #FFF7ED 0%, #FFFFFF 100%); }
.kt { font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; }
.kv { font-size: 22px; font-weight: 700; color: var(--text-primary); line-height: 1.1; }
.ks { font-size: 11px; color: #9CA3AF; }

#row-charts { display: flex; gap: 12px; height: 420px; }
.cc {
    background: var(--card-bg); border-radius: var(--border-radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05); padding: 16px;
    display: flex; flex-direction: column; overflow: hidden;
}
.cc.left  { flex: 0 0 55%; }
.cc.right { flex: 0 0 calc(45% - 12px); }
.ct { font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; }
.cc canvas { flex: 1; width: 100%; min-height: 0; display: block; }

#chartTooltip {
    position: fixed; background: #1C1917; color: #fff; padding: 6px 10px;
    border-radius: 6px; font: 12px Inter, sans-serif; pointer-events: none;
    opacity: 0; transition: opacity 0.15s; z-index: 9999; line-height: 1.6; white-space: pre-wrap;
}
</style>
</head>
<body>

<div class="fb">
    <div class="fb-item">
        <label>Danh Mục Sản Phẩm</label>
        <select id="selCategory" onchange="applyFilters()">
            <option value="ALL">Tất cả danh mục</option>
        </select>
    </div>
    <div class="fb-item">
        <label>Nhóm Biểu Đồ</label>
        <div class="toggle-group">
            <button class="toggle-btn active" id="btn_rating" onclick="setMode('rating')">Theo Rating</button>
            <button class="toggle-btn"        id="btn_reviews" onclick="setMode('reviews')">Theo Reviews</button>
        </div>
    </div>
    <div class="fb-item">
        <label>Chỉ Số Doanh Số</label>
        <div class="toggle-group">
            <button class="toggle-btn active" id="btn_mean"   onclick="setMetric('mean')">Mean</button>
            <button class="toggle-btn"        id="btn_median" onclick="setMetric('median')">Median</button>
        </div>
    </div>
    <div style="margin-left:auto; text-align:right;">
        <div style="font-size:16px; font-weight:800; color:var(--dark);">PHÂN TÍCH ĐÁNH GIÁ SẢN PHẨM</div>
        <div style="font-size:10px; color:var(--text-secondary); font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Tương quan Rating, Reviews & Doanh số</div>
    </div>
</div>

<div class="kpi-row">
    <div class="kc">
        <div class="kt">Rating</div>
        <div class="kv" id="kpi_rating">0★</div>
        <div class="ks" id="kpi_rating_sub">–</div>
    </div>
    <div class="kc accent">
        <div class="kt">Doanh Số - Rating ≥ 4.5</div>
        <div class="kv" id="kpi_sales_hi">–</div>
        <div class="ks" id="kpi_sales_hi_sub">So với rating < 4.5</div>
    </div>
    <div class="kc accent">
        <div class="kt">Giá - Rating ≥ 4.5</div>
        <div class="kv" id="kpi_price_hi_rating">–</div>
        <div class="ks" id="kpi_price_hi_rating_sub">So với rating < 4.5</div>
    </div>
    <div class="kc">
        <div class="kt">Doanh Số - Reviews Top 25%</div>
        <div class="kv" id="kpi_sales_top_reviews">–</div>
        <div class="ks" id="kpi_sales_top_reviews_sub">So với 75% còn lại</div>
    </div>
    <div class="kc">
        <div class="kt">Giá - Reviews Top 25%</div>
        <div class="kv" id="kpi_price_top">–</div>
        <div class="ks" id="kpi_price_top_sub">So với 75% còn lại</div>
    </div>
</div>

<div id="chartTooltip"></div>

<div id="row-charts">
    <div class="cc left">
        <div class="ct" id="comboTitle">Doanh số & Giá TB theo nhóm Rating</div>
        <canvas id="canvasCombo"></canvas>
    </div>
    <div class="cc right">
        <div class="ct">Mối quan hệ giữa Rating và Reviews</div>
        <canvas id="canvasScatter"></canvas>
    </div>
</div>

<script>
const RAW_DATA = __DATA_JSON__;
const tooltip = document.getElementById('chartTooltip');

function showTooltip(e, text) {
    tooltip.textContent = text;
    tooltip.style.opacity = '1';
    let tx = e.clientX + 12, ty = e.clientY + 12;
    if (tx + tooltip.offsetWidth > window.innerWidth) tx = e.clientX - tooltip.offsetWidth - 12;
    tooltip.style.left = tx + 'px'; tooltip.style.top = ty + 'px';
}
function hideTooltip() { tooltip.style.opacity = '0'; }

const fmtN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
const fmtF = (n, d=2) => Number(n).toFixed(d);
const fmtK = n => n >= 1000 ? (n/1000).toFixed(0)+'k' : fmtN(n);

function median(arr) {
    if (!arr.length) return 0;
    const s = [...arr].sort((a,b) => a-b);
    const m = Math.floor(s.length / 2);
    return s.length % 2 === 0 ? (s[m-1]+s[m])/2 : s[m];
}
function mean(arr) { return arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0; }
function quantile(arr, q) {
    if (!arr.length) return 0;
    const s = [...arr].sort((a,b)=>a-b);
    const pos = (s.length - 1) * q;
    const lo = Math.floor(pos), hi = Math.ceil(pos);
    return s[lo] + (s[hi] - s[lo]) * (pos - lo);
}

function initDropdown() {
    const cats = [...new Set(RAW_DATA.map(d => d.crawl_category).filter(c => c && c !== 'Không rõ' && c !== 'Khác'))].sort();
    const sel = document.getElementById('selCategory');
    cats.forEach(c => {
        const o = document.createElement('option'); o.value = o.textContent = c; sel.appendChild(o);
    });
}

let METRIC = 'mean';
function setMetric(m) {
    METRIC = m;
    document.getElementById('btn_mean').classList.toggle('active', m === 'mean');
    document.getElementById('btn_median').classList.toggle('active', m === 'median');
    applyFilters();
}

let currentMode = 'rating';
function setMode(m) {
    currentMode = m;
    document.getElementById('btn_rating').classList.toggle('active', m === 'rating');
    document.getElementById('btn_reviews').classList.toggle('active', m === 'reviews');
    document.getElementById('comboTitle').textContent = m === 'rating' ? 'Doanh số & Giá TB theo nhóm Rating' : 'Doanh số & Giá TB theo nhóm Reviews';
    applyFilters();
}

function getFiltered() {
    const cat = document.getElementById('selCategory').value;
    return RAW_DATA.filter(d => cat === 'ALL' || d.crawl_category === cat);
}

function updateKPIs(data) {
    const metricFn = arr => METRIC === 'median' ? median(arr) : mean(arr);
    const ratings = data.map(d => d.rating).filter(r => r > 0);
    const totalRev = data.reduce((a,b) => a + (b.reviews||0), 0);
    document.getElementById('kpi_rating').textContent = fmtF(mean(ratings)) + '★';
    document.getElementById('kpi_rating_sub').textContent = `từ ${fmtN(totalRev)} lượt đánh giá`;

    const hiSales = data.filter(d => d.rating >= 4.5 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const loSales = data.filter(d => d.rating <  4.5 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const valHiS = metricFn(hiSales), valLoS = metricFn(loSales);
    document.getElementById('kpi_sales_hi').textContent = valHiS > 0 ? fmtN(valHiS) + ' đơn' : 'N/A';
    document.getElementById('kpi_sales_hi_sub').textContent = valLoS > 0 ? `${(valHiS-valLoS)/valLoS*100 >= 0 ? '+' : ''}${fmtF((valHiS-valLoS)/valLoS*100,1)}% so với rating < 4.5` : 'Nhóm rating ≥ 4.5';

    const hiPrices = data.filter(d => d.rating >= 4.5 && d.current_price > 0).map(d => d.current_price);
    const loPrices = data.filter(d => d.rating <  4.5 && d.current_price > 0).map(d => d.current_price);
    const avgHiP = mean(hiPrices), avgLoP = mean(loPrices);
    document.getElementById('kpi_price_hi_rating').textContent = avgHiP > 0 ? '$' + fmtF(avgHiP, 2) : 'N/A';
    document.getElementById('kpi_price_hi_rating_sub').textContent = avgLoP > 0 ? `${avgHiP-avgLoP >= 0 ? '+' : '-'}$${fmtF(Math.abs(avgHiP-avgLoP),2)} so với nhóm < 4.5` : 'Giá TB nhóm rating ≥ 4.5';

    const allRevs = data.map(d => d.reviews).filter(r => r > 0);
    const q75 = quantile(allRevs, 0.75);
    const topS = data.filter(d => d.reviews >= q75 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const botS = data.filter(d => d.reviews <  q75 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const valTS = metricFn(topS), valBS = metricFn(botS);
    document.getElementById('kpi_sales_top_reviews').textContent = valTS > 0 ? fmtN(valTS) + ' đơn' : 'N/A';
    document.getElementById('kpi_sales_top_reviews_sub').textContent = valBS > 0 ? `${(valTS-valBS)/valBS*100 >= 0 ? '+' : ''}${fmtF((valTS-valBS)/valBS*100,1)}% so với 75% còn lại` : 'Nhóm reviews top 25%';

    const topP = data.filter(d => d.reviews >= q75 && d.current_price > 0).map(d => d.current_price);
    const botP = data.filter(d => d.reviews <  q75 && d.current_price > 0).map(d => d.current_price);
    const avgTP = mean(topP), avgBP = mean(botP);
    document.getElementById('kpi_price_top').textContent = avgTP > 0 ? '$' + fmtF(avgTP, 2) : 'N/A';
    document.getElementById('kpi_price_top_sub').textContent = avgBP > 0 ? `${avgTP-avgBP >= 0 ? '+' : '-'}$${fmtF(Math.abs(avgTP-avgBP),2)} so với 75% còn lại` : 'Giá TB nhóm reviews top 25%';
}

function buildComboGroups(mode, data) {
    const mFn = arr => METRIC === 'median' ? median(arr) : mean(arr);
    if (mode === 'rating') {
        const defs = [{l:'<3.5',f:r=>r<3.5},{l:'3.5-3.9',f:r=>r>=3.5&&r<4},{l:'4.0-4.4',f:r=>r>=4&&r<4.5},{l:'4.5-4.7',f:r=>r>=4.5&&r<4.8},{l:'4.8-5.0',f:r=>r>=4.8}];
        return defs.map(g => {
            const fd = data.filter(d => g.f(d.rating));
            const ds = fd.filter(d=>d.sales_volume_num>0).map(d=>d.sales_volume_num), ps = fd.filter(d=>d.current_price>0).map(d=>d.current_price);
            return { lbl: g.l, s: mFn(ds), p: mean(ps), sCount: ds.length, pCount: ps.length };
        });
    }
    const revs = data.map(d=>d.reviews||0), q25=quantile(revs,0.25), q50=quantile(revs,0.5), q75=quantile(revs,0.75);
    const buckets = [{l:'Q1',ds:[],ps:[]},{l:'Q2',ds:[],ps:[]},{l:'Q3',ds:[],ps:[]},{l:'Q4',ds:[],ps:[]}];
    data.forEach(d => {
        const r=d.reviews||0, idx = r>=q75?3:r>=q50?2:r>=q25?1:0;
        if(d.sales_volume_num>0) buckets[idx].ds.push(d.sales_volume_num);
        if(d.current_price>0) buckets[idx].ps.push(d.current_price);
    });
    return buckets.map(g => ({ lbl: g.l, s: mFn(g.ds), p: mean(g.ps), sCount: g.ds.length, pCount: g.ps.length }));
}

function drawComboChart(mode, data) {
    const canvas = document.getElementById('canvasCombo'), ctx = canvas.getContext('2d'), dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr; canvas.height = canvas.offsetHeight * dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(dpr, dpr);
    const cW = canvas.offsetWidth, cH = canvas.offsetHeight; ctx.clearRect(0,0,cW,cH);
    if (!data.length) return;
    const stats = buildComboGroups(mode, data), maxS = Math.max(1, ...stats.map(s=>s.s))*1.15, maxP = Math.max(1, ...stats.map(s=>s.p))*1.15;
    const pad = {t:50,r:60,b:50,l:60}, w = cW-pad.l-pad.r, h = cH-pad.t-pad.b, gap = w/stats.length;

    ctx.fillStyle = 'rgba(249, 115, 22, 0.08)';
    if(mode==='rating') ctx.fillRect(pad.l+3*gap, pad.t, 2*gap, h); else ctx.fillRect(pad.l+3*gap, pad.t, gap, h);

    ctx.fillStyle='#78716C'; ctx.font='11px Inter'; ctx.textBaseline='middle';
    for(let i=0;i<=5;i++){
        const y=pad.t+h-(i/5)*h; ctx.textAlign='right'; ctx.fillText(fmtK(maxS*i/5),pad.l-8,y);
        ctx.textAlign='left'; ctx.fillText('$'+fmtN(maxP*i/5),pad.l+w+8,y);
        ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(pad.l+w,y); ctx.strokeStyle='#E5E7EB'; ctx.stroke();
    }
    const barW = Math.min(50, gap*0.4);
    stats.forEach((d,i) => {
        const bH=(d.s/maxS)*h, x=pad.l+i*gap+gap/2-barW/2, y=pad.t+h-bH;
        ctx.fillStyle='#F97316'; ctx.fillRect(x,y,barW,bH);
        ctx.fillStyle='#78716C'; ctx.textAlign='center'; ctx.textBaseline='top'; ctx.fillText(d.lbl, pad.l+i*gap+gap/2, pad.t+h+8);
    });
    ctx.beginPath(); ctx.strokeStyle='#9A3412'; ctx.lineWidth=2;
    stats.forEach((d,i) => { const x=pad.l+i*gap+gap/2, y=pad.t+h-(d.p/maxP)*h; if(i===0)ctx.moveTo(x,y); else ctx.lineTo(x,y); });
    ctx.stroke();
    stats.forEach((d,i) => {
        const x=pad.l+i*gap+gap/2, y=pad.t+h-(d.p/maxP)*h;
        ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2); ctx.fillStyle='#fff'; ctx.fill(); ctx.strokeStyle='#9A3412'; ctx.lineWidth=1.5; ctx.stroke();
        ctx.fillStyle='#9A3412'; ctx.textAlign='center'; ctx.textBaseline=y-pad.t<20?'top':'bottom'; ctx.fillText('$'+fmtF(d.p,1),x,y+(y-pad.t<20?8:-8));
    });

    const lx = cW / 2, ly = 18;
    ctx.fillStyle = '#F97316'; ctx.fillRect(lx - 90, ly - 5, 12, 10);
    ctx.fillStyle = '#1C1917'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.font = '12px Inter';
    ctx.fillText('Doanh số TB', lx - 72, ly);
    ctx.beginPath(); ctx.strokeStyle = '#9A3412'; ctx.lineWidth = 2; ctx.moveTo(lx + 14, ly); ctx.lineTo(lx + 34, ly); ctx.stroke();
    ctx.beginPath(); ctx.fillStyle = '#9A3412'; ctx.arc(lx + 24, ly, 3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#1C1917'; ctx.fillText('Giá TB ($)', lx + 40, ly);

    ctx.fillStyle = '#78716C'; ctx.font = '12px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(mode === 'rating' ? 'Nhóm Rating' : 'Nhóm Reviews (Quartile)', pad.l + w / 2, pad.t + h + 28);
    ctx.save(); ctx.translate(14, pad.t + h / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('Doanh số', 0, 0); ctx.restore();
    ctx.save(); ctx.translate(cW - 14, pad.t + h / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('Giá ($)', 0, 0); ctx.restore();

    canvas.onmousemove = e => {
        const rect=canvas.getBoundingClientRect(), mx=e.clientX-rect.left, my=e.clientY-rect.top;
        for(let i=0;i<stats.length;i++){
            const px=pad.l+i*gap+gap/2, py=pad.t+h-(stats[i].p/maxP)*h;
            if(Math.hypot(mx-px,my-py)<=10){ showTooltip(e,`Nhóm: ${stats[i].lbl}\nGiá TB: $${fmtF(stats[i].p)}\nSố SP: ${fmtN(stats[i].pCount)}`); return; }
            const bH=(stats[i].s/maxS)*h, bx=pad.l+i*gap+gap/2-barW/2, by=pad.t+h-bH;
            if(mx>=bx && mx<=bx+barW && my>=by && my<=pad.t+h){ showTooltip(e,`Nhóm: ${stats[i].lbl}\nDS TB: ${fmtN(stats[i].s)} đơn\nSố có DS: ${fmtN(stats[i].sCount)}`); return; }
        }
        hideTooltip();
    };
    canvas.onmouseleave=hideTooltip;
}

function drawScatterPlot(data) {
    const canvas = document.getElementById('canvasScatter'), ctx = canvas.getContext('2d'), dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr; canvas.height = canvas.offsetHeight * dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(dpr, dpr);
    const cW = canvas.offsetWidth, cH = canvas.offsetHeight; ctx.clearRect(0,0,cW,cH);
    const valid = data.filter(d=>d.rating>=1&&d.reviews>0); if(!valid.length) return;
    const pad = {t:50,r:20,b:50,l:60}, w=cW-pad.l-pad.r, h=cH-pad.t-pad.b;
    const minLog=Math.floor(Math.log10(Math.min(...valid.map(d=>d.reviews)))), maxLog=Math.ceil(Math.log10(Math.max(...valid.map(d=>d.reviews))));
    const getX = r => pad.l+((Math.max(2.5,Math.min(5,r))-2.5)/2.5)*(w-10), getY = rv => pad.t+h-((Math.log10(rv)-minLog)/(maxLog-minLog||1))*h;

    ctx.fillStyle='#78716C'; ctx.font='10px Inter'; ctx.textAlign='right';
    for(let i=minLog;i<=maxLog;i++){ const y=getY(Math.pow(10,i)); ctx.fillText(fmtK(Math.pow(10,i)),pad.l-6,y); ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(pad.l+w,y);ctx.strokeStyle='#f3f4f6';ctx.stroke(); }
    valid.forEach(d => {
        ctx.beginPath(); ctx.arc(getX(d.rating),getY(d.reviews),3.5,0,Math.PI*2);
        const s=d.sales_volume_num; ctx.fillStyle=s>2000?'rgba(154,52,18,0.8)':s>500?'rgba(249,115,22,0.7)':'rgba(209,213,219,0.5)'; ctx.fill();
    });

    const legends = [{l:'Không DS',c:'rgba(209,213,219,0.5)'},{l:'DS Thấp',c:'rgba(249,180,100,0.7)'},{l:'DS TB',c:'rgba(249,115,22,0.7)'},{l:'DS Cao',c:'rgba(154,52,18,0.8)'}];
    let lx = pad.l + w - 4; const ly = 18; ctx.textAlign = 'right'; ctx.textBaseline = 'middle'; ctx.font = '11px Inter';
    [...legends].reverse().forEach(lg => {
        ctx.fillStyle = '#1C1917'; ctx.fillText(lg.l, lx, ly);
        const tw = ctx.measureText(lg.l).width; ctx.fillStyle = lg.c;
        ctx.beginPath(); ctx.arc(lx - tw - 6, ly, 4, 0, Math.PI * 2); ctx.fill(); lx -= (tw + 20);
    });

    ctx.fillStyle = '#78716C'; ctx.font = '12px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText('Rating (★)', pad.l + w / 2, pad.t + h + 26);
    ctx.save(); ctx.translate(14, pad.t + h / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('Số Reviews (log)', 0, 0); ctx.restore();

    canvas.onmousemove = e => {
        const rect=canvas.getBoundingClientRect(), mx=e.clientX-rect.left, my=e.clientY-rect.top;
        for(let i=0;i<valid.length;i++){
            const d=valid[i], px=getX(d.rating), py=getY(d.reviews);
            if(Math.hypot(mx-px,my-py)<=6){ showTooltip(e,`Rating: ${d.rating}★\nReviews: ${fmtN(d.reviews)}\nDoanh số: ${fmtN(d.sales_volume_num||0)} đơn`); return; }
        }
        hideTooltip();
    };
    canvas.onmouseleave=hideTooltip;
}

function applyFilters() {
    const d = getFiltered(); updateKPIs(d); drawComboChart(currentMode, d); drawScatterPlot(d);
}

initDropdown(); applyFilters();
window.onresize = applyFilters;
</script>
</body>
</html>"""

def render(df: pd.DataFrame):
    # Giao diện chính tab Đánh Giá
    st.markdown("<style>.block-container { padding-top: 1rem !important; }</style>", unsafe_allow_html=True)
    
    # Chuẩn bị dữ liệu JSON
    data_list = _prep_data(df)
    
    # Inject dữ liệu vào template
    html = _HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(data_list, ensure_ascii=False))
    
    components.html(html, height=680, scrolling=False)
