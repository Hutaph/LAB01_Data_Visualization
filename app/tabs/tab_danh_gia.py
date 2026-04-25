import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render(df: pd.DataFrame):
    data = df.copy()
    CATEGORY_MAP = {
        "electronics_laptops": "Laptop",
        "electronics_tablets": "Máy Tính Bảng",
        "electronics_smartphones": "Điện Thoại",
        "electronics_monitors": "Màn Hình",
        "electronics_headphones": "Tai Nghe",
        "electronics_keyboards": "Bàn Phím",
        "electronics_storage_ssd": "Ổ Cứng & SSD",
        "electronics_networking": "Thiết Bị Mạng",
        "electronics_gaming_consoles": "Máy Chơi Game",
        "home_kitchen_appliances": "Thiết Bị Bếp",
        "home_cleaning": "Dụng Cụ Vệ Sinh",
        "home_air_quality": "Máy Lọc Khí",
        "home_furniture": "Nội Thất",
        "office_supplies": "Văn Phòng Phẩm",
        "office_stationery": "Dụng Cụ VP",
        "fashion_mens": "Thời Trang Nam",
        "fashion_womens": "Thời Trang Nữ",
        "fashion_shoes": "Giày Dép",
        "fashion_bags": "Túi Xách",
        "beauty_skincare": "Chăm Sóc Da",
        "beauty_makeup": "Trang Điểm",
        "health_personal_care": "Chăm Sóc Cá Nhân",
        "health_supplements": "TPCN & Vitamin",
        "baby_products": "Sản Phẩm Cho Bé",
        "toys_games": "Đồ Chơi & Game",
        "sports_outdoors": "Thể Thao Ngoài Trời",
        "sports_fitness": "Dụng Cụ Gym",
        "pet_supplies": "Thú Cưng",
        "automotive_accessories": "Phụ Kiện Ô Tô",
        "tools_home_improvement": "Dụng Cụ Sửa Nhà",
    }

    # Đảm bảo các cột cần thiết tồn tại và có kiểu dữ liệu số
    for col, fallback in [
        ("current_price", 0.0),
        ("original_price", 0.0),
        ("rating", 0.0),
        ("reviews", 0),
        ("sales_volume_num", 0)
    ]:
        if col == "current_price":
            # Ưu tiên lấy từ cột "price" nếu có
            src_col = "price" if "price" in data.columns else "current_price"
            if src_col in data.columns:
                data[col] = data[src_col]
            else:
                data[col] = fallback
        elif col not in data.columns:
            data[col] = fallback
            
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(fallback)

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
    data_json_str = json.dumps(export.to_dict(orient="records"), ensure_ascii=False)

    html_code = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --primary:        #F97316;
    --dark:           #9A3412;
    --bg:             #FEF3E2;
    --card-bg:        #FFFFFF;
    --text-primary:   #1C1917;
    --text-secondary: #78716C;
    --border-radius:  8px;
    --font:           'Inter', sans-serif;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    background: var(--bg);
    font-family: var(--font);
    color: var(--text-primary);
    padding: 20px;
    overflow-y: auto;
    overflow-x: hidden;
}}

body::-webkit-scrollbar {{
    display: none;
}}
.filter-bar {{
    display: flex;
    align-items: flex-start;
    gap: 16px;
    flex-wrap: wrap;
    background: var(--card-bg);
    padding: 8px 10px;
    border-radius: var(--border-radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}}
.f-item {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
}}
.f-label {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
}}
select {{
    padding: 8px 12px;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    font-family: var(--font);
    font-size: 13px;
    color: var(--text-primary);
    background: #fff;
    outline: none;
    cursor: pointer;
    width: 180px;
}}
select:focus {{ border-color: var(--primary); }}

.slider-wrap {{
    position: relative;
    height: 20px;
    display: flex;
    align-items: center;
    min-width: 160px;
}}
.slider-track {{
    position: absolute;
    left: 0; right: 0;
    height: 4px;
    border-radius: 999px;
    background: #E5E7EB;
    pointer-events: none;
}}
.slider-wrap input[type=range] {{
    position: absolute;
    width: 100%;
    pointer-events: none;
    background: transparent;
    appearance: none;
    -webkit-appearance: none;
    margin: 0;
}}
.slider-wrap input[type=range]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 18px; height: 18px;
    border-radius: 50%;
    background: #fff;
    border: 2.5px solid var(--primary);
    box-shadow: 0 1px 4px rgba(249,115,22,0.35);
    cursor: grab;
    pointer-events: auto;
    transition: box-shadow .15s;
}}
.slider-wrap input[type=range]::-webkit-slider-thumb:hover {{
    box-shadow: 0 2px 8px rgba(249,115,22,0.55);
}}
.slider-wrap input[type=range]::-moz-range-thumb {{
    width: 18px; height: 18px;
    border-radius: 50%;
    background: #fff;
    border: 2.5px solid var(--primary);
    cursor: grab;
    pointer-events: auto;
}}
.slider-vals {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    margin-top: 5px;
}}

.toggle-group {{
    display: flex;
    gap: 8px;
    align-items: center;
    cursor: pointer;
    padding-bottom: 2px;
}}
.toggle-switch {{
    position: relative;
    width: 36px; height: 20px;
    background: #E5E7EB;
    border-radius: 20px;
    transition: background .25s;
    flex-shrink: 0;
}}
.toggle-knob {{
    position: absolute;
    top: 2px; left: 2px;
    width: 16px; height: 16px;
    background: #fff;
    border-radius: 50%;
    transition: transform .25s;
}}
.toggle-checkbox {{ display: none; }}
.toggle-checkbox:checked + .toggle-switch {{ background: var(--primary); }}
.toggle-checkbox:checked + .toggle-switch .toggle-knob {{ transform: translateX(16px); }}
.toggle-lbl {{ font-size: 13px; font-weight: 500; white-space: nowrap; }}

.mode-divider {{
    width: 1px;
    height: 28px;
    background: #F3E8D8;
    align-self: center;
    flex-shrink: 0;
}}
.mode-pill {{
    display: inline-flex;
    gap: 4px;
    background: #F3E8D8;
    border-radius: 20px;
    padding: 3px;
    flex-shrink: 0;
    align-self: center;
}}
.mode-opt {{
    padding: 3px 12px;
    font: 600 11px var(--font);
    color: var(--text-secondary);
    background: transparent;
    border-radius: 20px;
    cursor: pointer;
    user-select: none;
    transition: background .15s, color .15s;
}}
.mode-opt.active {{
    background: var(--primary);
    color: #fff;
}}
.kpi-row {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}}
.kpi-card {{
    background: var(--card-bg);
    border-left: 4px solid var(--primary);
    border-radius: var(--border-radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    overflow: hidden;
}}
.kpi-card.accent {{
    border-left-color: var(--dark);
    background: linear-gradient(135deg, #FFF7ED 0%, #FFFFFF 100%);
}}
.kpi-title {{
    font-size: 11px;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.kpi-value {{
    font-size: 26px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.kpi-sub {{
    font-size: 12px;
    color: #9CA3AF;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

#row-charts {{
    display: flex;
    flex-direction: row;
    gap: 12px;
    height: 420px;
}}
.chart-card {{
    background: var(--card-bg);
    border-radius: var(--border-radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-width: 0;
}}
.chart-card.left  {{ flex: 0 0 calc(55% - 6px); }}
.chart-card.right {{ flex: 0 0 calc(45% - 6px); }}
.chart-title {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 4px 4px 8px 4px;
}}
.chart-card canvas {{
    flex: 1;
    width: 100%;
    min-height: 0;
    display: block;
}}
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

    <div class="mode-divider"></div>
    <div class="mode-pill" id="modePill">
        <div class="mode-opt active" data-mode="rating">Theo Rating</div>
        <div class="mode-opt"        data-mode="reviews">Theo Reviews</div>
    </div>
    <div class="mode-divider"></div>

    <div class="f-item">
        <span class="f-label">Khoảng Rating (★)</span>
        <div class="slider-wrap" style="min-width:160px">
            <div id="rating_track" class="slider-track"></div>
            <input type="range" id="rating_min" min="1" max="5" step="0.1" value="1"
                   oninput="updateSlider('rating'); applyFilters()">
            <input type="range" id="rating_max" min="1" max="5" step="0.1" value="5"
                   oninput="updateSlider('rating'); applyFilters()">
        </div>
        <div class="slider-vals">
            <span id="rating_val_min">★1.0</span>
            <span id="rating_val_max">★5.0</span>
        </div>
    </div>

    <div class="f-item">
        <span class="f-label">Số Reviews</span>
        <div class="slider-wrap" style="min-width:180px">
            <div id="reviews_track" class="slider-track"></div>
            <input type="range" id="reviews_min" min="0" max="500000" step="500" value="0"
                   oninput="updateSlider('reviews'); applyFilters()">
            <input type="range" id="reviews_max" min="0" max="500000" step="500" value="500000"
                   oninput="updateSlider('reviews'); applyFilters()">
        </div>
        <div class="slider-vals">
            <span id="reviews_val_min">0</span>
            <span id="reviews_val_max">500k</span>
        </div>
    </div>

    <div class="f-item">
        <span class="f-label">Khoảng Giá ($)</span>
        <div class="slider-wrap" style="min-width:180px">
            <div id="price_track" class="slider-track"></div>
            <input type="range" id="price_min" min="0" max="3400" step="1" value="0"
                   oninput="updateSlider('price'); applyFilters()">
            <input type="range" id="price_max" min="0" max="3400" step="1" value="3400"
                   oninput="updateSlider('price'); applyFilters()">
        </div>
        <div class="slider-vals">
            <span id="price_val_min">$0</span>
            <span id="price_val_max">$3,400</span>
        </div>
    </div>

    <div class="f-item">
        <span class="f-label">&nbsp;</span>
        <label class="toggle-group">
            <input type="checkbox" id="chkSales" class="toggle-checkbox" onchange="applyFilters()">
            <div class="toggle-switch"><div class="toggle-knob"></div></div>
            <span class="toggle-lbl">Có dữ liệu doanh số</span>
        </label>
    </div>

</div>

<div class="kpi-row">

    <div class="kpi-card">
        <div class="kpi-title">Rating Trung Bình</div>
        <div class="kpi-value" id="kpi_rating">0★</div>
        <div class="kpi-sub"  id="kpi_rating_sub">–</div>
    </div>

    <div class="kpi-card accent">
        <div class="kpi-title">Doanh Số TB - Rating ≥ 4.5</div>
        <div class="kpi-value" id="kpi_sales_hi">–</div>
        <div class="kpi-sub"  id="kpi_sales_hi_sub">So với rating &lt; 4.5</div>
    </div>

    <div class="kpi-card accent">
        <div class="kpi-title">Giá TB - Rating ≥ 4.5</div>
        <div class="kpi-value" id="kpi_price_hi_rating">–</div>
        <div class="kpi-sub"  id="kpi_price_hi_rating_sub">So với rating &lt; 4.5</div>
    </div>

    <div class="kpi-card">
        <div class="kpi-title">Doanh Số TB - Reviews Top 25%</div>
        <div class="kpi-value" id="kpi_sales_top_reviews">–</div>
        <div class="kpi-sub"  id="kpi_sales_top_reviews_sub">So với 75% còn lại</div>
    </div>

    <div class="kpi-card">
        <div class="kpi-title">Giá TB - Reviews Top 25%</div>
        <div class="kpi-value" id="kpi_price_top">–</div>
        <div class="kpi-sub"  id="kpi_price_top_sub">So với 75% còn lại</div>
    </div>

</div>

<div id="chartTooltip" style="position:fixed; background:#1C1917; color:#fff; padding:6px 10px; border-radius:6px; font:12px Inter, sans-serif; pointer-events:none; opacity:0; transition:opacity 0.15s; z-index:9999; line-height:1.6; white-space:pre-wrap;"></div>

<div id="row-charts">
    <div class="chart-card left">
        <div class="chart-title" id="comboTitle">Doanh số &amp; Giá TB theo nhóm Rating</div>
        <canvas id="canvasCombo"></canvas>
    </div>
    <div class="chart-card right">
        <div class="chart-title">Mối quan hệ giữa Rating và Reviews</div>
        <canvas id="canvasScatter"></canvas>
    </div>
</div>

<script>
const RAW_DATA = {data_json_str};

const tooltip = document.getElementById('chartTooltip');
function showTooltip(e, text) {{
    tooltip.textContent = text;
    tooltip.style.opacity = '1';
    let tx = e.clientX + 12;
    let ty = e.clientY + 12;
    if (tx + tooltip.offsetWidth > window.innerWidth) {{
        tx = e.clientX - tooltip.offsetWidth - 12;
    }}
    tooltip.style.left = tx + 'px';
    tooltip.style.top = ty + 'px';
}}
function hideTooltip() {{
    tooltip.style.opacity = '0';
}}
const fmtN = n => new Intl.NumberFormat('en-US').format(Math.round(n));
const fmtF = (n, d=2) => Number(n).toFixed(d);
const fmtK = n => n >= 1000 ? (n/1000).toFixed(0)+'k' : fmtN(n);

function median(arr) {{
    if (!arr.length) return 0;
    const s = [...arr].sort((a,b) => a-b);
    const m = Math.floor(s.length / 2);
    return s.length % 2 === 0 ? (s[m-1]+s[m])/2 : s[m];
}}
function mean(arr) {{
    return arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
}}
function quantile(arr, q) {{
    if (!arr.length) return 0;
    const s = [...arr].sort((a,b)=>a-b);
    const pos = (s.length - 1) * q;
    const lo  = Math.floor(pos);
    const hi  = Math.ceil(pos);
    return s[lo] + (s[hi] - s[lo]) * (pos - lo);
}}

const SLIDER_CFG = {{
    rating:  {{ min: 1, max: 5,      fmt: v => '★'+Number(v).toFixed(1) }},
    reviews: {{ min: 0, max: 500000, fmt: v => fmtK(Number(v)) }},
    price:   {{ min: 0, max: 3400,   fmt: v => '$'+fmtN(Number(v)) }},
}};

function updateSlider(name) {{
    const minEl  = document.getElementById(name+'_min');
    const maxEl  = document.getElementById(name+'_max');
    const track  = document.getElementById(name+'_track');
    const valMin = document.getElementById(name+'_val_min');
    const valMax = document.getElementById(name+'_val_max');
    const cfg    = SLIDER_CFG[name];

    let lo = parseFloat(minEl.value);
    let hi = parseFloat(maxEl.value);
    const gap = name === 'rating' ? 0.1 : (name === 'reviews' ? 500 : 1);

    if (lo > hi - gap) {{
        if (document.activeElement === minEl) {{ lo = hi - gap; minEl.value = lo; }}
        else                                  {{ hi = lo + gap; maxEl.value = hi; }}
    }}

    const range = parseFloat(minEl.max) - parseFloat(minEl.min);
    const pLo   = ((lo - parseFloat(minEl.min)) / range) * 100;
    const pHi   = ((hi - parseFloat(minEl.min)) / range) * 100;
    track.style.background =
        `linear-gradient(to right,#E5E7EB ${{pLo}}%,#F97316 ${{pLo}}%,#F97316 ${{pHi}}%,#E5E7EB ${{pHi}}%)`;
    valMin.textContent = cfg.fmt(lo);
    valMax.textContent = cfg.fmt(hi);
}}

function initSliders() {{
    let maxRev = 0, maxPrice = 0;
    RAW_DATA.forEach(d => {{
        if (d.reviews       > maxRev)   maxRev   = d.reviews;
        if (d.current_price > maxPrice) maxPrice = d.current_price;
    }});
    maxRev   = Math.ceil(maxRev   / 500) * 500  || 500000;
    maxPrice = Math.ceil(maxPrice / 100) * 100  || 3400;

    ['reviews_min','reviews_max'].forEach(id => {{
        document.getElementById(id).max   = maxRev;
        document.getElementById(id).value = id.endsWith('min') ? 0 : maxRev;
    }});
    ['price_min','price_max'].forEach(id => {{
        document.getElementById(id).max   = maxPrice;
        document.getElementById(id).value = id.endsWith('min') ? 0 : maxPrice;
    }});

    SLIDER_CFG.reviews.max = maxRev;
    SLIDER_CFG.price.max   = maxPrice;

    ['rating','reviews','price'].forEach(updateSlider);
}}

function initDropdown() {{
    const cats = [...new Set(RAW_DATA.map(d => d.crawl_category)
        .filter(c => c && c !== 'Không rõ' && c !== 'Khác'))].sort();
    const sel = document.getElementById('selCategory');
    cats.forEach(c => {{
        const o = document.createElement('option');
        o.value = o.textContent = c;
        sel.appendChild(o);
    }});
}}

let currentMode = 'rating';
function initModeToggle() {{
    document.querySelectorAll('#modePill .mode-opt').forEach(opt => {{
        opt.addEventListener('click', () => {{
            const m = opt.getAttribute('data-mode');
            if (m === currentMode) return;
            currentMode = m;
            document.querySelectorAll('#modePill .mode-opt').forEach(o => o.classList.toggle('active', o === opt));
            document.getElementById('comboTitle').textContent =
                m === 'rating'
                    ? 'Doanh số & Giá TB theo nhóm Rating'
                    : 'Doanh số & Giá TB theo nhóm Reviews';
            drawComboChart(currentMode, getFiltered());
        }});
    }});
}}

function getFiltered() {{
    const cat       = document.getElementById('selCategory').value;
    const rLo       = parseFloat(document.getElementById('rating_min').value);
    const rHi       = parseFloat(document.getElementById('rating_max').value);
    const revLo     = parseFloat(document.getElementById('reviews_min').value);
    const revHi     = parseFloat(document.getElementById('reviews_max').value);
    const pLo       = parseFloat(document.getElementById('price_min').value);
    const pHi       = parseFloat(document.getElementById('price_max').value);
    const salesOnly = document.getElementById('chkSales').checked;

    return RAW_DATA.filter(d => {{
        if (cat !== 'ALL' && d.crawl_category !== cat) return false;
        if (d.rating        < rLo  || d.rating        > rHi)  return false;
        if (d.reviews       < revLo|| d.reviews       > revHi) return false;
        if (d.current_price < pLo  || d.current_price > pHi)  return false;
        if (salesOnly && d.sales_volume_num <= 0)               return false;
        return true;
    }});
}}

function updateKPIs(data) {{
    const ratings  = data.map(d => d.rating).filter(r => r > 0);
    const avgRat   = mean(ratings);
    const totalRev = data.reduce((a,b) => a + (b.reviews||0), 0);
    document.getElementById('kpi_rating').textContent     = fmtF(avgRat) + '★';
    document.getElementById('kpi_rating_sub').textContent = `từ ${{fmtN(totalRev)}} lượt đánh giá`;

    const hiSales = data.filter(d => d.rating >= 4.5 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const loSales = data.filter(d => d.rating <  4.5 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const avgHiS  = mean(hiSales);
    const avgLoS  = mean(loSales);
    const salesEl  = document.getElementById('kpi_sales_hi');
    const salesSub = document.getElementById('kpi_sales_hi_sub');
    if (avgHiS > 0) {{
        salesEl.textContent = fmtN(avgHiS) + ' đơn';
        if (avgLoS > 0) {{
            const pct = (avgHiS - avgLoS) / avgLoS * 100;
            salesSub.textContent = `${{pct >= 0 ? '+' : ''}}${{fmtF(pct,1)}}% so với rating < 4.5`;
        }} else {{
            salesSub.textContent = 'TB doanh số nhóm rating ≥ 4.5';
        }}
    }} else {{
        salesEl.textContent  = 'N/A';
        salesSub.textContent = 'Chưa đủ dữ liệu doanh số';
    }}

    const hiPrices = data.filter(d => d.rating >= 4.5 && d.current_price > 0).map(d => d.current_price);
    const loPrices = data.filter(d => d.rating <  4.5 && d.current_price > 0).map(d => d.current_price);
    const avgHiP   = mean(hiPrices);
    const avgLoP   = mean(loPrices);
    const priceHiEl  = document.getElementById('kpi_price_hi_rating');
    const priceHiSub = document.getElementById('kpi_price_hi_rating_sub');
    if (avgHiP > 0) {{
        priceHiEl.textContent = '$' + fmtF(avgHiP, 2);
        if (avgLoP > 0) {{
            const diff = avgHiP - avgLoP;
            priceHiSub.textContent = `${{diff >= 0 ? '+' : '-'}}$${{fmtF(Math.abs(diff),2)}} so với rating < 4.5`;
        }} else {{
            priceHiSub.textContent = 'Giá TB nhóm rating ≥ 4.5';
        }}
    }} else {{
        priceHiEl.textContent  = 'N/A';
        priceHiSub.textContent = 'Chưa đủ dữ liệu giá';
    }}

    const allRevs     = data.map(d => d.reviews).filter(r => r > 0);
    const q75         = quantile(allRevs, 0.75);
    const topSales    = data.filter(d => d.reviews >= q75 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const botSales    = data.filter(d => d.reviews <  q75 && d.sales_volume_num > 0).map(d => d.sales_volume_num);
    const avgTopS     = mean(topSales);
    const avgBotS     = mean(botSales);
    const salesTopEl  = document.getElementById('kpi_sales_top_reviews');
    const salesTopSub = document.getElementById('kpi_sales_top_reviews_sub');
    if (avgTopS > 0) {{
        salesTopEl.textContent = fmtN(avgTopS) + ' đơn';
        if (avgBotS > 0) {{
            const pct = (avgTopS - avgBotS) / avgBotS * 100;
            salesTopSub.textContent = `${{pct >= 0 ? '+' : ''}}${{fmtF(pct,1)}}% so với 75% còn lại`;
        }} else {{
            salesTopSub.textContent = 'TB doanh số nhóm reviews top 25%';
        }}
    }} else {{
        salesTopEl.textContent  = 'N/A';
        salesTopSub.textContent = 'Chưa đủ dữ liệu doanh số';
    }}

    const topPrices = data.filter(d => d.reviews >= q75 && d.current_price > 0).map(d => d.current_price);
    const botPrices = data.filter(d => d.reviews <  q75 && d.current_price > 0).map(d => d.current_price);
    const avgTopP   = mean(topPrices);
    const avgBotP   = mean(botPrices);
    const priceEl   = document.getElementById('kpi_price_top');
    const priceSub  = document.getElementById('kpi_price_top_sub');
    if (avgTopP > 0) {{
        priceEl.textContent = '$' + fmtF(avgTopP, 2);
        if (avgBotP > 0) {{
            const diff = avgTopP - avgBotP;
            priceSub.textContent = `${{diff >= 0 ? '+' : '-'}}$${{fmtF(Math.abs(diff),2)}} so với 75% còn lại`;
        }} else {{
            priceSub.textContent = 'Giá TB nhóm reviews top 25%';
        }}
    }} else {{
        priceEl.textContent  = 'N/A';
        priceSub.textContent = 'Chưa đủ dữ liệu giá';
    }}
}}

function buildComboGroups(mode, data) {{
    if (mode === 'rating') {{
        const defs = [
            {{ lbl: '<3.5',    f: r => r < 3.5 }},
            {{ lbl: '3.5-3.9', f: r => r >= 3.5 && r <= 3.9 }},
            {{ lbl: '4.0-4.4', f: r => r >= 4.0 && r <= 4.4 }},
            {{ lbl: '4.5-4.7', f: r => r >= 4.5 && r <= 4.7 }},
            {{ lbl: '4.8-5.0', f: r => r >= 4.8 }}
        ];
        return defs.map(g => {{
            const fData  = data.filter(d => g.f(d.rating));
            const sales  = fData.filter(d => d.sales_volume_num > 0).map(d => d.sales_volume_num);
            const prices = fData.filter(d => d.current_price > 0).map(d => d.current_price);
            return {{ lbl: g.lbl, s: mean(sales), p: mean(prices), sCount: sales.length, pCount: prices.length }};
        }});
    }}
    const revs = data.map(d => d.reviews || 0);
    const q25 = quantile(revs, 0.25);
    const q50 = quantile(revs, 0.50);
    const q75 = quantile(revs, 0.75);
    const buckets = [
        {{ lbl: 'Q1 (ít nhất)', ds: [], ps: [] }},
        {{ lbl: 'Q2',           ds: [], ps: [] }},
        {{ lbl: 'Q3',           ds: [], ps: [] }},
        {{ lbl: 'Q4 (top 25%)', ds: [], ps: [] }}
    ];
    data.forEach(d => {{
        const r = d.reviews || 0;
        let idx = 0;
        if (r >= q75) idx = 3;
        else if (r >= q50) idx = 2;
        else if (r >= q25) idx = 1;
        if (d.sales_volume_num > 0) buckets[idx].ds.push(d.sales_volume_num);
        if (d.current_price   > 0) buckets[idx].ps.push(d.current_price);
    }});
    return buckets.map(g => ({{
        lbl: g.lbl,
        s: mean(g.ds), p: mean(g.ps),
        sCount: g.ds.length, pCount: g.ps.length
    }}));
}}

function drawComboChart(mode, data) {{
    const canvas = document.getElementById('canvasCombo');
    const ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    canvas.width  = canvas.offsetWidth  * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    ctx.clearRect(0, 0, cW, cH);
    if (!data || !data.length) return;

    const stats = buildComboGroups(mode, data);
    const maxS = Math.max(1, ...stats.map(s => s.s)) * 1.15;
    const maxP = Math.max(1, ...stats.map(s => s.p)) * 1.15;

    const pad = {{ t: 50, r: 60, b: 50, l: 60 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;
    const gap = w / stats.length;

    ctx.fillStyle = 'rgba(249, 115, 22, 0.08)';
    if (mode === 'rating') {{
        ctx.fillRect(pad.l + 3 * gap, pad.t, 2 * gap, h);
    }} else {{
        ctx.fillRect(pad.l + 3 * gap, pad.t, gap, h);
    }}

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= 5; i++) {{
        const y = pad.t + h - (i / 5) * h;
        ctx.textAlign = 'right';
        ctx.fillText(fmtK(maxS * i / 5), pad.l - 8, y);
        ctx.textAlign = 'left';
        ctx.fillText('$' + fmtN(maxP * i / 5), pad.l + w + 8, y);

        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + w, y);
        ctx.strokeStyle = '#E5E7EB';
        ctx.stroke();
    }}

    const barW = Math.min(56, gap * 0.42);
    stats.forEach((d, i) => {{
        const barH = (d.s / maxS) * h;
        const x = pad.l + i * gap + gap / 2 - barW / 2;
        const y = pad.t + h - barH;
        ctx.fillStyle = '#F97316';
        ctx.fillRect(x, y, barW, barH);

        ctx.fillStyle = '#78716C';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(d.lbl, pad.l + i * gap + gap / 2, pad.t + h + 8);
    }});

    ctx.beginPath();
    ctx.strokeStyle = '#9A3412';
    ctx.lineWidth = 2;
    stats.forEach((d, i) => {{
        const x = pad.l + i * gap + gap / 2;
        const y = pad.t + h - (d.p / maxP) * h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }});
    ctx.stroke();

    ctx.font = '12px Inter';
    stats.forEach((d, i) => {{
        const x = pad.l + i * gap + gap / 2;
        const y = pad.t + h - (d.p / maxP) * h;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.strokeStyle = '#9A3412';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = '#9A3412';
        ctx.textAlign = 'center';
        if (y - pad.t < 22) {{
            ctx.textBaseline = 'top';
            ctx.fillText('$' + fmtF(d.p), x, y + 8);
        }} else {{
            ctx.textBaseline = 'bottom';
            ctx.fillText('$' + fmtF(d.p), x, y - 8);
        }}
    }});

    const lx = cW / 2;
    const ly = 18;
    ctx.fillStyle = '#F97316';
    ctx.fillRect(lx - 90, ly - 5, 12, 10);
    ctx.fillStyle = '#1C1917';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.font = '12px Inter';
    ctx.fillText('Doanh số TB', lx - 72, ly);

    ctx.beginPath();
    ctx.strokeStyle = '#9A3412';
    ctx.lineWidth = 2;
    ctx.moveTo(lx + 14, ly);
    ctx.lineTo(lx + 34, ly);
    ctx.stroke();
    ctx.beginPath();
    ctx.fillStyle = '#9A3412';
    ctx.arc(lx + 24, ly, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1C1917';
    ctx.fillText('Giá TB ($)', lx + 40, ly);

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(mode === 'rating' ? 'Nhóm Rating' : 'Nhóm Reviews (Quartile)',
                 pad.l + w / 2, pad.t + h + 28);

    ctx.save();
    ctx.translate(14, pad.t + h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Doanh số', 0, 0);
    ctx.restore();

    ctx.save();
    ctx.translate(cW - 14, pad.t + h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Giá ($)', 0, 0);
    ctx.restore();

    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        for (let i = 0; i < stats.length; i++) {{
            const px = pad.l + i * gap + gap / 2;
            const py = pad.t + h - (stats[i].p / maxP) * h;
            if (Math.hypot(mx - px, my - py) <= 12) {{
                showTooltip(e, `Nhóm: ${{stats[i].lbl}}\nGiá TB: $${{fmtF(stats[i].p)}}\nSố SP: ${{fmtN(stats[i].pCount)}}`);
                return;
            }}
        }}
        for (let i = 0; i < stats.length; i++) {{
            const barH = (stats[i].s / maxS) * h;
            const bx = pad.l + i * gap + gap / 2 - barW / 2;
            const by = pad.t + h - barH;
            if (mx >= bx && mx <= bx + barW && my >= by && my <= pad.t + h) {{
                showTooltip(e, `Nhóm: ${{stats[i].lbl}}\nDoanh số TB: ${{fmtN(stats[i].s)}} đơn\nSố SP có DS: ${{fmtN(stats[i].sCount)}}`);
                return;
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

function drawScatterPlot(data) {{
    const canvas = document.getElementById('canvasScatter');
    const ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    canvas.width  = canvas.offsetWidth  * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    ctx.clearRect(0, 0, cW, cH);
    if (!data || !data.length) return;

    const valid = data.filter(d => d.rating >= 1.0 && d.reviews > 0);
    if (!valid.length) return;

    const pad = {{ t: 50, r: 20, b: 50, l: 60 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;

    const minX = 2.5, maxX = 5.0;
    const getX = r => pad.l + ((Math.max(minX, Math.min(maxX, r)) - minX) / (maxX - minX)) * w;

    const revs = valid.map(d => d.reviews);
    const minRev = Math.min(...revs);
    const maxRev = Math.max(...revs);
    const minLog = Math.floor(Math.log10(Math.max(1, minRev)));
    const maxLog = Math.ceil(Math.log10(maxRev));
    const getY = rev => pad.t + h - ((Math.log10(rev) - minLog) / (maxLog - minLog || 1)) * h;

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = minLog; i <= maxLog; i++) {{
        const y = pad.t + h - ((i - minLog) / (maxLog - minLog || 1)) * h;
        ctx.fillText(fmtK(Math.pow(10, i)), pad.l - 6, y);

        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + w, y);
        ctx.strokeStyle = '#E5E7EB';
        ctx.stroke();
    }}

    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let r10 = 25; r10 <= 50; r10 += 5) {{
        const r = r10 / 10;
        const x = getX(r);
        ctx.fillText(r.toFixed(1), x, pad.t + h + 6);
    }}

    const x45 = getX(4.5);
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.moveTo(x45, pad.t);
    ctx.lineTo(x45, pad.t + h);
    ctx.strokeStyle = 'rgba(154, 52, 18, 0.4)';
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#9A3412';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.font = '12px Inter';
    ctx.fillText('≥ 4.5', x45, pad.t - 4);

    const getColor = sv => {{
        if (!sv || sv === 0) return 'rgba(209, 213, 219, 0.5)';
        if (sv <= 500) return 'rgba(249, 180, 100, 0.7)';
        if (sv <= 2000) return 'rgba(249, 115, 22, 0.7)';
        return 'rgba(154, 52, 18, 0.85)';
    }};

    ctx.save();
    ctx.beginPath();
    ctx.rect(pad.l, pad.t - 5, w, h + 10);
    ctx.clip();
    valid.forEach(d => {{
        const x = getX(d.rating);
        const y = getY(d.reviews);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = getColor(d.sales_volume_num);
        ctx.fill();
    }});
    ctx.restore();

    const legends = [
        {{ l: 'Không có DS', c: 'rgba(209, 213, 219, 0.5)' }},
        {{ l: 'DS Thấp',     c: 'rgba(249, 180, 100, 0.7)' }},
        {{ l: 'DS TB',       c: 'rgba(249, 115, 22, 0.7)' }},
        {{ l: 'DS Cao',      c: 'rgba(154, 52, 18, 0.85)' }}
    ];
    let lx = pad.l + w - 4;
    const ly = pad.t - 28;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.font = '11px Inter';
    [...legends].reverse().forEach(lg => {{
        ctx.fillStyle = '#1C1917';
        ctx.fillText(lg.l, lx, ly);
        const textW = ctx.measureText(lg.l).width;
        ctx.fillStyle = lg.c;
        ctx.beginPath();
        ctx.arc(lx - textW - 6, ly, 4, 0, Math.PI * 2);
        ctx.fill();
        lx -= (textW + 20);
    }});

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('Rating (★)', pad.l + w / 2, pad.t + h + 26);

    ctx.save();
    ctx.translate(14, pad.t + h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Số Reviews (log)', 0, 0);
    ctx.restore();

    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        for (let i = 0; i < valid.length; i++) {{
            const d = valid[i];
            const px = getX(d.rating);
            const py = getY(d.reviews);
            if (Math.hypot(mx - px, my - py) <= 8) {{
                showTooltip(e, `Rating: ${{d.rating}}★\nReviews: ${{fmtN(d.reviews)}}\nDoanh số: ${{fmtN(d.sales_volume_num || 0)}} đơn`);
                return;
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

function applyFilters() {{
    const filtered = getFiltered();
    updateKPIs(filtered);
    drawComboChart(currentMode, filtered);
    drawScatterPlot(filtered);
}}

window.addEventListener('resize', () => {{
    applyFilters();
}});

document.addEventListener('DOMContentLoaded', () => {{
    initDropdown();
    initSliders();
    initModeToggle();
    applyFilters();
}});
</script>
</body>
</html>"""

    components.html(html_code, height=648, scrolling=False)
