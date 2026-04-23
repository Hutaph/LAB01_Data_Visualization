import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render(df: pd.DataFrame):
    # ------------------------------------------------------------------ #
    #  Chuẩn bị dữ liệu
    # ------------------------------------------------------------------ #
    data = df.copy()

    data["current_price"] = pd.to_numeric(data.get("price", data.get("current_price", 0)), errors="coerce").fillna(0.0)
    data["original_price"] = pd.to_numeric(data.get("original_price", 0), errors="coerce").fillna(0.0)
    data["rating"] = pd.to_numeric(data.get("rating", 0), errors="coerce").fillna(0.0)
    data["reviews"] = pd.to_numeric(data.get("reviews", 0), errors="coerce").fillna(0)
    data["sales_volume_num"] = pd.to_numeric(data.get("sales_volume_num", 0), errors="coerce").fillna(0)
    data["crawl_category"] = data.get("crawl_category", pd.Series(["Không rõ"] * len(data))).fillna("Không rõ")
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
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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

/* dropdown */
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

/* dual-handle slider */
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

/* toggle */
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

/* ── KPI row ──────────────────────────────────────────────── */
.kpi-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
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
    min-width: 0;          /* bắt buộc — tránh overflow trong CSS Grid */
    overflow: hidden;
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
    font-size: 28px;
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

/* ── Chart placeholder ────────────────────────────────────── */
.section-divider {{
    height: 1px;
    background: #F3E8D8;
    margin: 8px 0 24px;
}}
</style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════
     FILTER BAR
═══════════════════════════════════════════════════════════ -->
<div class="filter-bar">

    <!-- 1. Danh mục -->
    <div class="f-item">
        <span class="f-label">Danh mục</span>
        <select id="selCategory" onchange="applyFilters()">
            <option value="ALL">Tất cả</option>
        </select>
    </div>

    <!-- 2. Rating -->
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

    <!-- 3. Reviews -->
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

    <!-- 4. Giá -->
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

    <!-- 5. Toggle doanh số -->
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
     KPI CARDS  (4 cards)
═══════════════════════════════════════════════════════════ -->
<div class="kpi-row">
    <div class="kpi-card">
        <div class="kpi-title">Tổng sản phẩm</div>
        <div class="kpi-value" id="kpi_total">0</div>
        <div class="kpi-sub"  id="kpi_total_sub">–</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Rating trung bình</div>
        <div class="kpi-value" id="kpi_rating">0★</div>
        <div class="kpi-sub"  id="kpi_rating_sub">–</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Trung vị Reviews</div>
        <div class="kpi-value" id="kpi_reviews">0</div>
        <div class="kpi-sub"  id="kpi_reviews_sub">–</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Rating ≥ 4.5</div>
        <div class="kpi-value" id="kpi_high_rating">0%</div>
        <div class="kpi-sub"  id="kpi_high_rating_sub">–</div>
    </div>
</div>

<div class="section-divider"></div>

<!-- biểu đồ sẽ thêm vào đây -->

<script>
const RAW_DATA = {data_json_str};

/* ── helpers ─────────────────────────────────────────────── */
const fmtN  = n => new Intl.NumberFormat('en-US').format(Math.round(n));
const fmtF  = (n, d=2) => Number(n).toFixed(d);
const fmtK  = n => n >= 1000 ? (n/1000).toFixed(0)+'k' : fmtN(n);

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
        if (d.reviews      > maxRev)   maxRev   = d.reviews;
        if (d.current_price > maxPrice) maxPrice = d.current_price;
    }});
    maxRev   = Math.ceil(maxRev   / 500)  * 500  || 500000;
    maxPrice = Math.ceil(maxPrice / 100)  * 100  || 3400;

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
    const cats = [...new Set(RAW_DATA.map(d => d.crawl_category).filter(c => c && c !== 'Không rõ'))].sort();
    const sel  = document.getElementById('selCategory');
    cats.forEach(c => {{ const o = document.createElement('option'); o.value = o.textContent = c; sel.appendChild(o); }});
}}

/* ── filter ──────────────────────────────────────────────── */
function getFiltered() {{
    const cat      = document.getElementById('selCategory').value;
    const rLo      = parseFloat(document.getElementById('rating_min').value);
    const rHi      = parseFloat(document.getElementById('rating_max').value);
    const revLo    = parseFloat(document.getElementById('reviews_min').value);
    const revHi    = parseFloat(document.getElementById('reviews_max').value);
    const pLo      = parseFloat(document.getElementById('price_min').value);
    const pHi      = parseFloat(document.getElementById('price_max').value);
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
    const total    = data.length;
    const cats     = new Set(data.map(d => d.crawl_category)).size;

    const ratings  = data.map(d => d.rating).filter(r => r > 0);
    const avgRat   = ratings.length ? ratings.reduce((a,b)=>a+b,0)/ratings.length : 0;
    const totalRev = data.reduce((a,b) => a + (b.reviews||0), 0);

    const revArr   = data.map(d => d.reviews).filter(r => r > 0).sort((a,b)=>a-b);
    const medRev   = revArr.length
        ? (revArr.length%2===0
            ? (revArr[revArr.length/2-1]+revArr[revArr.length/2])/2
            : revArr[Math.floor(revArr.length/2)])
        : 0;

    const highRat  = data.filter(d => d.rating >= 4.5).length;
    const highPct  = total ? (highRat/total*100) : 0;

    document.getElementById('kpi_total').textContent          = fmtN(total);
    document.getElementById('kpi_total_sub').textContent      = `thuộc ${{cats}} danh mục`;

    document.getElementById('kpi_rating').textContent         = fmtF(avgRat)+'★';
    document.getElementById('kpi_rating_sub').textContent     = `từ ${{fmtN(totalRev)}} lượt đánh giá`;

    document.getElementById('kpi_reviews').textContent        = fmtN(medRev);
    document.getElementById('kpi_reviews_sub').textContent    = `Trung vị lượt đánh giá`;

    document.getElementById('kpi_high_rating').textContent    = fmtF(highPct,1)+'%';
    document.getElementById('kpi_high_rating_sub').textContent= `${{fmtN(highRat)}} sản phẩm có rating ≥ 4.5`;
}}

/* ── main apply ──────────────────────────────────────────── */
function applyFilters() {{
    const filtered = getFiltered();
    updateKPIs(filtered);
}}

/* ── boot ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {{
    initDropdown();
    initSliders();
    applyFilters();
}});
</script>
</body>
</html>"""

    components.html(html_code, height=400, scrolling=False)
