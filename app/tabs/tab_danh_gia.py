import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render(df: pd.DataFrame):
    # ------------------------------------------------------------------ #
    #  Chuẩn bị dữ liệu
    # ------------------------------------------------------------------ #
    data = df.copy()

    # ══════════════════════════════════════════════════════════════
    # 1. TIỀN XỬ LÝ DỮ LIỆU & MAPPING DANH MỤC
    # ══════════════════════════════════════════════════════════════
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

    data["current_price"]    = pd.to_numeric(data.get("price", data.get("current_price", 0)), errors="coerce").fillna(0.0)
    data["original_price"]   = pd.to_numeric(data.get("original_price", 0), errors="coerce").fillna(0.0)
    data["rating"]           = pd.to_numeric(data.get("rating", 0), errors="coerce").fillna(0.0)
    data["reviews"]          = pd.to_numeric(data.get("reviews", 0), errors="coerce").fillna(0)
    data["sales_volume_num"] = pd.to_numeric(data.get("sales_volume_num", 0), errors="coerce").fillna(0)

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

    # ------------------------------------------------------------------ #
    #  HTML / CSS / JS
    # ------------------------------------------------------------------ #
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

/* ── Filter bar ───────────────────────────────────────────── */
.filter-bar {{
    display: flex;
    align-items: flex-start;
    gap: 24px;
    flex-wrap: wrap;
    background: var(--card-bg);
    padding: 16px 20px;
    border-radius: var(--border-radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 24px;
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

/* ── KPI row — 5 cards ────────────────────────────────────── */
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
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    overflow: hidden;
}}
/* 2 card phân tích MT1 & MT2 nổi bật hơn */
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



/* ── Charts ───────────────────────────────────────────────── */
.chart-container {{
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
}}
.chart-box {{
    flex: 1;
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    min-width: 0;
}}
.chart-title {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-primary);
    text-align: center;
}}
canvas {{
    width: 100%;
    height: 300px;
    display: block;
}}

/* Table Styles */
.top-table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
.top-table th {{ background: #FEF3E2; padding: 8px; border-bottom: 1px solid #F3E8D8; font-weight: 600; cursor: pointer; white-space: nowrap; position: sticky; top: 0; z-index: 10; user-select: none; }}
.top-table th.no-sort {{ cursor: default; }}
.top-table td {{ padding: 8px; border-bottom: 1px solid #F3E8D8; }}
.top-table tbody tr:hover {{ background: #FFF7ED; }}
.top-table .sort-icon {{ display: inline-block; width: 12px; margin-left: 4px; color: #F97316; }}
</style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════
     FILTER BAR
═══════════════════════════════════════════════════════════ -->
<div class="filter-bar">

    <div class="f-item">
        <span class="f-label">Danh mục</span>
        <select id="selCategory" onchange="applyFilters()">
            <option value="ALL">Tất cả</option>
        </select>
    </div>

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

<!-- ═══════════════════════════════════════════════════════════
     KPI CARDS — 5 cards
     [1] Rating TB           → baseline bối cảnh
     [2] Trung vị Reviews    → ngưỡng phân chia Q (MT2)
     [3] % Rating ≥ 4.5      → mức cạnh tranh thị trường
     [4] DS TB Rating ≥ 4.5  → tổng quan MT1  (accent)
     [5] Giá TB Top 25%      → tổng quan MT2  (accent)
═══════════════════════════════════════════════════════════ -->
<div class="kpi-row">

    <!-- Card 1: Rating TB -->
    <div class="kpi-card">
        <div class="kpi-title">Rating Trung Bình</div>
        <div class="kpi-value" id="kpi_rating">0★</div>
        <div class="kpi-sub"  id="kpi_rating_sub">–</div>
    </div>

    <!-- Card 2: Trung vị Reviews -->
    <div class="kpi-card">
        <div class="kpi-title">Trung Vị Reviews</div>
        <div class="kpi-value" id="kpi_med_reviews">0</div>
        <div class="kpi-sub"  id="kpi_med_reviews_sub">Ngưỡng phân chia ít / nhiều</div>
    </div>

    <!-- Card 3: % Rating ≥ 4.5 -->
    <div class="kpi-card">
        <div class="kpi-title">% Rating ≥ 4.5</div>
        <div class="kpi-value" id="kpi_high_rating">0%</div>
        <div class="kpi-sub"  id="kpi_high_rating_sub">–</div>
    </div>

    <!-- Card 4: Doanh số TB - Rating ≥ 4.5  (MT1) -->
    <div class="kpi-card accent">
        <div class="kpi-title">Doanh số TB - Rating ≥ 4.5</div>
        <div class="kpi-value" id="kpi_sales_hi">–</div>
        <div class="kpi-sub"  id="kpi_sales_hi_sub">So với rating &lt; 4.5</div>
    </div>

    <!-- Card 5: Giá TB - Reviews Top 25%  (MT2) -->
    <div class="kpi-card accent">
        <div class="kpi-title">Giá TB - Reviews Top 25%</div>
        <div class="kpi-value" id="kpi_price_top">–</div>
        <div class="kpi-sub"  id="kpi_price_top_sub">So với 75% còn lại</div>
    </div>

</div>




<div id="chartTooltip" style="position:fixed; background:#1C1917; color:#fff; padding:6px 10px; border-radius:6px; font:12px Inter, sans-serif; pointer-events:none; opacity:0; transition:opacity 0.15s; z-index:9999; line-height:1.6; white-space:pre-wrap;"></div>

<div class="chart-container">
    <div class="chart-box" style="flex: 6; max-height: 420px; overflow-y: auto; overflow-x: hidden; padding-right: 8px; padding-top: 0;">
        <div class="chart-title" style="position: sticky; top: 0; background: white; z-index: 11; padding: 16px 0 8px 0; margin-bottom: 0;">Top sản phẩm nổi bật</div>
        <table class="top-table" id="topTable">
            <thead>
                <tr>
                    <th class="no-sort">Sản phẩm</th>
                    <th data-sort="rating">Rating ★ <span class="sort-icon"></span></th>
                    <th data-sort="reviews" data-dir="desc">Reviews <span class="sort-icon">▼</span></th>
                    <th data-sort="current_price">Giá ($) <span class="sort-icon"></span></th>
                    <th data-sort="sales_volume_num">Doanh số <span class="sort-icon"></span></th>
                    <th class="no-sort">Danh mục</th>
                </tr>
            </thead>
            <tbody id="topBody"></tbody>
        </table>
    </div>
    <div class="chart-box" style="flex: 4;">
        <div class="chart-title">Mối quan hệ giữa Rating và Reviews</div>
        <canvas id="chart3"></canvas>
    </div>
</div>

<div class="chart-container">
    <div class="chart-box">
        <div class="chart-title">Phân bố Rating sản phẩm</div>
        <canvas id="chart1"></canvas>
    </div>
    <div class="chart-box">
        <div class="chart-title">Doanh số & Giá TB theo nhóm Rating</div>
        <canvas id="chart2"></canvas>
    </div>
</div>

<div class="chart-container" style="height: 420px;">
    <div class="chart-box" style="flex: 4.5; display: flex; flex-direction: column;">
        <div class="chart-title">Doanh số & Giá TB theo nhóm Reviews</div>
        <canvas id="chart4" style="flex: 1; min-height: 0;"></canvas>
    </div>
    <div class="chart-box" style="flex: 3.5; display: flex; flex-direction: column;">
        <div class="chart-title">Top 5 danh mục có Giá TB theo Reviews</div>
        <canvas id="chart5" style="flex: 1; min-height: 0;"></canvas>
    </div>
    <div class="chart-box" style="flex: 2; display: flex; flex-direction: column;">
        <div class="chart-title" style="font-size: 13px;">Đóng góp Doanh số theo nhóm Reviews</div>
        <canvas id="chart6" style="flex: 1; min-height: 0;"></canvas>
    </div>
</div>

<script>
const RAW_DATA = {data_json_str};

/* ── helpers ─────────────────────────────────────────────── */
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

/* ── slider logic ─────────────────────────────────────────── */
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

/* ── init sliders từ data thực ───────────────────────────── */
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

/* ── init category dropdown ──────────────────────────────── */
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

/* ── filter ──────────────────────────────────────────────── */
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

/* ── KPI update ──────────────────────────────────────────── */
function updateKPIs(data) {{

    /* --- Card 1: Rating TB --- */
    const ratings  = data.map(d => d.rating).filter(r => r > 0);
    const avgRat   = mean(ratings);
    const totalRev = data.reduce((a,b) => a + (b.reviews||0), 0);
    document.getElementById('kpi_rating').textContent     = fmtF(avgRat) + '★';
    document.getElementById('kpi_rating_sub').textContent = `từ ${{fmtN(totalRev)}} lượt đánh giá`;

    /* --- Card 2: Trung vị Reviews --- */
    const revArr = data.map(d => d.reviews).filter(r => r > 0);
    const medRev = median(revArr);
    document.getElementById('kpi_med_reviews').textContent     = fmtN(medRev);
    document.getElementById('kpi_med_reviews_sub').textContent = 'Ngưỡng phân chia ít / nhiều';

    /* --- Card 3: % Rating ≥ 4.5 --- */
    const total   = data.length;
    const highCnt = data.filter(d => d.rating >= 4.5).length;
    const highPct = total ? (highCnt / total * 100) : 0;
    document.getElementById('kpi_high_rating').textContent     = fmtF(highPct, 1) + '%';
    document.getElementById('kpi_high_rating_sub').textContent = `${{fmtN(highCnt)}} / ${{fmtN(total)}} sản phẩm`;

    /* --- Card 4: DS TB — Rating ≥ 4.5  (MT1) --- */
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

    /* --- Card 5: Giá TB — Reviews Top 25%  (MT2) ---
         Ngưỡng Q3 (75th percentile) phân chia top 25%                       */
    const allRevs   = data.map(d => d.reviews).filter(r => r > 0);
    const q75       = quantile(allRevs, 0.75);
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

/* ── charts ──────────────────────────────────────────────── */
function drawChart1(data) {{
    const canvas = document.getElementById('chart1');
    const ctx = canvas.getContext('2d');
    
    const dpr = window.devicePixelRatio || 1;
    canvas.width  = canvas.offsetWidth  * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    
    ctx.clearRect(0, 0, cW, cH);
    if (!data || !data.length) return;

    const bins = new Array(20).fill(0);
    data.forEach(d => {{
        let r = d.rating;
        if (r < 1.0) r = 1.0;
        if (r > 5.0) r = 5.0;
        let idx = Math.floor((r - 1.0) / 0.2);
        if (idx >= 20) idx = 19;
        bins[idx]++;
    }});
    const maxCount = Math.max(...bins, 1);
    
    const pad = {{ t: 30, r: 20, b: 45, l: 55 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= 5; i++) {{
        const val = (maxCount / 5) * i;
        const y = pad.t + h - (h / 5) * i;
        ctx.fillText(fmtK(val), pad.l - 6, y);
        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + w, y);
        ctx.strokeStyle = '#E5E7EB';
        ctx.stroke();
    }}

    const barW = w / 20;
    for (let i = 0; i < 20; i++) {{
        const binVal = 1.0 + i * 0.2;
        const barH = (bins[i] / maxCount) * h;
        const x = pad.l + i * barW;
        const y = pad.t + h - barH;
        
        ctx.fillStyle = binVal >= 4.49 ? '#9A3412' : '#F97316';
        ctx.fillRect(x + 1, y, barW - 2, barH);
        
        if (i % 5 === 0 || i === 19) {{
            ctx.fillStyle = '#78716C';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText((i===19?'5.0':(1.0+i*0.2).toFixed(1)), x + barW/2, pad.t + h + 6);
        }}
    }}

    const x45 = pad.l + 17.5 * barW;
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.moveTo(x45, pad.t);
    ctx.lineTo(x45, pad.t + h);
    ctx.strokeStyle = '#9A3412';
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#9A3412';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.font = 'bold 13px Inter';
    ctx.fillText('≥ 4.5', x45, pad.t - 4);

    // Axis titles
    ctx.fillStyle = '#78716C';
    ctx.font = '13px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('Rating', pad.l + w/2, pad.t + h + 25);

    ctx.save();
    ctx.translate(15, pad.t + h/2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Số lượng', 0, 0);
    ctx.restore();

    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        if (x >= pad.l && x <= pad.l + w && y >= pad.t && y <= pad.t + h) {{
            const barW = w / 20;
            const idx = Math.floor((x - pad.l) / barW);
            if (idx >= 0 && idx < 20) {{
                const c = bins[idx];
                const min = (1.0 + idx * 0.2).toFixed(1);
                const max = (1.0 + (idx + 1) * 0.2).toFixed(1);
                showTooltip(e, `Rating: ${{min}} – ${{max}}\nSố sản phẩm: ${{fmtN(c)}}`);
                return;
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

function drawChart2(data) {{
    const canvas = document.getElementById('chart2');
    const ctx = canvas.getContext('2d');
    
    const dpr = window.devicePixelRatio || 1;
    canvas.width  = canvas.offsetWidth  * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    
    ctx.clearRect(0, 0, cW, cH);
    if (!data || !data.length) return;

    const groups = [
        {{ label: '<3.5',    f: r => r < 3.5 }},
        {{ label: '3.5-3.9', f: r => r >= 3.5 && r <= 3.9 }},
        {{ label: '4.0-4.4', f: r => r >= 4.0 && r <= 4.4 }},
        {{ label: '4.5-4.7', f: r => r >= 4.5 && r <= 4.7 }},
        {{ label: '4.8-5.0', f: r => r >= 4.8 }}
    ];
    const stats = groups.map(g => {{
        const fData = data.filter(d => g.f(d.rating));
        const sales = fData.filter(d => d.sales_volume_num > 0).map(d => d.sales_volume_num);
        const prices = fData.filter(d => d.current_price > 0).map(d => d.current_price);
        return {{ lbl: g.label, s: mean(sales), p: mean(prices) }};
    }});

    const maxS = Math.max(...stats.map(x => x.s), 1);
    const maxP = Math.max(...stats.map(x => x.p), 1);
    const pad = {{ t: 40, r: 55, b: 45, l: 55 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= 5; i++) {{
        const y = pad.t + h - (h / 5) * i;
        ctx.textAlign = 'right';
        ctx.fillText(fmtK(maxS / 5 * i), pad.l - 6, y);
        ctx.textAlign = 'left';
        ctx.fillText('$'+fmtN(maxP / 5 * i), pad.l + w + 6, y);

        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + w, y);
        ctx.strokeStyle = '#E5E7EB';
        ctx.stroke();
    }}

    const gap = w / groups.length;
    const barW = gap * 0.4;
    
    // Highlight rating >= 4.5
    ctx.fillStyle = 'rgba(249, 115, 22, 0.08)';
    const xStart = pad.l + 3 * gap;
    const xEnd = pad.l + 5 * gap;
    ctx.fillRect(xStart, pad.t, xEnd - xStart, h);

    // Bars
    ctx.fillStyle = '#F97316';
    stats.forEach((st, i) => {{
        const barH = (st.s / maxS) * h;
        const x = pad.l + i * gap + gap/2 - barW/2;
        const y = pad.t + h - barH;
        ctx.fillRect(x, y, barW, barH);
        
        ctx.fillStyle = '#78716C';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(st.lbl, pad.l + i * gap + gap/2, pad.t + h + 6);
        ctx.fillStyle = '#F97316';
    }});

    // Line
    ctx.beginPath();
    ctx.strokeStyle = '#9A3412';
    ctx.lineWidth = 2;
    stats.forEach((st, i) => {{
        const x = pad.l + i * gap + gap/2;
        const y = pad.t + h - (st.p / maxP) * h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }});
    ctx.stroke();

    // Dots
    ctx.fillStyle = '#9A3412';
    stats.forEach((st, i) => {{
        const x = pad.l + i * gap + gap/2;
        const y = pad.t + h - (st.p / maxP) * h;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI*2);
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        
        ctx.fillStyle = '#9A3412';
        ctx.textAlign = 'center';
        ctx.font = '12px Inter';
        ctx.textBaseline = (y - pad.t < 20) ? 'top' : 'bottom';
        const yOff = (y - pad.t < 20) ? 8 : -8;
        ctx.fillText('$' + fmtN(st.p), x, y + yOff);
    }});

    // Legend
    const lx = canvas.width / 2;
    const ly = 15;
    ctx.fillStyle = '#F97316';
    ctx.fillRect(lx - 80, ly - 5, 12, 10);
    ctx.fillStyle = '#1C1917';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.font = '13px Inter';
    ctx.fillText('Doanh số', lx - 60, ly);

    ctx.beginPath();
    ctx.strokeStyle = '#9A3412';
    ctx.lineWidth = 2;
    ctx.moveTo(lx + 10, ly);
    ctx.lineTo(lx + 30, ly);
    ctx.stroke();
    ctx.beginPath();
    ctx.fillStyle = '#9A3412';
    ctx.arc(lx + 20, ly, 3, 0, Math.PI*2);
    ctx.fill();
    ctx.fillStyle = '#1C1917';
    ctx.fillText('Giá ($)', lx + 36, ly);

    // Axis titles
    ctx.fillStyle = '#78716C';
    ctx.font = '13px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('Nhóm Rating', pad.l + w/2, pad.t + h + 25);

    ctx.save();
    ctx.translate(15, pad.t + h/2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Doanh số', 0, 0);
    ctx.restore();

    ctx.save();
    ctx.translate(cW - 15, pad.t + h/2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Giá ($)', 0, 0);
    ctx.restore();

    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        for (let i = 0; i < stats.length; i++) {{
            const px = pad.l + i * gap + gap/2;
            const py = pad.t + h - (stats[i].p / maxP) * h;
            if (Math.hypot(x - px, y - py) <= 12) {{
                showTooltip(e, `Nhóm: ${{stats[i].lbl}}\nGiá TB: $${{fmtF(stats[i].p)}}`);
                return;
            }}
        }}
        
        for (let i = 0; i < stats.length; i++) {{
            const barH = (stats[i].s / maxS) * h;
            const bx = pad.l + i * gap + gap/2 - barW/2;
            const by = pad.t + h - barH;
            if (x >= bx && x <= bx + barW && y >= by && y <= pad.t + h) {{
                showTooltip(e, `Nhóm: ${{stats[i].lbl}}\nDoanh số TB: ${{fmtN(stats[i].s)}} đơn`);
                return;
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

function drawChart3(data) {{
    const canvas = document.getElementById('chart3');
    const ctx = canvas.getContext('2d');
    
    const dpr = window.devicePixelRatio || 1;
    canvas.width  = canvas.offsetWidth  * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    
    ctx.clearRect(0, 0, cW, cH);
    if (!data || !data.length) return;

    const valid = data.filter(d => d.rating >= 1.0 && d.reviews > 0);
    if (!valid.length) return;

    const pad = {{ t: 40, r: 20, b: 45, l: 55 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;

    const dataMinR = Math.min(...valid.map(d => d.rating));
    let dynMinX = Math.floor(dataMinR * 10) / 10 - 0.1;
    if (dynMinX < 2.5) dynMinX = 2.5;
    const minX = dynMinX, maxX = 5.0;
    const getX = r => pad.l + ((r - minX) / (maxX - minX)) * w;

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
    for (let r10 = Math.ceil(minX * 2) * 5; r10 <= 50; r10 += 5) {{
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
        ctx.arc(x, y, 4, 0, Math.PI*2);
        ctx.fillStyle = getColor(d.sales_volume_num);
        ctx.fill();
    }});
    ctx.restore();

    const legends = [
        {{ l: 'Không có DS', c: 'rgba(209, 213, 219, 0.5)' }},
        {{ l: 'DS Thấp', c: 'rgba(249, 180, 100, 0.7)' }},
        {{ l: 'DS Trung bình', c: 'rgba(249, 115, 22, 0.7)' }},
        {{ l: 'DS Cao', c: 'rgba(154, 52, 18, 0.85)' }}
    ];
    let lx = pad.l + w - 10;
    const ly = pad.t - 25;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.font = '12px Inter';
    [...legends].reverse().forEach(lg => {{
        ctx.fillStyle = '#1C1917';
        ctx.fillText(lg.l, lx, ly);
        const textW = ctx.measureText(lg.l).width;
        ctx.fillStyle = lg.c;
        ctx.beginPath();
        ctx.arc(lx - textW - 8, ly, 4, 0, Math.PI*2);
        ctx.fill();
        lx -= (textW + 24);
    }});

    ctx.fillStyle = '#78716C';
    ctx.font = '13px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('Rating (★)', pad.l + w/2, pad.t + h + 25);

    ctx.save();
    ctx.translate(15, pad.t + h/2);
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
                showTooltip(e, `Rating: ${{d.rating}}★\nReviews: ${{fmtN(d.reviews)}}\nDoanh số: ${{d.sales_volume_num || 0}} đơn`);
                return;
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

let tableSort = {{ field: 'reviews', dir: 'desc' }};
let currentTableData = [];

function renderTable() {{
    const tbody = document.getElementById('topBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const f = tableSort.field;
    const isDesc = tableSort.dir === 'desc';
    const dCopy = [...currentTableData].sort((a, b) => {{
        let vA = a[f] || 0;
        let vB = b[f] || 0;
        if (typeof a[f] === 'string') {{
            vA = a[f].toLowerCase();
            vB = (b[f] || '').toLowerCase();
        }}
        if (vA < vB) return isDesc ? 1 : -1;
        if (vA > vB) return isDesc ? -1 : 1;
        return 0;
    }});

    const top9 = dCopy.slice(0, 9);
    top9.forEach(d => {{
        const tr = document.createElement('tr');
        
        let titleStr = (d.title || '').replace(/"/g, '&quot;');
        let titleCell = `<td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${{titleStr}}">${{titleStr}}</td>`;
        let ratingCell = `<td style="white-space: nowrap;">${{d.rating ? d.rating.toFixed(1) + '★' : '–'}}</td>`;
        let reviewsCell = `<td style="white-space: nowrap;">${{d.reviews ? fmtN(d.reviews) : '0'}}</td>`;
        let priceCell = `<td style="white-space: nowrap;">${{d.current_price ? '$' + fmtF(d.current_price) : '–'}}</td>`;
        let salesCell = `<td style="white-space: nowrap;">${{d.sales_volume_num ? fmtN(d.sales_volume_num) : '–'}}</td>`;
        let catCell = `<td style="white-space: nowrap;">${{d.crawl_category || '–'}}</td>`;
        
        tr.innerHTML = titleCell + ratingCell + reviewsCell + priceCell + salesCell + catCell;
        tbody.appendChild(tr);
    }});

    document.querySelectorAll('.top-table th').forEach(th => {{
        const sf = th.getAttribute('data-sort');
        if (sf) {{
            const icon = th.querySelector('.sort-icon');
            if (sf === tableSort.field) {{
                icon.textContent = isDesc ? '▼' : '▲';
                icon.style.color = '#F97316';
            }} else {{
                icon.textContent = '';
                icon.style.color = 'inherit';
            }}
        }}
    }});
}}

function initTable() {{
    document.querySelectorAll('.top-table th[data-sort]').forEach(th => {{
        th.addEventListener('click', () => {{
            const sf = th.getAttribute('data-sort');
            if (tableSort.field === sf) {{
                tableSort.dir = tableSort.dir === 'desc' ? 'asc' : 'desc';
            }} else {{
                tableSort.field = sf;
                tableSort.dir = 'desc';
            }}
            renderTable();
        }});
    }});
}}

/* ── helpers for Goal 2 ── */
function getQuantile(arr, q) {{
    if(!arr.length) return 0;
    const sorted = [...arr].sort((a,b)=>a-b);
    const pos = (sorted.length - 1) * q;
    const base = Math.floor(pos);
    const rest = pos - base;
    if(sorted[base+1] !== undefined) {{
        return sorted[base] + rest * (sorted[base+1] - sorted[base]);
    }} else {{
        return sorted[base];
    }}
}}

function drawChart4(data) {{
    const canvas = document.getElementById('chart4');
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    ctx.clearRect(0,0,cW,cH);
    if(!data || !data.length) return;

    const revs = data.map(d => d.reviews || 0);
    const q25 = getQuantile(revs, 0.25);
    const q50 = getQuantile(revs, 0.50);
    const q75 = getQuantile(revs, 0.75);

    const groups = [
        {{ lbl: "Q1 (ít nhất)", ds: [], ps: [] }},
        {{ lbl: "Q2", ds: [], ps: [] }},
        {{ lbl: "Q3", ds: [], ps: [] }},
        {{ lbl: "Q4 (top 25%)", ds: [], ps: [] }}
    ];

    data.forEach(d => {{
        const r = d.reviews || 0;
        let idx = 0;
        if(r >= q75) idx = 3;
        else if(r >= q50) idx = 2;
        else if(r >= q25) idx = 1;

        if (d.sales_volume_num > 0) groups[idx].ds.push(d.sales_volume_num);
        if (d.current_price > 0) groups[idx].ps.push(d.current_price);
    }});

    const stats = groups.map(g => ({{
        lbl: g.lbl,
        s: g.ds.length ? g.ds.reduce((a,b)=>a+b,0)/g.ds.length : 0,
        sCount: g.ds.length,
        p: g.ps.length ? g.ps.reduce((a,b)=>a+b,0)/g.ps.length : 0,
        pCount: g.ps.length
    }}));

    const pad = {{ t: 40, r: 60, b: 40, l: 60 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;

    const maxS = Math.max(1, ...stats.map(d => d.s)) * 1.15;
    const maxP = Math.max(1, ...stats.map(d => d.p)) * 1.15;
    const gap = w / stats.length;

    ctx.fillStyle = 'rgba(249, 115, 22, 0.08)';
    ctx.fillRect(pad.l + 3 * gap, pad.t, gap, h);

    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textBaseline = 'middle';
    ctx.beginPath();
    for (let i = 0; i <= 5; i++) {{
        const y = pad.t + h - (i / 5) * h;
        ctx.textAlign = 'right';
        ctx.fillText(fmtK(maxS * i / 5), pad.l - 8, y);
        ctx.textAlign = 'left';
        ctx.fillText('$' + fmtF(maxP * i / 5), pad.l + w + 8, y);
        
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + w, y);
    }}
    ctx.strokeStyle = '#E5E7EB';
    ctx.stroke();

    const barW = Math.min(60, gap * 0.4);
    stats.forEach((d, i) => {{
        const barH = (d.s / maxS) * h;
        const x = pad.l + i * gap + gap/2 - barW/2;
        const y = pad.t + h - barH;
        ctx.fillStyle = '#F97316';
        ctx.fillRect(x, y, barW, barH);
        
        ctx.fillStyle = '#1C1917';
        ctx.font = '11px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        let sLabel = d.s >= 1000 ? (d.s/1000).toFixed(1) + 'k' : Math.round(d.s).toString();
        ctx.fillText(sLabel, x + barW/2, y - 4);
        
        ctx.fillStyle = '#78716C';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(d.lbl, x + barW/2, pad.t + h + 8);
    }});

    ctx.beginPath();
    stats.forEach((d, i) => {{
        const x = pad.l + i * gap + gap/2;
        const y = pad.t + h - (d.p / maxP) * h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }});
    ctx.strokeStyle = '#9A3412';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.font = '12px Inter';
    ctx.textAlign = 'center';
    stats.forEach((d, i) => {{
        const x = pad.l + i * gap + gap/2;
        const y = pad.t + h - (d.p / maxP) * h;
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI*2);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.stroke();
        
        ctx.fillStyle = '#9A3412';
        if (y < pad.t + 30) {{
            ctx.textBaseline = 'top';
            ctx.fillText('$' + fmtF(d.p), x, y + 8);
        }} else {{
            ctx.textBaseline = 'bottom';
            ctx.fillText('$' + fmtF(d.p), x, y - 8);
        }}
    }});

    ctx.save();
    ctx.translate(15, pad.t + h/2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#78716C';
    ctx.fillText('Doanh số', 0, 0);
    ctx.restore();

    ctx.save();
    ctx.translate(cW - 20, pad.t + h/2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#78716C';
    ctx.fillText('Giá ($)', 0, 0);
    ctx.restore();



    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        
        for (let i = 0; i < stats.length; i++) {{
            const px = pad.l + i * gap + gap/2;
            const py = pad.t + h - (stats[i].p / maxP) * h;
            if (Math.hypot(mx - px, my - py) <= 12) {{
                showTooltip(e, `Nhóm: ${{stats[i].lbl}}\nGiá TB: $${{fmtF(stats[i].p)}}\nSố SP: ${{fmtN(stats[i].pCount)}}`);
                return;
            }}
        }}
        
        for (let i = 0; i < stats.length; i++) {{
            const barH = (stats[i].s / maxS) * h;
            const bx = pad.l + i * gap + gap/2 - barW/2;
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

function drawChart5(data) {{
    const canvas = document.getElementById('chart5');
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    ctx.clearRect(0,0,cW,cH);
    if(!data || !data.length) return;

    const catCounts = {{}};
    data.forEach(d => {{
        if (d.crawl_category && d.crawl_category.trim() !== '') {{
            const c = d.crawl_category.trim();
            catCounts[c] = (catCounts[c] || 0) + 1;
        }}
    }});
    const topCats = Object.entries(catCounts).sort((a,b)=>b[1]-a[1]).slice(0,5).map(x=>x[0]);
    if(!topCats.length) return;

    const revs = data.map(d => d.reviews || 0);
    const q75 = getQuantile(revs, 0.75);

    const groups = topCats.map(c => ({{ cat: c, g1: [], g2: [] }}));

    data.forEach(d => {{
        if (d.crawl_category && d.crawl_category.trim() !== '') {{
            const c = d.crawl_category.trim();
            const idx = topCats.indexOf(c);
            if (idx > -1 && d.current_price > 0) {{
                const r = d.reviews || 0;
                if (r >= q75) groups[idx].g1.push(d.current_price);
                else groups[idx].g2.push(d.current_price);
            }}
        }}
    }});

    const stats = groups.map(g => ({{
        cat: g.cat,
        p1: g.g1.length ? g.g1.reduce((a,b)=>a+b,0)/g.g1.length : 0,
        c1: g.g1.length,
        p2: g.g2.length ? g.g2.reduce((a,b)=>a+b,0)/g.g2.length : 0,
        c2: g.g2.length
    }}));

    const pad = {{ t: 40, r: 20, b: 55, l: 65 }};
    const w = cW - pad.l - pad.r;
    const h = cH - pad.t - pad.b;

    const maxP = Math.max(1, ...stats.map(s => Math.max(s.p1, s.p2))) * 1.15;
    
    ctx.fillStyle = '#78716C';
    ctx.font = '12px Inter';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'right';
    ctx.beginPath();
    for (let i = 0; i <= 4; i++) {{
        const y = pad.t + h - (i / 4) * h;
        ctx.fillText('$' + Math.round(maxP * i / 4), pad.l - 8, y);
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + w, y);
    }}
    ctx.strokeStyle = '#E5E7EB';
    ctx.stroke();

    const gap = w / stats.length;
    const barW = Math.min(30, gap * 0.35);

    stats.forEach((d, i) => {{
        const xCenter = pad.l + i * gap + gap/2;
        
        const h1 = (d.p1 / maxP) * h;
        const x1 = xCenter - barW - 2;
        const y1 = pad.t + h - h1;
        ctx.fillStyle = '#9A3412';
        ctx.fillRect(x1, y1, barW, h1);

        const h2 = (d.p2 / maxP) * h;
        const x2 = xCenter + 2;
        const y2 = pad.t + h - h2;
        ctx.fillStyle = '#FDBA74';
        ctx.fillRect(x2, y2, barW, h2);
        
        ctx.fillStyle = '#78716C';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        const lbl = d.cat.length > 15 ? d.cat.slice(0, 12) + '...' : d.cat;
        
        ctx.save();
        ctx.translate(xCenter, pad.t + h + 8);
        if(d.cat.length > 6) {{
            ctx.rotate(20 * Math.PI / 180);
            ctx.textAlign = 'left';
        }}
        ctx.fillText(lbl, 0, 0);
        ctx.restore();
    }});

    let lx = pad.l + w - 10;
    const ly = pad.t - 20;
    ctx.textBaseline = 'middle';
    ctx.font = '12px Inter';
    
    ctx.textAlign = 'right';
    ctx.fillStyle = '#1C1917';
    ctx.fillText('75% còn lại', lx, ly);
    let textW = ctx.measureText('75% còn lại').width;
    ctx.fillStyle = '#FDBA74';
    ctx.fillRect(lx - textW - 14, ly - 5, 10, 10);
    
    lx -= (textW + 24);
    
    ctx.fillStyle = '#1C1917';
    ctx.fillText('Top 25% Reviews', lx, ly);
    textW = ctx.measureText('Top 25% Reviews').width;
    ctx.fillStyle = '#9A3412';
    ctx.fillRect(lx - textW - 14, ly - 5, 10, 10);

    ctx.save();
    ctx.translate(15, pad.t + h/2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#78716C';
    ctx.fillText('Giá TB ($)', 0, 0);
    ctx.restore();



    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        
        for (let i = 0; i < stats.length; i++) {{
            const xCenter = pad.l + i * gap + gap/2;
            const h1 = (stats[i].p1 / maxP) * h;
            const x1 = xCenter - barW - 2;
            const y1 = pad.t + h - h1;
            
            if (mx >= x1 && mx <= x1 + barW && my >= y1 && my <= pad.t + h) {{
                showTooltip(e, `Danh mục: ${{stats[i].cat}}\nNhóm: Top 25% Reviews\nGiá TB: $${{fmtF(stats[i].p1)}}\nSố SP: ${{fmtN(stats[i].c1)}}`);
                return;
            }}
            
            const h2 = (stats[i].p2 / maxP) * h;
            const x2 = xCenter + 2;
            const y2 = pad.t + h - h2;
            
            if (mx >= x2 && mx <= x2 + barW && my >= y2 && my <= pad.t + h) {{
                showTooltip(e, `Danh mục: ${{stats[i].cat}}\nNhóm: 75% còn lại\nGiá TB: $${{fmtF(stats[i].p2)}}\nSố SP: ${{fmtN(stats[i].c2)}}`);
                return;
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

function drawChart6(data) {{
    const canvas = document.getElementById('chart6');
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    const cW = canvas.offsetWidth;
    const cH = canvas.offsetHeight;
    ctx.clearRect(0,0,cW,cH);
    if(!data || !data.length) return;

    const revs = data.map(d => d.reviews || 0);
    const q25 = getQuantile(revs, 0.25);
    const q50 = getQuantile(revs, 0.50);
    const q75 = getQuantile(revs, 0.75);

    const stats = [
        {{ lbl: "Q1 (ít nhất)", sales: 0, count: 0 }},
        {{ lbl: "Q2", sales: 0, count: 0 }},
        {{ lbl: "Q3", sales: 0, count: 0 }},
        {{ lbl: "Q4 (top 25%)", sales: 0, count: 0 }}
    ];

    data.forEach(d => {{
        const r = d.reviews || 0;
        let idx = 0;
        if(r >= q75) idx = 3;
        else if(r >= q50) idx = 2;
        else if(r >= q25) idx = 1;

        if (d.sales_volume_num > 0) {{
            stats[idx].sales += d.sales_volume_num;
            stats[idx].count++;
        }}
    }});

    const totalSales = stats.reduce((acc, s) => acc + s.sales, 0);
    const colors = ["#FED7AA", "#FDBA74", "#F97316", "#9A3412"];
    
    const pad = {{ t: 40, r: 10, b: 50, l: 10 }};
    const h = cH - pad.t - pad.b;
    const cx = cW / 2;
    const cy = pad.t + h / 2;
    const radius = Math.min(cx, h/2) * 0.8;
    const innerRadius = radius * 0.7;

    let startAngle = -Math.PI / 2;
    const segments = [];

    stats.forEach((s, i) => {{
        const pct = totalSales > 0 ? (s.sales / totalSales) : 0;
        const sliceAngle = pct * 2 * Math.PI;
        
        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
        ctx.arc(cx, cy, innerRadius, startAngle + sliceAngle, startAngle, true);
        ctx.fillStyle = colors[i];
        ctx.fill();
        
        segments.push({{ 
            start: startAngle, 
            end: startAngle + sliceAngle, 
            sales: s.sales, 
            count: s.count,
            pct: (pct * 100).toFixed(1),
            label: s.lbl
        }});
        startAngle += sliceAngle;
    }});

    // Center text
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#1C1917';
    ctx.font = 'bold 15px Inter';
    ctx.fillText('% Doanh số', cx, cy - 8);
    ctx.fillStyle = '#78716C';
    ctx.font = '11px Inter';
    ctx.fillText('theo nhóm Reviews', cx, cy + 12);

    // Legend (pct) - 2 lines
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillStyle = '#1C1917';
    ctx.font = '11px Inter';
    const lg1 = `Q1: ${{segments[0].pct}}% | Q2: ${{segments[1].pct}}%`;
    const lg2 = `Q3: ${{segments[2].pct}}% | Q4: ${{segments[3].pct}}%`;
    ctx.fillText(lg1, cx, cH - 25);
    ctx.fillText(lg2, cx, cH - 10);

    canvas.onmousemove = e => {{
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const dx = mx - cx;
        const dy = my - cy;
        const dist = Math.hypot(dx, dy);
        
        if (dist >= innerRadius && dist <= radius) {{
            let angle = Math.atan2(dy, dx);
            if (angle < -Math.PI/2) angle += 2*Math.PI;
            
            for (let i = 0; i < segments.length; i++) {{
                if (angle >= segments[i].start && angle <= segments[i].end) {{
                    showTooltip(e, `Nhóm: ${{segments[i].label}}\nTổng doanh số: ${{fmtN(segments[i].sales)}}\n% đóng góp: ${{segments[i].pct}}%\nSố SP có DS: ${{fmtN(segments[i].count)}}`);
                    return;
                }}
            }}
        }}
        hideTooltip();
    }};
    canvas.onmouseleave = hideTooltip;
}}

/* ── main apply ──────────────────────────────────────────── */
function applyFilters() {{
    const filtered = getFiltered();
    updateKPIs(filtered);
    drawChart1(filtered);
    drawChart2(filtered);
    drawChart3(filtered);
    drawChart4(filtered);
    drawChart5(filtered);
    drawChart6(filtered);
    
    currentTableData = filtered;
    tableSort = {{ field: 'reviews', dir: 'desc' }};
    renderTable();
}}

window.addEventListener('resize', () => {{
    applyFilters();
}});

/* ── boot ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {{
    initDropdown();
    initSliders();
    initTable();
    applyFilters();
}});
</script>
</body>
</html>"""

    components.html(html_code, height=1550, scrolling=False)
