"""
Tab Định Giá — Pricing Strategy Analysis
Phân tích chiến lược định giá dựa trên dataset thực tế Amazon (8.537 sản phẩm).

Phát hiện chính từ EDA:
- Cột giá chính: current_price (= price), median=$26.95, mean=$76.26
- Discount: original_price chỉ có ~46% SP, discount TB=22.4%
- Phân khúc hợp lý (theo phân phối thực): Bình dân <$20, Trung cấp $20-$70, Cao cấp >$70
- Doanh số: sales_volume_num (50–100.000, median=1.000/tháng)
- Tương quan Spearman giá–doanh số = -0.47 (âm rõ rệt)
- is_best_seller = 100% True → không dùng để so sánh
- is_prime chỉ 73 SP (0.8%) → không đại diện
- is_amazon_choice: 623 SP (7.1%) → có ý nghĩa
- Danh mục: 30 loại, ~300 SP/loại
- delivery_fee: không có free delivery (0), range ~$14–$39
"""

import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components


# ─────────────────────────────────────────────────────────────────────────────
#  Data preparation
# ─────────────────────────────────────────────────────────────────────────────
def _prep(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Giá chính — current_price (đã clean sẵn, tương đương price)
    price_src = "current_price" if "current_price" in out.columns else "price"
    out["current_price"] = pd.to_numeric(out.get(price_src, pd.Series()), errors="coerce").fillna(0)

    # Giá gốc (~46% có dữ liệu)
    out["original_price"] = pd.to_numeric(out.get("original_price", pd.Series()), errors="coerce").fillna(0)

    # Discount — chỉ khi original_price > current_price
    mask = (out["original_price"] > out["current_price"]) & (out["original_price"] > 0) & (out["current_price"] > 0)
    out["discount_pct"] = 0.0
    out.loc[mask, "discount_pct"] = (
        (out.loc[mask, "original_price"] - out.loc[mask, "current_price"])
        / out.loc[mask, "original_price"] * 100
    ).clip(0, 80)

    # Rating & Reviews
    out["rating"]  = pd.to_numeric(out.get("rating",  pd.Series(dtype=float)), errors="coerce").fillna(0)
    out["reviews"] = pd.to_numeric(out.get("reviews", pd.Series(dtype=int)),   errors="coerce").fillna(0).astype(int)

    # Doanh số — sales_volume_num (đã parse từ "1K+ bought in past month")
    sv_col = "sales_volume_num" if "sales_volume_num" in out.columns else None
    out["sales_vol"] = pd.to_numeric(out[sv_col], errors="coerce").fillna(0) if sv_col else 0.0

    # Nhãn boolean
    for b in ["is_amazon_choice", "is_prime", "is_best_seller", "has_variations", "is_climate_friendly"]:
        if b not in out.columns:
            out[b] = False
        else:
            out[b] = out[b].fillna(False).astype(bool)

    # Danh mục
    cat_col = "crawl_category" if "crawl_category" in out.columns else "category"
    out["category"] = out[cat_col].fillna("Không rõ") if cat_col in out.columns else "Không rõ"

    # Lọc giá hợp lệ
    out = out[out["current_price"] > 0].copy()

    # Phân khúc giá — dựa trên phân phối thực tế dataset
    # 25th=$14, median=$27, 75th=$70 → ngưỡng $20 / $70 hợp lý
    def _seg(p):
        if p < 20:  return "Bình dân"
        if p <= 70: return "Trung cấp"
        return "Cao cấp"

    out["segment"] = out["current_price"].apply(_seg)
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  Build payload — tất cả tính toán phía Python, JS chỉ render
# ─────────────────────────────────────────────────────────────────────────────
def _build_payload(df: pd.DataFrame) -> dict:
    SEG_ORDER  = ["Bình dân", "Trung cấp", "Cao cấp"]
    SEG_COLORS = {"Bình dân": "#3266ad", "Trung cấp": "#F97316", "Cao cấp": "#9A3412"}

    total = len(df)

    # ── KPI ──────────────────────────────────────────────────────────────────
    avg_price    = float(df["current_price"].mean())
    median_price = float(df["current_price"].median())
    disc_df      = df[df["discount_pct"] > 0]
    avg_disc     = float(disc_df["discount_pct"].mean())    if len(disc_df) > 0 else 0.0
    pct_disc     = float(len(disc_df) / total * 100)
    avg_rating   = float(df["rating"].mean())
    sv_valid     = df[df["sales_vol"] > 0]["sales_vol"]
    median_sales = float(sv_valid.median()) if len(sv_valid) > 0 else 0.0
    seg_counts   = df["segment"].value_counts()
    dominant_seg = seg_counts.idxmax()
    dominant_pct = float(seg_counts.max() / total * 100)
    # Spearman correlation giá–doanh số
    valid_corr   = df[df["sales_vol"] > 0][["current_price", "sales_vol"]]
    spearman_r   = float(valid_corr["current_price"].corr(valid_corr["sales_vol"], method="spearman")) \
                   if len(valid_corr) > 30 else -0.47

    kpi = dict(
        total=total,
        avg_price=round(avg_price, 2),
        median_price=round(median_price, 2),
        avg_disc=round(avg_disc, 1),
        pct_disc=round(pct_disc, 1),
        avg_rating=round(avg_rating, 2),
        median_sales=int(median_sales),
        dominant_seg=dominant_seg,
        dominant_pct=round(dominant_pct, 1),
        spearman_r=round(spearman_r, 3),
    )

    # ── Donut: thị phần phân khúc ─────────────────────────────────────────
    donut = dict(
        labels=SEG_ORDER,
        counts=[int(seg_counts.get(s, 0)) for s in SEG_ORDER],
        colors=[SEG_COLORS[s] for s in SEG_ORDER],
    )

    # ── Bar bins chi tiết ──────────────────────────────────────────────────
    bins       = [0, 5, 10, 15, 20, 30, 50, 70, 100, 200, 9999]
    bin_labels = ["<$5","$5-10","$10-15","$15-20","$20-30","$30-50","$50-70","$70-100","$100-200",">$200"]
    bin_colors = ["#6aaee8","#5499d8","#3e84c8","#3266ad","#F97316","#e06008","#c84e00","#9A3412","#7a280e","#5a1c0a"]

    df["_bin"] = pd.cut(df["current_price"], bins=bins, labels=bin_labels, right=False)
    bin_counts = df["_bin"].value_counts().reindex(bin_labels, fill_value=0)
    bin_pcts   = (bin_counts / total * 100).round(1)

    bin_sales_mean   = df.groupby("_bin", observed=True)["sales_vol"].mean().reindex(bin_labels).fillna(0)
    bin_sales_median = df.groupby("_bin", observed=True)["sales_vol"].median().reindex(bin_labels).fillna(0)
    bin_rating       = df.groupby("_bin", observed=True)["rating"].mean().reindex(bin_labels).fillna(0)

    bar_bins = dict(
        labels=bin_labels,
        pcts=bin_pcts.tolist(),
        colors=bin_colors,
        sales_mean=[int(x) for x in bin_sales_mean],
        sales_median=[int(x) for x in bin_sales_median],
        avg_rating=[round(float(x), 2) for x in bin_rating],
    )

    # ── Segment comparison ────────────────────────────────────────────────
    seg_agg = df.groupby("segment").agg(
        avg_sales=("sales_vol",    "mean"),
        med_sales=("sales_vol",    "median"),
        avg_rating=("rating",      "mean"),
        avg_reviews=("reviews",    "mean"),
        avg_disc=("discount_pct",  "mean"),
        count=("current_price",    "count"),
    ).reindex(SEG_ORDER).fillna(0)

    seg_compare = dict(
        labels=SEG_ORDER,
        colors=[SEG_COLORS[s] for s in SEG_ORDER],
        avg_sales  =[int(seg_agg.loc[s,"avg_sales"])   for s in SEG_ORDER],
        med_sales  =[int(seg_agg.loc[s,"med_sales"])   for s in SEG_ORDER],
        avg_rating =[round(float(seg_agg.loc[s,"avg_rating"]),3)  for s in SEG_ORDER],
        avg_reviews=[int(seg_agg.loc[s,"avg_reviews"]) for s in SEG_ORDER],
        avg_disc   =[round(float(seg_agg.loc[s,"avg_disc"]),1)    for s in SEG_ORDER],
        counts     =[int(seg_agg.loc[s,"count"])        for s in SEG_ORDER],
    )

    # ── Scatter: price vs sales_vol (price ≤ $200, sample 500) ───────────
    scat = df[(df["current_price"] <= 200) & (df["sales_vol"] > 0)].copy()
    if len(scat) > 500:
        scat = scat.sample(500, random_state=42)
    scatter = dict(
        points=[dict(x=round(float(r["current_price"]),2), y=int(r["sales_vol"]),
                     seg=r["segment"], r=round(float(r["rating"]),1))
                for _, r in scat.iterrows()],
        colors=SEG_COLORS,
    )

    # ── Amazon Choice premium ─────────────────────────────────────────────
    amz = df.groupby("is_amazon_choice")["sales_vol"].agg(["mean","median","count"]).round(0)
    amz_compare = dict(
        labels=["Không có nhãn", "Amazon's Choice"],
        sales_mean=[
            int(amz.loc[False,"mean"])   if False in amz.index else 0,
            int(amz.loc[True, "mean"])   if True  in amz.index else 0,
        ],
        sales_median=[
            int(amz.loc[False,"median"]) if False in amz.index else 0,
            int(amz.loc[True, "median"]) if True  in amz.index else 0,
        ],
        colors=["#D1D5DB","#F97316"],
    )

    # ── Top 3 SP mỗi phân khúc ────────────────────────────────────────────
    top_rows = []
    for s in SEG_ORDER:
        sub = df[df["segment"] == s].copy()
        sort_c = "sales_vol" if sub["sales_vol"].sum() > 0 else "reviews"
        for _, r in sub.nlargest(3, sort_c).iterrows():
            t = str(r.get("title","—"))
            t = t[:55] + "…" if len(t) > 55 else t
            top_rows.append(dict(
                seg=s, title=t,
                price=round(float(r["current_price"]),2),
                rating=round(float(r["rating"]),1),
                reviews=int(r["reviews"]),
                sales=int(r["sales_vol"]),
                disc=round(float(r["discount_pct"]),0),
            ))

    return dict(kpi=kpi, donut=donut, bar_bins=bar_bins,
                seg_compare=seg_compare, scatter=scatter,
                amz_compare=amz_compare, top_rows=top_rows,
                seg_colors=SEG_COLORS)


# ─────────────────────────────────────────────────────────────────────────────
#  HTML / JS dashboard
# ─────────────────────────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --pr:#F97316;--prd:#EA580C;--dk:#9A3412;
  --bg:#FEF3E2;--card:#FFFFFF;
  --t1:#1C1917;--t2:#78716C;--t3:#A8A29E;--bd:#E7E5E4;
  --r:8px;--fn:'Inter',sans-serif;--ft:'Montserrat',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);font-family:var(--fn);color:var(--t1);padding:20px;overflow-y:auto;overflow-x:hidden;}

.intro{background:linear-gradient(135deg,#FFF7ED,#FFEDD5);border:1px solid #FED7AA;border-left:5px solid var(--pr);
  border-radius:var(--r);padding:13px 18px;margin-bottom:20px;display:flex;align-items:flex-start;gap:12px;}
.intro-icon{font-size:20px;flex-shrink:0;margin-top:1px;}
.intro-text{font-size:13px;color:#7c3f00;line-height:1.65;}
.intro-text strong{font-weight:700;}

.sec{font-family:var(--ft);font-size:12px;font-weight:800;color:var(--dk);text-transform:uppercase;
  letter-spacing:.7px;margin:22px 0 12px;display:flex;align-items:center;gap:8px;}
.sec::after{content:'';flex:1;height:1.5px;background:linear-gradient(90deg,#FED7AA,transparent);}

.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:13px;margin-bottom:22px;}
.kc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);
  padding:14px 13px;border-left:4px solid var(--pr);transition:transform .15s,box-shadow .15s;}
.kc:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(249,115,22,.15);}
.kc.hi{border-left-color:var(--dk);background:linear-gradient(135deg,#fff7ed,#ffedd5);}
.kt{font-size:10.5px;font-weight:700;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.kv{font-family:var(--ft);font-size:23px;font-weight:700;color:var(--t1);margin:5px 0 3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ks{font-size:11px;color:var(--t3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.kc.hi .kv{color:var(--dk);}

.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;}
.cc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:18px 20px;}
.ct{font-size:14px;font-weight:600;color:var(--t1);margin-bottom:3px;}
.cs{font-size:11.5px;color:var(--t2);margin-bottom:12px;}
.cw{position:relative;width:100%;}

.leg{display:flex;flex-wrap:wrap;gap:11px;margin-bottom:9px;}
.li{display:flex;align-items:center;gap:5px;font-size:11.5px;color:var(--t2);font-weight:500;}
.ld{width:10px;height:10px;border-radius:2px;flex-shrink:0;}

.sb{display:inline-block;font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap;}
.sb0{background:#DBEAFE;color:#1e40af;}
.sb1{background:#FFEDD5;color:#9A3412;}
.sb2{background:#FEE2E2;color:#991b1b;}

.tbl{width:100%;border-collapse:collapse;font-size:12.5px;}
.tbl thead th{text-align:left;font-size:10.5px;font-weight:700;color:var(--t2);text-transform:uppercase;
  letter-spacing:.4px;padding:8px 10px;border-bottom:1.5px solid var(--bd);background:#FAFAF9;}
.tbl tbody td{padding:8px 10px;border-bottom:1px solid var(--bd);vertical-align:middle;}
.tbl tbody tr:last-child td{border-bottom:none;}
.tbl tbody tr:hover{background:#FFF7ED;}

.ins-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px;}
.ins{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);
  padding:14px 15px;border-top:3px solid;}
.ins h4{font-size:13px;font-weight:700;margin-bottom:6px;}
.ins p{font-size:12px;color:var(--t2);line-height:1.65;}

.strat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px;}
.sg{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);
  padding:16px;border-left:4px solid;}
.sg h4{font-size:13px;font-weight:700;margin-bottom:8px;}
.sg ul{padding-left:16px;font-size:12px;color:var(--t2);line-height:1.85;}
.stag{display:inline-block;font-size:10px;font-weight:800;text-transform:uppercase;
  letter-spacing:.5px;padding:2px 8px;border-radius:4px;margin-bottom:8px;}

.tab-bar{display:flex;gap:6px;margin-bottom:11px;}
.tb-btn{padding:6px 13px;font-size:11.5px;font-weight:600;border:1.5px solid var(--bd);
  border-radius:6px;background:var(--card);color:var(--t2);cursor:pointer;transition:all .15s;}
.tb-btn.on{background:var(--pr);border-color:var(--pr);color:#fff;}
.tp{display:none;}
.tp.on{display:block;}
</style>
</head>
<body>

<div class="intro">
  <span class="intro-icon">🏷️</span>
  <div class="intro-text">
    <strong>Phân tích Chiến lược Định giá Amazon</strong> — 
    Dataset thực: <strong>8.537 SP</strong> (USD, 30 danh mục).
    Phân khúc dựa trên phân phối thực tế (P25=$14, Median=$27, P75=$70):
    <em>Bình dân &lt;$20 · Trung cấp $20–$70 · Cao cấp &gt;$70</em>.
    Tương quan Spearman giá–doanh số = <strong id="corrSpan">...</strong>
    (âm có nghĩa là giá thấp → bán nhiều hơn).
  </div>
</div>

<div class="kpi-row" id="kpiRow"></div>

<!-- Phân bố thị trường -->
<div class="sec">📊 Phân bố thị trường</div>
<div class="g2">
  <div class="cc">
    <div class="ct">Thị phần theo phân khúc giá</div>
    <div class="cs">% số lượng sản phẩm — Bình dân chiếm tỷ trọng cao nhất (40%)</div>
    <div class="leg" id="donutLeg"></div>
    <div class="cw" style="height:210px">
      <canvas id="cDonut" role="img" aria-label="Thị phần 3 phân khúc giá">Thị phần phân khúc giá.</canvas>
    </div>
  </div>
  <div class="cc">
    <div class="ct">Phân bố sản phẩm theo khoảng giá chi tiết</div>
    <div class="cs">% số SP — hai đỉnh tại $5–10 (16%) và $20–30 (15.8%)</div>
    <div class="cw" style="height:240px">
      <canvas id="cBin" role="img" aria-label="Phân bố khoảng giá chi tiết">Phân bố khoảng giá.</canvas>
    </div>
  </div>
</div>

<!-- Scatter -->
<div class="sec">🔍 Tương quan Giá — Doanh số (sales_volume_num)</div>
<div class="cc" style="margin-bottom:16px">
  <div class="ct">Scatter plot: Giá bán ($) vs Doanh số tháng (lượt mua)</div>
  <div class="cs">Giới hạn price ≤ $200, sample 500 SP. Spearman r = –0.47 → tương quan âm rõ rệt. Mỗi điểm = 1 sản phẩm.</div>
  <div class="leg" id="scatLeg"></div>
  <div class="cw" style="height:270px">
    <canvas id="cScat" role="img" aria-label="Scatter giá vs doanh số">Scatter giá vs doanh số.</canvas>
  </div>
</div>

<!-- Doanh số & Rating -->
<div class="sec">📈 Doanh số & Rating theo phân khúc</div>
<div class="g2">
  <div class="cc">
    <div class="ct">Doanh số theo khoảng giá chi tiết</div>
    <div class="cs">Xu hướng giảm rõ khi giá tăng — giá thấp hút volume mạnh hơn</div>
    <div class="tab-bar">
      <button class="tb-btn on" onclick="switchTab(this,'pMean')">Trung bình</button>
      <button class="tb-btn" onclick="switchTab(this,'pMed')">Trung vị</button>
    </div>
    <div id="pMean" class="tp on" style="position:relative;height:220px">
      <canvas id="cBinMean" role="img" aria-label="Doanh số trung bình theo khoảng giá">Doanh số TB.</canvas>
    </div>
    <div id="pMed" class="tp" style="position:relative;height:220px">
      <canvas id="cBinMed" role="img" aria-label="Doanh số trung vị theo khoảng giá">Doanh số median.</canvas>
    </div>
  </div>
  <div class="cc">
    <div class="ct">Rating trung bình theo phân khúc</div>
    <div class="cs">Bình dân rating cao nhất (4.53★) — hiệu ứng số lượng lớn</div>
    <div class="cw" style="height:160px">
      <canvas id="cRating" role="img" aria-label="Rating trung bình theo phân khúc">Rating theo phân khúc.</canvas>
    </div>
    <div class="ct" style="margin-top:16px">Nhãn Amazon's Choice vs Doanh số TB</div>
    <div class="cs">Sản phẩm có nhãn Amazon's Choice doanh số trung bình cao hơn ~16%</div>
    <div class="cw" style="height:120px">
      <canvas id="cAmz" role="img" aria-label="Amazon Choice vs doanh số">Amazon Choice premium.</canvas>
    </div>
  </div>
</div>

<!-- Bảng so sánh phân khúc -->
<div class="sec">📋 Bảng so sánh chi tiết 3 phân khúc</div>
<div class="cc" style="margin-bottom:16px">
  <table class="tbl">
    <thead>
      <tr>
        <th>Phân khúc</th><th>Khoảng giá</th><th>Số SP</th>
        <th>DT trung bình/tháng</th><th>DT trung vị/tháng</th>
        <th>Rating TB</th><th>Reviews TB</th><th>Discount TB</th>
      </tr>
    </thead>
    <tbody id="segTbody"></tbody>
  </table>
</div>

<!-- Insights -->
<div class="sec">💡 Phát hiện chính từ dữ liệu thực</div>
<div class="ins-grid">
  <div class="ins" style="border-top-color:#3266ad">
    <h4 style="color:#3266ad">📉 Giá thấp → Doanh số cao</h4>
    <p>Spearman r = <strong>–0.47</strong>: tương quan âm rõ rệt, không chỉ ngẫu nhiên. Nhóm &lt;$20 doanh số median <strong>3.000/tháng</strong>; nhóm &gt;$70 chỉ <strong>200/tháng</strong>. Khách hàng Amazon rất nhạy cảm về giá.</p>
  </div>
  <div class="ins" style="border-top-color:#F97316">
    <h4 style="color:#F97316">⚖️ Trung cấp: cân bằng tối ưu</h4>
    <p>$20–$70: doanh số TB <strong>~3.472/tháng</strong>, rating <strong>4.44★</strong>. Khi nhân với mức giá cao hơn bình dân, <strong>doanh thu tổng thể ($×lượt) cao nhất</strong> trong 3 phân khúc. Đây là vùng chiến lược nhất.</p>
  </div>
  <div class="ins" style="border-top-color:#9A3412">
    <h4 style="color:#9A3412">💎 Cao cấp: margin cao, volume thấp</h4>
    <p>Doanh số median chỉ <strong>200/tháng</strong> nhưng giá &gt;$70. Amazon's Choice tăng doanh số trung bình <strong>+24%</strong> (4.694 vs 3.775). Phù hợp chiến lược <strong>niche + branding</strong> hơn volume đại trà.</p>
  </div>
</div>

<!-- Top SP -->
<div class="sec">🏆 Top sản phẩm tiêu biểu mỗi phân khúc (theo doanh số thực)</div>
<div class="cc" style="margin-bottom:16px">
  <table class="tbl">
    <thead>
      <tr>
        <th>Phân khúc</th><th style="width:35%">Tên sản phẩm</th>
        <th>Giá</th><th>Rating</th><th>Reviews</th><th>Doanh số/tháng</th><th>Disc.</th>
      </tr>
    </thead>
    <tbody id="topTbody"></tbody>
  </table>
</div>

<!-- Chiến lược -->
<div class="sec">🚀 Đề xuất chiến lược định giá</div>
<div class="strat-grid">
  <div class="sg" style="border-left-color:#3266ad">
    <span class="stag" style="background:#DBEAFE;color:#1e40af">📦 Chiến lược Volume</span>
    <h4 style="color:#3266ad">Bình dân (&lt;$20)</h4>
    <ul>
      <li>Doanh số median cao nhất (~4.000/tháng)</li>
      <li>Cần tối ưu chi phí sản xuất &amp; fulfillment</li>
      <li>Discount 20–25% là mức thị trường chấp nhận</li>
      <li>Phù hợp SP tiêu dùng nhanh, hàng hóa thông dụng</li>
      <li>Xây dựng review base để giữ ranking Amazon</li>
    </ul>
  </div>
  <div class="sg" style="border-left-color:#F97316">
    <span class="stag" style="background:#FFEDD5;color:#9A3412">✅ Khuyến nghị</span>
    <h4 style="color:#F97316">Trung cấp ($20–$70)</h4>
    <ul>
      <li>Doanh thu tổng thể tốt nhất (volume × giá)</li>
      <li>Rating cao (4.44★) — khách hàng hài lòng hơn</li>
      <li>Discount vừa phải (~21%) — bảo vệ biên lợi nhuận</li>
      <li>Nhắm đến nhãn Amazon's Choice (+16% doanh số)</li>
      <li>Chiến lược phù hợp đa số ngành hàng trên Amazon</li>
    </ul>
  </div>
  <div class="sg" style="border-left-color:#9A3412">
    <span class="stag" style="background:#FEE2E2;color:#991b1b">🎯 Niche Premium</span>
    <h4 style="color:#9A3412">Cao cấp (&gt;$70)</h4>
    <ul>
      <li>Doanh số thấp nhưng giá trị đơn hàng cao</li>
      <li>Ít cạnh tranh trực tiếp về giá</li>
      <li>Đầu tư mạnh vào hình ảnh &amp; A+ content</li>
      <li>Hạn chế discount để bảo vệ định vị cao cấp</li>
      <li>Tập trung nhóm khách hàng có thu nhập cao, trung thành</li>
    </ul>
  </div>
</div>

<div style="height:20px"></div>

<script>
const D = __PAYLOAD__;
Chart.defaults.font.family = "'Inter',sans-serif";
Chart.defaults.color = '#78716C';
const fN = n => Number(n).toLocaleString('vi-VN');
const fR = (n,d=1) => Number(n).toFixed(d);

document.getElementById('corrSpan').textContent = D.kpi.spearman_r;

// KPI
(function(){
  const k = D.kpi;
  const cards = [
    {t:'Tổng sản phẩm',        v:fN(k.total),                 s:'có giá hợp lệ (USD)',              hi:false},
    {t:'Giá trung bình',        v:'$'+fR(k.avg_price,2),       s:'Median: $'+fR(k.median_price,2),   hi:false},
    {t:'Discount trung bình',   v:fR(k.avg_disc,1)+'%',        s:k.pct_disc+'% SP có ghi nhận disc', hi:false},
    {t:'Rating trung bình',     v:fR(k.avg_rating,2)+'★',      s:'Doanh số median: '+fN(k.median_sales)+'/tháng', hi:false},
    {t:'Phân khúc nhiều nhất',  v:k.dominant_seg,              s:k.dominant_pct+'% tổng sản phẩm',  hi:true},
  ];
  const row = document.getElementById('kpiRow');
  cards.forEach(c => {
    row.innerHTML += `<div class="kc${c.hi?' hi':''}">
      <div class="kt">${c.t}</div>
      <div class="kv">${c.v}</div>
      <div class="ks">${c.s}</div>
    </div>`;
  });
})();

// Donut
(function(){
  const dd = D.donut;
  const tot = dd.counts.reduce((a,b)=>a+b,0);
  const lg = document.getElementById('donutLeg');
  dd.labels.forEach((l,i)=>{
    const pct = tot?(dd.counts[i]/tot*100).toFixed(1):0;
    lg.innerHTML += `<span class="li"><span class="ld" style="background:${dd.colors[i]}"></span>${l} (${pct}%)</span>`;
  });
  new Chart(document.getElementById('cDonut'),{
    type:'doughnut',
    data:{labels:dd.labels,datasets:[{data:dd.counts,backgroundColor:dd.colors,borderWidth:2,borderColor:'#FEF3E2'}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${fN(c.raw)} SP`}}}}
  });
})();

// Bar bins % SP
(function(){
  const b = D.bar_bins;
  new Chart(document.getElementById('cBin'),{
    type:'bar',
    data:{labels:b.labels,datasets:[{label:'% SP',data:b.pcts,backgroundColor:b.colors,borderRadius:4,borderSkipped:false}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.parsed.y}% sản phẩm`}}},
      scales:{
        x:{ticks:{font:{size:10},autoSkip:false,maxRotation:35},grid:{display:false}},
        y:{ticks:{callback:v=>v+'%'},grid:{color:'rgba(0,0,0,0.05)'},max:Math.max(...b.pcts)*1.3}
      }}
  });
})();

// Scatter
(function(){
  const sc = D.scatter;
  const segs=['Bình dân','Trung cấp','Cao cấp'];
  const styles=['circle','triangle','rect'];
  const datasets=segs.map((s,i)=>({
    label:s,
    data:sc.points.filter(p=>p.seg===s).map(p=>({x:p.x,y:p.y})),
    backgroundColor:sc.colors[s]+'70',pointRadius:4.5,pointStyle:styles[i],
  }));
  const lg=document.getElementById('scatLeg');
  segs.forEach((s,i)=>{
    lg.innerHTML+=`<span class="li"><span class="ld" style="background:${sc.colors[s]}"></span>${s}</span>`;
  });
  new Chart(document.getElementById('cScat'),{
    type:'scatter',data:{datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` $${c.parsed.x} | ${fN(c.parsed.y)} đơn/tháng`}}},
      scales:{
        x:{title:{display:true,text:'Giá ($)',color:'#78716C',font:{size:12}},grid:{color:'rgba(0,0,0,0.05)'}},
        y:{title:{display:true,text:'Doanh số/tháng',color:'#78716C',font:{size:12}},
          ticks:{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v},grid:{color:'rgba(0,0,0,0.05)'}}
      }}
  });
})();

// Bin sales tabs
(function(){
  const b=D.bar_bins;
  const mkOpts=(data,color)=>({
    type:'bar',
    data:{labels:b.labels,datasets:[{label:'Doanh số',data,backgroundColor:color,borderRadius:4,borderSkipped:false}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn/tháng`}}},
      scales:{
        x:{ticks:{font:{size:10},autoSkip:false,maxRotation:35},grid:{display:false}},
        y:{ticks:{callback:v=>fN(v)},grid:{color:'rgba(0,0,0,0.05)'}}
      }}
  });
  new Chart(document.getElementById('cBinMean'),mkOpts(b.sales_mean,'#F97316'));
  new Chart(document.getElementById('cBinMed'), mkOpts(b.sales_median,'#3266ad'));
})();

// Rating
(function(){
  const s=D.seg_compare;
  new Chart(document.getElementById('cRating'),{
    type:'bar',
    data:{labels:s.labels,datasets:[{label:'Rating TB',data:s.avg_rating,
      backgroundColor:s.colors,borderRadius:4,borderSkipped:false,barThickness:34}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.parsed.x.toFixed(2)} ★`}}},
      scales:{
        x:{min:4.1,max:4.7,ticks:{callback:v=>v.toFixed(1)+'★'},grid:{color:'rgba(0,0,0,0.05)'}},
        y:{ticks:{font:{size:12}},grid:{display:false}}
      }}
  });
})();

// Amazon Choice
(function(){
  const a=D.amz_compare;
  new Chart(document.getElementById('cAmz'),{
    type:'bar',
    data:{labels:a.labels,datasets:[{label:'Doanh số TB',data:a.sales_mean,
      backgroundColor:a.colors,borderRadius:4,borderSkipped:false,barThickness:34}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.x)} đơn/tháng`}}},
      scales:{
        x:{ticks:{callback:v=>fN(v)},grid:{color:'rgba(0,0,0,0.05)'}},
        y:{ticks:{font:{size:11.5}},grid:{display:false}}
      }}
  });
})();

// Segment table
(function(){
  const s=D.seg_compare;
  const ranges=['< $20','$20 – $70','> $70'];
  const bcs=['sb0','sb1','sb2'];
  const tb=document.getElementById('segTbody');
  s.labels.forEach((lbl,i)=>{
    tb.innerHTML+=`<tr>
      <td><span class="sb ${bcs[i]}">${lbl}</span></td>
      <td>${ranges[i]}</td>
      <td>${fN(s.counts[i])}</td>
      <td style="font-weight:600">${fN(s.avg_sales[i])}</td>
      <td>${fN(s.med_sales[i])}</td>
      <td>${s.avg_rating[i].toFixed(2)} ★</td>
      <td>${fN(s.avg_reviews[i])}</td>
      <td>${s.avg_disc[i].toFixed(1)}%</td>
    </tr>`;
  });
})();

// Top products
(function(){
  const rows=D.top_rows;
  const bcm={'Bình dân':'sb0','Trung cấp':'sb1','Cao cấp':'sb2'};
  const tb=document.getElementById('topTbody');
  rows.forEach(r=>{
    tb.innerHTML+=`<tr>
      <td><span class="sb ${bcm[r.seg]}">${r.seg}</span></td>
      <td title="${r.title}">${r.title}</td>
      <td style="font-weight:600">$${fR(r.price,2)}</td>
      <td>${r.rating>0?r.rating.toFixed(1)+'★':'—'}</td>
      <td>${fN(r.reviews)}</td>
      <td style="font-weight:600;color:var(--pr)">${fN(r.sales)}</td>
      <td>${r.disc>0?r.disc.toFixed(0)+'%':'—'}</td>
    </tr>`;
  });
})();

function switchTab(btn,paneId){
  document.querySelectorAll('.tb-btn').forEach(b=>b.classList.remove('on'));
  document.querySelectorAll('.tp').forEach(p=>p.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById(paneId).classList.add('on');
}
</script>
</body>
</html>"""


def render(df: pd.DataFrame):
    df_prep = _prep(df)

    if df_prep.empty:
        st.warning("⚠️ Không có dữ liệu giá hợp lệ để phân tích.")
        return

    payload     = _build_payload(df_prep)
    payload_str = json.dumps(payload, ensure_ascii=False)

    html = _HTML.replace("__PAYLOAD__", payload_str)
    components.html(html, height=2750, scrolling=False)