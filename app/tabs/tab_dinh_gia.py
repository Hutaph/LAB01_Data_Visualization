"""
Tab Định Giá — Pricing Strategy Analysis
Câu hỏi: Giá cả ảnh hưởng thế nào đến doanh số? Phân khúc nào được ưa chuộng nhất?
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
    # Bin distribution
    bins=[0,5,10,15,20,30,50,70,100,200,9999]
    bl=["<$5","$5-10","$10-15","$15-20","$20-30","$30-50","$50-70","$70-100","$100-200",">$200"]
    # Tối giản hoàn toàn: Dùng 1 màu duy nhất vì trục X đã thể hiện rõ mốc giá
    bc2=["#3266ad"] * len(bl)
    df["_b"]=pd.cut(df["current_price"],bins=bins,labels=bl,right=False)
    bct=df["_b"].value_counts().reindex(bl,fill_value=0)
    bpct=(bct/t*100).round(1)
    bsm=df.groupby("_b",observed=True)["sales_vol"].median().reindex(bl).fillna(0)
    bar=dict(labels=bl,pcts=bpct.tolist(),colors=bc2,sales_med=[int(x) for x in bsm])
    # Discount
    db=[-1,0,15,30,100]; dl=["Không giảm","Giảm <15%","Giảm 15-30%","Giảm >30%"]
    df["_d"]=pd.cut(df["discount_pct"],bins=db,labels=dl)
    da=df.groupby("_d",observed=True)["sales_vol"].median().reindex(dl).fillna(0)
    disc=dict(labels=dl,med=[int(x) for x in da])
    # Scatter
    st2=df[(df["current_price"]<=200)&(df["sales_vol"]>0)].copy()
    if len(st2)>500: st2=st2.sample(500,random_state=42)
    scat=dict(pts=[dict(x=round(float(r["current_price"]),2),y=int(r["sales_vol"]),s=r["segment"]) for _,r in st2.iterrows()],colors=SC)
    # Segment table
    sa=df.groupby("segment").agg(as2=("sales_vol","mean"),ms=("sales_vol","median"),ar=("rating","mean"),ad=("discount_pct","mean"),c=("current_price","count")).reindex(SO).fillna(0)
    seg=dict(labels=SO,avg_s=[int(sa.loc[s,"as2"]) for s in SO],med_s=[int(sa.loc[s,"ms"]) for s in SO],
        avg_r=[round(float(sa.loc[s,"ar"]),2) for s in SO],avg_d=[round(float(sa.loc[s,"ad"]),1) for s in SO],
        cnt=[int(sa.loc[s,"c"]) for s in SO])
    # Top products
    tr=[]
    for s in SO:
        sub=df[df["segment"]==s].copy()
        sc2="sales_vol" if sub["sales_vol"].sum()>0 else "reviews"
        for _,r in sub.nlargest(3,sc2).iterrows():
            tt=str(r.get("title","—")); tt=tt[:55]+"…" if len(tt)>55 else tt
            tr.append(dict(seg=s,title=tt,price=round(float(r["current_price"]),2),rating=round(float(r["rating"]),1),sales=int(r["sales_vol"]),disc=round(float(r["discount_pct"]),0)))
    return dict(kpi=kpi,donut=donut,bar=bar,seg=seg,scat=scat,disc=disc,top=tr,sc=SC)

_HTML=r"""<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--pr:#F97316;--dk:#9A3412;--bg:#FEF3E2;--card:#FFFFFF;--t1:#1C1917;--t2:#78716C;--t3:#A8A29E;--bd:#E7E5E4;--r:8px;--fn:'Inter',sans-serif;--ft:'Montserrat',sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);font-family:var(--fn);color:var(--t1);padding:16px;height:100vh;overflow:hidden;display:flex;flex-direction:column}
.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px;flex-shrink:0}
.kc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:12px 14px;border-left:3px solid var(--pr);}
.kc.hi{border-left-color:var(--dk);background:#FFF7ED}
.kt{font-size:10px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.kv{font-family:var(--ft);font-size:20px;font-weight:700;color:var(--t1);margin-bottom:2px}
.ks{font-size:10.5px;color:var(--t3)}
.kc.hi .kv{color:var(--dk)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px;flex:1;min-height:0}
.cc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:14px 16px;display:flex;flex-direction:column}
.ct{font-size:13px;font-weight:600;color:var(--t1);margin-bottom:2px}
.cs{font-size:11px;color:var(--t2);margin-bottom:10px}
.cw{position:relative;flex:1;min-height:0}
.leg{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px}
.li{display:flex;align-items:center;gap:4px;font-size:11px;color:var(--t2);font-weight:500}
.ld{width:10px;height:10px;border-radius:2px;flex-shrink:0}
</style></head><body>

<div class="kpi-row" id="kpiRow"></div>

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
const D=__PAYLOAD__;
Chart.defaults.font.family="'Inter',sans-serif";Chart.defaults.color='#78716C';
const fN=n=>Number(n).toLocaleString('vi-VN');
const fR=(n,d=1)=>Number(n).toFixed(d);

// KPI
(()=>{const k=D.kpi;const c=[
{t:'Giá niêm yết TB',v:'$'+fR(k.avg_price,2),s:'Trung vị: $'+fR(k.median_price,2)},
{t:'Phân khúc ưu thế',v:k.dom_seg,s:'Chiếm '+k.dom_pct+'% thị phần',hi:1},
{t:'Tương quan Giá–Cầu',v:k.spearman,s:'Spearman (Âm = nghịch biến)'},
{t:'SP có giảm giá',v:k.pct_disc+'%',s:'Mức giảm TB: '+fR(k.avg_disc,1)+'%'},
{t:'Tổng sản phẩm',v:fN(k.total),s:'Có giá bán hợp lệ'},
];const r=document.getElementById('kpiRow');
c.forEach(x=>{r.innerHTML+=`<div class="kc${x.hi?' hi':''}"><div class="kt">${x.t}</div><div class="kv">${x.v}</div><div class="ks">${x.s}</div></div>`;});})();

// Donut
(()=>{const d=D.donut,t=d.counts.reduce((a,b)=>a+b,0),l=document.getElementById('dLeg');
d.labels.forEach((lb,i)=>{const p=t?(d.counts[i]/t*100).toFixed(1):0;
l.innerHTML+=`<span class="li"><span class="ld" style="background:${d.colors[i]}"></span>${lb} (${p}%)</span>`;});
new Chart(document.getElementById('cDonut'),{type:'doughnut',
data:{labels:d.labels,datasets:[{data:d.counts,backgroundColor:d.colors,borderWidth:0}]},
options:{responsive:true,maintainAspectRatio:false,cutout:'65%',
plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${fN(c.raw)} SP`}}}}});})();

// Scatter
(()=>{const s=D.scat,segs=['Bình dân','Trung cấp','Cao cấp'];
const ds=segs.map(sg=>({label:sg,data:s.pts.filter(p=>p.s===sg).map(p=>({x:p.x,y:p.y})),backgroundColor:s.colors[sg]+'60',pointRadius:4}));
const l=document.getElementById('sLeg');segs.forEach(sg=>{l.innerHTML+=`<span class="li"><span class="ld" style="background:${s.colors[sg]}"></span>${sg}</span>`;});
new Chart(document.getElementById('cScat'),{type:'scatter',data:{datasets:ds},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` $${c.parsed.x} | ${fN(c.parsed.y)} đơn`}}},
scales:{x:{title:{display:true,text:'Giá ($)',font:{size:11}},grid:{color:'rgba(0,0,0,0.04)'},ticks:{font:{size:10}}},
y:{title:{display:true,text:'Doanh số',font:{size:11}},ticks:{font:{size:10},callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v},grid:{color:'rgba(0,0,0,0.04)'}}}}});})();

// Bin Sales
(()=>{const b=D.bar;new Chart(document.getElementById('cBinSales'),{type:'bar',
data:{labels:b.labels,datasets:[{data:b.sales_med,backgroundColor:'#F97316',borderRadius:3}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn`}}},
scales:{x:{ticks:{font:{size:10},maxRotation:45},grid:{display:false}},y:{ticks:{font:{size:10},callback:v=>fN(v)},grid:{color:'rgba(0,0,0,0.04)'}}}}});})();

// Discount
(()=>{const d=D.disc;new Chart(document.getElementById('cDisc'),{type:'bar',
data:{labels:d.labels,datasets:[{data:d.med,backgroundColor:'#9A3412',borderRadius:3}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn`}}},
scales:{x:{grid:{display:false},ticks:{font:{size:11}}},y:{grid:{color:'rgba(0,0,0,0.04)'},ticks:{font:{size:10},callback:v=>fN(v)}}}}});})();
</script></body></html>"""

def render(df):
    d=_prep(df)
    if d.empty: st.warning("Không có dữ liệu giá hợp lệ."); return
    p=_payload(d)
    # Tối ưu height cho 1 màn hình duy nhất
    components.html(_HTML.replace("__PAYLOAD__",json.dumps(p,ensure_ascii=False)),height=720,scrolling=False)