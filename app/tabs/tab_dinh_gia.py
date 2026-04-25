"""
Tab Định Giá — Pricing Strategy Analysis
Câu hỏi: Giá cả ảnh hưởng thế nào đến doanh số? Phân khúc nào được ưa chuộng nhất?

Filter nằm hoàn toàn trong HTML/JS — không dùng st.selectbox.
Toàn bộ data truyền xuống 1 lần, filter chạy client-side.
"""
import json, pandas as pd, numpy as np, streamlit as st
import streamlit.components.v1 as components


def _prep(df):
    o = df.copy()
    ps = "current_price" if "current_price" in o.columns else "price"
    o["current_price"] = pd.to_numeric(o.get(ps, pd.Series()), errors="coerce").fillna(0)
    o["original_price"] = pd.to_numeric(o.get("original_price", pd.Series()), errors="coerce").fillna(0)
    m = (o["original_price"] > o["current_price"]) & (o["original_price"] > 0) & (o["current_price"] > 0)
    o["discount_pct"] = 0.0
    o.loc[m, "discount_pct"] = ((o.loc[m,"original_price"]-o.loc[m,"current_price"])/o.loc[m,"original_price"]*100).clip(0,80)
    o["rating"] = pd.to_numeric(o.get("rating", pd.Series(dtype=float)), errors="coerce").fillna(0)
    o["reviews"] = pd.to_numeric(o.get("reviews", pd.Series(dtype=int)), errors="coerce").fillna(0).astype(int)
    sv = "sales_volume_num" if "sales_volume_num" in o.columns else None
    o["sales_vol"] = pd.to_numeric(o[sv], errors="coerce").fillna(0) if sv else 0.0
    o = o[o["current_price"] > 0].copy()
    o["segment"] = o["current_price"].apply(lambda p: "Bình dân" if p<20 else ("Trung cấp" if p<=70 else "Cao cấp"))
    return o


def _payload(df):
    SO = ["Bình dân","Trung cấp","Cao cấp"]
    SC = {"Bình dân":"#3266ad","Trung cấp":"#F97316","Cao cấp":"#9A3412"}
    t = len(df)
    sc = df["segment"].value_counts()
    vc = df[df["sales_vol"]>0][["current_price","sales_vol"]]
    sp = float(vc["current_price"].corr(vc["sales_vol"],method="spearman")) if len(vc)>30 else 0.0
    dd = df[df["discount_pct"]>0]
    kpi = dict(total=t, avg_price=round(float(df["current_price"].mean()),2),
        median_price=round(float(df["current_price"].median()),2),
        avg_disc=round(float(dd["discount_pct"].mean()),1) if len(dd)>0 else 0.0,
        pct_disc=round(float(len(dd)/t*100),1),
        dom_seg=sc.idxmax(), dom_pct=round(float(sc.max()/t*100),1), spearman=round(sp,3))
    donut = dict(labels=SO, counts=[int(sc.get(s,0)) for s in SO], colors=[SC[s] for s in SO])
    bins=[0,5,10,15,20,30,50,70,100,200,9999]
    bl=["<$5","$5-10","$10-15","$15-20","$20-30","$30-50","$50-70","$70-100","$100-200",">$200"]
    bc2=["#3266ad"] * len(bl)
    df["_b"]=pd.cut(df["current_price"],bins=bins,labels=bl,right=False)
    bct=df["_b"].value_counts().reindex(bl,fill_value=0)
    bpct=(bct/t*100).round(1)
    bsm=df.groupby("_b",observed=True)["sales_vol"].median().reindex(bl).fillna(0)
    bar=dict(labels=bl,pcts=bpct.tolist(),colors=bc2,sales_med=[int(x) for x in bsm])
    db=[-1,0,15,30,100]; dl=["Không giảm","Giảm <15%","Giảm 15-30%","Giảm >30%"]
    df["_d"]=pd.cut(df["discount_pct"],bins=db,labels=dl)
    da=df.groupby("_d",observed=True)["sales_vol"].median().reindex(dl).fillna(0)
    disc=dict(labels=dl,med=[int(x) for x in da])
    st2=df[(df["current_price"]<=200)&(df["sales_vol"]>0)].copy()
    if len(st2)>500: st2=st2.sample(500,random_state=42)
    scat=dict(pts=[dict(x=round(float(r["current_price"]),2),y=int(r["sales_vol"]),s=r["segment"]) for _,r in st2.iterrows()],colors=SC)
    sa=df.groupby("segment").agg(as2=("sales_vol","mean"),ms=("sales_vol","median"),ar=("rating","mean"),ad=("discount_pct","mean"),c=("current_price","count")).reindex(SO).fillna(0)
    seg=dict(labels=SO,avg_s=[int(sa.loc[s,"as2"]) for s in SO],med_s=[int(sa.loc[s,"ms"]) for s in SO],
        avg_r=[round(float(sa.loc[s,"ar"]),2) for s in SO],avg_d=[round(float(sa.loc[s,"ad"]),1) for s in SO],
        cnt=[int(sa.loc[s,"c"]) for s in SO])
    tr=[]
    for s in SO:
        sub=df[df["segment"]==s].copy()
        sc2="sales_vol" if sub["sales_vol"].sum()>0 else "reviews"
        for _,r in sub.nlargest(3,sc2).iterrows():
            tt=str(r.get("title","—")); tt=tt[:55]+"…" if len(tt)>55 else tt
            tr.append(dict(seg=s,title=tt,price=round(float(r["current_price"]),2),rating=round(float(r["rating"]),1),sales=int(r["sales_vol"]),disc=round(float(r["discount_pct"]),0)))
    return dict(kpi=kpi,donut=donut,bar=bar,seg=seg,scat=scat,disc=disc,top=tr,sc=SC)


def _all_rows(df):
    """Truyền toàn bộ rows thô xuống JS để filter client-side."""
    rows = []
    for _, r in df.iterrows():
        rows.append(dict(
            price=round(float(r["current_price"]), 2),
            rating=round(float(r["rating"]), 2),
            disc=round(float(r["discount_pct"]), 1),
            sales=int(r["sales_vol"]),
            seg=r["segment"],
        ))
    return rows


_HTML = r"""<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--pr:#F97316;--dk:#9A3412;--bg:#FEF3E2;--card:#FFFFFF;--t1:#1C1917;--t2:#78716C;--t3:#A8A29E;--bd:#E7E5E4;--r:8px;--fn:'Inter',sans-serif;--ft:'Montserrat',sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);font-family:var(--fn);color:var(--t1);padding:6px 14px 8px;height:100vh;overflow:hidden;display:flex;flex-direction:column;gap:8px}

/* ── FILTER BAR ── */
.fb{
  display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;
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
.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;flex-shrink:0}
.kc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:10px 14px;border-left:3px solid var(--pr);}
.kc.hi{border-left-color:var(--dk);background:#FFF7ED}
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
</style></head><body>

<!-- FILTER BAR -->
<div class="fb">
  <div class="fb-item">
    <label>Phân khúc giá</label>
    <select id="fSeg">
      <option value="all">Tất cả</option>
      <option value="Bình dân">Bình dân (&lt;$20)</option>
      <option value="Trung cấp">Trung cấp ($20–$70)</option>
      <option value="Cao cấp">Cao cấp (&gt;$70)</option>
    </select>
  </div>
  <div class="fb-item">
    <label>Khuyến mãi</label>
    <select id="fDisc">
      <option value="all">Tất cả</option>
      <option value="on">Đang giảm giá</option>
      <option value="off">Không giảm giá</option>
    </select>
  </div>
  <div class="fb-item">
    <label>Rating tối thiểu</label>
    <select id="fStar">
      <option value="0">Tất cả</option>
      <option value="3">3.0+</option>
      <option value="4">4.0+</option>
      <option value="4.5">4.5+</option>
    </select>
  </div>
</div>

<!-- KPI -->
<div class="kpi-row" id="kpiRow"></div>

<!-- CHARTS -->
<div class="g2">
  <div class="cc">
    <div class="ct">Thị phần theo phân khúc giá</div>
    <div class="cs">Tỷ trọng số lượng sản phẩm niêm yết trong mỗi phân khúc</div>
    <div class="leg" id="dLeg"></div>
    <div class="cw"><canvas id="cDonut"></canvas></div>
  </div>
  <div class="cc">
    <div class="ct">Tương quan Giá — Doanh số</div>
    <div class="cs">Mỗi điểm = 1 sản phẩm. Xu hướng giảm rõ rệt khi giá tăng.</div>
    <div class="leg" id="sLeg"></div>
    <div class="cw"><canvas id="cScat"></canvas></div>
  </div>
  <div class="cc">
    <div class="ct">Doanh số trung vị theo mốc giá</div>
    <div class="cs">Hiệu suất bán hàng thực tế tại từng khung giá</div>
    <div class="cw"><canvas id="cBinSales"></canvas></div>
  </div>
  <div class="cc">
    <div class="ct">Tác động của mức giảm giá lên doanh số</div>
    <div class="cs">Doanh số trung vị theo nhóm % giảm giá so với giá gốc</div>
    <div class="cw"><canvas id="cDisc"></canvas></div>
  </div>
</div>

<script>
const ALL_ROWS = __ALL_ROWS__;
const SC = {"Bình dân":"#3266ad","Trung cấp":"#F97316","Cao cấp":"#9A3412"};
const SO = ["Bình dân","Trung cấp","Cao cấp"];
const BL = ["<$5","$5-10","$10-15","$15-20","$20-30","$30-50","$50-70","$70-100","$100-200",">$200"];
const BINS = [0,5,10,15,20,30,50,70,100,200,Infinity];
const DL = ["Không giảm","Giảm <15%","Giảm 15-30%","Giảm >30%"];

Chart.defaults.font.family="'Inter',sans-serif"; Chart.defaults.color='#78716C';
const fN = n => Number(n).toLocaleString('vi-VN');
const fR = (n,d=1) => Number(n).toFixed(d);
const avg = a => a.length ? a.reduce((x,y)=>x+y,0)/a.length : 0;
const median = a => { if(!a.length) return 0; const s=[...a].sort((x,y)=>x-y),m=Math.floor(s.length/2); return s.length%2?s[m]:(s[m-1]+s[m])/2; };

let charts = {};
function destroy() { Object.values(charts).forEach(c=>c&&c.destroy()); charts={}; }

function render(rows) {
  destroy();
  if (!rows.length) return;

  const t = rows.length;
  const prices = rows.map(r=>r.price);
  const segCnt = {}; SO.forEach(s=>segCnt[s]=0);
  rows.forEach(r=>{ if(segCnt[r.seg]!==undefined) segCnt[r.seg]++; });
  const domSeg = SO.reduce((a,b)=>segCnt[a]>=segCnt[b]?a:b);

  // Spearman
  const wSales = rows.filter(r=>r.sales>0);
  let sp = 0;
  if (wSales.length>30) {
    const rank = a => { const s=[...a].map((v,i)=>({v,i})).sort((x,y)=>x.v-y.v),r=new Array(a.length); s.forEach((x,i)=>r[x.i]=i+1); return r; };
    const px=wSales.map(r=>r.price), py=wSales.map(r=>r.sales);
    const rx=rank(px), ry=rank(py), n=rx.length;
    const mx=avg(rx), my=avg(ry);
    let num=0,dx2=0,dy2=0;
    for(let i=0;i<n;i++){num+=(rx[i]-mx)*(ry[i]-my);dx2+=(rx[i]-mx)**2;dy2+=(ry[i]-my)**2;}
    sp = dx2&&dy2 ? +(num/Math.sqrt(dx2*dy2)).toFixed(3) : 0;
  }

  const discRows = rows.filter(r=>r.disc>0);
  const avgDisc = discRows.length ? +avg(discRows.map(r=>r.disc)).toFixed(1) : 0;
  const pctDisc = +(discRows.length/t*100).toFixed(1);
  const avgPrice = +avg(prices).toFixed(2);
  const medPrice = +median(prices).toFixed(2);

  // KPI
  const kpis = [
    {t:'Giá niêm yết TB',   v:'$'+fR(avgPrice,2),  s:'Trung vị: $'+fR(medPrice,2)},
    {t:'Phân khúc ưu thế',  v:domSeg,              s:'Chiếm '+(segCnt[domSeg]/t*100).toFixed(1)+'% thị phần', hi:1},
    {t:'Tương quan Giá–Cầu',v:sp,                  s:'Spearman (Âm = nghịch biến)'},
    {t:'SP có giảm giá',    v:pctDisc+'%',          s:'Mức giảm TB: '+fR(avgDisc,1)+'%'},
    {t:'Tổng sản phẩm',     v:fN(t),                s:'Có giá bán hợp lệ'},
  ];
  const kRow = document.getElementById('kpiRow');
  kRow.innerHTML = kpis.map(x=>`<div class="kc${x.hi?' hi':''}"><div class="kt">${x.t}</div><div class="kv">${x.v}</div><div class="ks">${x.s}</div></div>`).join('');

  // Donut
  const dCounts = SO.map(s=>segCnt[s]);
  const dTotal  = dCounts.reduce((a,b)=>a+b,0);
  document.getElementById('dLeg').innerHTML = SO.map((lb,i)=>`<span class="li"><span class="ld" style="background:${SC[lb]}"></span>${lb} (${dTotal?(dCounts[i]/dTotal*100).toFixed(1):0}%)</span>`).join('');
  charts.donut = new Chart(document.getElementById('cDonut'),{type:'doughnut',
    data:{labels:SO,datasets:[{data:dCounts,backgroundColor:SO.map(s=>SC[s]),borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'65%',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${fN(c.raw)} SP`}}}}});

  // Scatter
  const segs = SO;
  document.getElementById('sLeg').innerHTML = segs.map(sg=>`<span class="li"><span class="ld" style="background:${SC[sg]}"></span>${sg}</span>`).join('');
  let scPts = rows.filter(r=>r.sales>0&&r.price<=200);
  if(scPts.length>500) scPts=scPts.sort(()=>Math.random()-.5).slice(0,500);
  charts.scat = new Chart(document.getElementById('cScat'),{type:'scatter',
    data:{datasets:segs.map(sg=>({label:sg,data:scPts.filter(r=>r.seg===sg).map(r=>({x:r.price,y:r.sales})),backgroundColor:SC[sg]+'60',pointRadius:4}))},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` $${c.parsed.x} | ${fN(c.parsed.y)} đơn`}}},
      scales:{x:{title:{display:true,text:'Giá ($)',font:{size:11}},grid:{color:'rgba(0,0,0,0.04)'},ticks:{font:{size:10}}},
              y:{title:{display:true,text:'Doanh số',font:{size:11}},ticks:{font:{size:10},callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v},grid:{color:'rgba(0,0,0,0.04)'}}}}});

  // Bin Sales
  const binBuckets = BL.map(()=>[]);
  rows.forEach(r=>{ for(let i=0;i<BINS.length-1;i++){if(r.price>=BINS[i]&&r.price<BINS[i+1]){binBuckets[i].push(r.sales);break;}} });
  charts.bin = new Chart(document.getElementById('cBinSales'),{type:'bar',
    data:{labels:BL,datasets:[{data:binBuckets.map(b=>Math.round(median(b))),backgroundColor:'#F97316',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn`}}},
      scales:{x:{title:{display:true,text:'Khoảng giá ($)',font:{size:11}},ticks:{font:{size:10},maxRotation:45},grid:{display:false}},
              y:{title:{display:true,text:'Doanh số trung vị',font:{size:11}},ticks:{font:{size:10},callback:v=>fN(v)},grid:{color:'rgba(0,0,0,0.04)'}}}}});

  // Discount
  const dBands = [[],[],[],[]];
  rows.forEach(r=>{ if(r.disc===0)dBands[0].push(r.sales); else if(r.disc<15)dBands[1].push(r.sales); else if(r.disc<=30)dBands[2].push(r.sales); else dBands[3].push(r.sales); });
  charts.disc = new Chart(document.getElementById('cDisc'),{type:'bar',
    data:{labels:DL,datasets:[{data:dBands.map(b=>Math.round(median(b))),backgroundColor:'#9A3412',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn`}}},
      scales:{x:{title:{display:true,text:'Mức giảm giá',font:{size:11}},grid:{display:false},ticks:{font:{size:11}}},
              y:{title:{display:true,text:'Doanh số trung vị',font:{size:11}},grid:{color:'rgba(0,0,0,0.04)'},ticks:{font:{size:10},callback:v=>fN(v)}}}}});
}

function applyFilters() {
  const seg  = document.getElementById('fSeg').value;
  const disc = document.getElementById('fDisc').value;
  const star = parseFloat(document.getElementById('fStar').value);
  let rows = ALL_ROWS;
  if (seg  !== 'all') rows = rows.filter(r => r.seg === seg);
  if (disc === 'on')  rows = rows.filter(r => r.disc > 0);
  if (disc === 'off') rows = rows.filter(r => r.disc === 0);
  if (star > 0)       rows = rows.filter(r => r.rating >= star);
  render(rows);
}

['fSeg','fDisc','fStar'].forEach(id => document.getElementById(id).addEventListener('change', applyFilters));
render(ALL_ROWS);
</script></body></html>"""


def render(df):
    st.markdown("<style>.block-container{padding-top:.4rem!important;}</style>", unsafe_allow_html=True)

    d = _prep(df)
    if d.empty:
        st.warning("Không có dữ liệu giá hợp lệ.")
        return

    # Truyền toàn bộ rows xuống JS, filter chạy client-side
    rows = []
    for _, r in d.iterrows():
        rows.append(dict(
            price=round(float(r["current_price"]), 2),
            rating=round(float(r["rating"]), 2),
            disc=round(float(r["discount_pct"]), 1),
            sales=int(r["sales_vol"]),
            seg=r["segment"],
        ))

    html = _HTML.replace("__ALL_ROWS__", json.dumps(rows, ensure_ascii=False))
    components.html(html, height=650, scrolling=False)