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
body{background:var(--bg);font-family:var(--fn);color:var(--t1);padding:20px;overflow-y:auto;overflow-x:hidden}
.intro{background:linear-gradient(135deg,#FFF7ED,#FFEDD5);border:1px solid #FED7AA;border-left:4px solid var(--pr);border-radius:var(--r);padding:14px 18px;margin-bottom:22px}
.intro-text{font-size:13px;color:#7c3f00;line-height:1.55}
.sec{font-family:var(--ft);font-size:11.5px;font-weight:700;color:var(--dk);text-transform:uppercase;letter-spacing:.8px;margin:22px 0 12px;display:flex;align-items:center;gap:8px}
.sec::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,#FED7AA,transparent)}
.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:22px}
.kc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:14px 16px;border-left:3px solid var(--pr);transition:transform .15s}
.kc:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(249,115,22,.12)}
.kc.hi{border-left-color:var(--dk);background:#FFF7ED}
.kt{font-size:10.5px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px}
.kv{font-family:var(--ft);font-size:22px;font-weight:700;color:var(--t1);margin-bottom:3px}
.ks{font-size:11px;color:var(--t3)}
.kc.hi .kv{color:var(--dk)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.cc{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:18px 20px}
.ct{font-size:14px;font-weight:600;color:var(--t1);margin-bottom:4px}
.cs{font-size:12px;color:var(--t2);margin-bottom:14px}
.cw{position:relative;width:100%}
.leg{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:12px}
.li{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--t2);font-weight:500}
.ld{width:10px;height:10px;border-radius:2px;flex-shrink:0}
.sb{display:inline-block;font-size:10.5px;font-weight:600;padding:4px 10px;border-radius:12px;white-space:nowrap}
.sb0{background:#DBEAFE;color:#1e40af}.sb1{background:#FFEDD5;color:#9A3412}.sb2{background:#FEE2E2;color:#991b1b}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.tbl thead th{text-align:left;font-size:11px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;padding:10px 12px;border-bottom:1px solid var(--bd);background:#FAFAF9}
.tbl tbody td{padding:10px 12px;border-bottom:1px solid var(--bd);vertical-align:middle}
.tbl tbody tr:last-child td{border-bottom:none}
.ins-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.ins{background:var(--card);border-radius:var(--r);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:18px;border-left:3px solid}
.ins h4{font-size:13.5px;font-weight:600;margin-bottom:8px}
.ins p{font-size:12px;color:var(--t2);line-height:1.65}
.ins .val{font-family:var(--ft);font-weight:700;color:var(--t1)}
</style></head><body>
<div class="intro"><div class="intro-text">
<strong>Phân tích Chiến lược Định giá</strong> — Dữ liệu <strong id="iTotal"></strong> sản phẩm Amazon.
Phân khúc: Bình dân &lt;$20 · Trung cấp $20–$70 · Cao cấp &gt;$70.
Hệ số tương quan Spearman (Giá vs Doanh số) = <strong id="iCorr"></strong> — giá càng thấp, doanh số càng cao.
</div></div>

<div class="kpi-row" id="kpiRow"></div>

<div class="sec">CẤU TRÚC THỊ TRƯỜNG THEO MỨC GIÁ</div>
<div class="g2">
<div class="cc"><div class="ct">Thị phần theo phân khúc giá</div>
<div class="cs">Tỷ trọng số lượng sản phẩm niêm yết trong mỗi phân khúc</div>
<div class="leg" id="dLeg"></div>
<div class="cw" style="height:220px"><canvas id="cDonut"></canvas></div></div>
<div class="cc"><div class="ct">Phân bố sản phẩm theo mốc giá chi tiết</div>
<div class="cs">Tỷ lệ % sản phẩm tập trung ở từng khoảng giá</div>
<div class="cw" style="height:240px"><canvas id="cBinPct"></canvas></div></div>
</div>

<div class="sec">TÁC ĐỘNG CỦA GIÁ LÊN DOANH SỐ</div>
<div class="g2">
<div class="cc"><div class="ct">Tương quan Giá — Doanh số (Scatter)</div>
<div class="cs">Mỗi điểm = 1 sản phẩm. Xu hướng giảm rõ rệt khi giá tăng.</div>
<div class="leg" id="sLeg"></div>
<div class="cw" style="height:240px"><canvas id="cScat"></canvas></div></div>
<div class="cc"><div class="ct">Doanh số trung vị theo mốc giá</div>
<div class="cs">Hiệu suất bán hàng thực tế tại từng khung giá — xu hướng giảm dần</div>
<div class="cw" style="height:260px"><canvas id="cBinSales"></canvas></div></div>
</div>

<div class="sec">CHIẾN LƯỢC KHUYẾN MÃI (PROMOTIONAL PRICING)</div>
<div class="g2" style="grid-template-columns:1fr">
<div class="cc"><div class="ct">Tác động của mức giảm giá lên doanh số</div>
<div class="cs">Doanh số trung vị theo nhóm % giảm giá so với giá gốc — Sản phẩm giảm giá có bán chạy hơn không?</div>
<div class="cw" style="height:240px;max-width:750px;margin:0 auto"><canvas id="cDisc"></canvas></div></div>
</div>

<div class="sec">SO SÁNH PHÂN KHÚC</div>
<div class="cc" style="margin-bottom:16px">
<table class="tbl" style="margin-bottom:20px"><thead><tr>
<th>Phân khúc</th><th>Số SP</th><th>Doanh số TB</th><th>Doanh số Trung vị</th><th>Rating TB</th><th>Discount TB</th>
</tr></thead><tbody id="segTb"></tbody></table>
<div class="ct">Top sản phẩm doanh số cao nhất mỗi phân khúc</div>
<table class="tbl" style="margin-top:10px"><thead><tr>
<th>Phân khúc</th><th style="width:40%">Tên sản phẩm</th><th>Giá</th><th>Rating</th><th>Doanh số/tháng</th><th>Discount</th>
</tr></thead><tbody id="topTb"></tbody></table></div>

<div class="sec">INSIGHT & CHIẾN LƯỢC ĐỊNH GIÁ</div>
<div class="ins-grid" id="insGrid"></div>

<div style="height:20px"></div>
<script>
const D=__PAYLOAD__;
Chart.defaults.font.family="'Inter',sans-serif";Chart.defaults.color='#78716C';
const fN=n=>Number(n).toLocaleString('vi-VN');
const fR=(n,d=1)=>Number(n).toFixed(d);
document.getElementById('iTotal').textContent=fN(D.kpi.total);
document.getElementById('iCorr').textContent=D.kpi.spearman;

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

// Bin Pcts
(()=>{const b=D.bar;new Chart(document.getElementById('cBinPct'),{type:'bar',
data:{labels:b.labels,datasets:[{data:b.pcts,backgroundColor:b.colors,borderRadius:3}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.parsed.y}% SP`}}},
scales:{x:{ticks:{font:{size:10},maxRotation:35},grid:{display:false}},y:{ticks:{callback:v=>v+'%'},grid:{color:'rgba(0,0,0,0.04)'}}}}});})();

// Scatter
(()=>{const s=D.scat,segs=['Bình dân','Trung cấp','Cao cấp'];
const ds=segs.map(sg=>({label:sg,data:s.pts.filter(p=>p.s===sg).map(p=>({x:p.x,y:p.y})),backgroundColor:s.colors[sg]+'60',pointRadius:4}));
const l=document.getElementById('sLeg');segs.forEach(sg=>{l.innerHTML+=`<span class="li"><span class="ld" style="background:${s.colors[sg]}"></span>${sg}</span>`;});
new Chart(document.getElementById('cScat'),{type:'scatter',data:{datasets:ds},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` $${c.parsed.x} | ${fN(c.parsed.y)} đơn`}}},
scales:{x:{title:{display:true,text:'Giá ($)',font:{size:11}},grid:{color:'rgba(0,0,0,0.04)'}},
y:{title:{display:true,text:'Doanh số/tháng',font:{size:11}},ticks:{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v},grid:{color:'rgba(0,0,0,0.04)'}}}}});})();

// Bin Sales
(()=>{const b=D.bar;new Chart(document.getElementById('cBinSales'),{type:'bar',
data:{labels:b.labels,datasets:[{data:b.sales_med,backgroundColor:'#F97316',borderRadius:3}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn/tháng`}}},
scales:{x:{ticks:{font:{size:10},maxRotation:35},grid:{display:false}},y:{ticks:{callback:v=>fN(v)},grid:{color:'rgba(0,0,0,0.04)'}}}}});})();

// Discount
(()=>{const d=D.disc;new Chart(document.getElementById('cDisc'),{type:'bar',
data:{labels:d.labels,datasets:[{data:d.med,backgroundColor:'#9A3412',borderRadius:4,barThickness:48}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fN(c.parsed.y)} đơn/tháng`}}},
scales:{x:{grid:{display:false},ticks:{font:{size:11.5}}},y:{grid:{color:'rgba(0,0,0,0.04)'},ticks:{callback:v=>fN(v)}}}}});})();

// Segment table
(()=>{const s=D.seg,bc=['sb0','sb1','sb2'],tb=document.getElementById('segTb');
s.labels.forEach((l,i)=>{tb.innerHTML+=`<tr><td><span class="sb ${bc[i]}">${l}</span></td><td>${fN(s.cnt[i])}</td><td style="font-weight:600">${fN(s.avg_s[i])}</td><td>${fN(s.med_s[i])}</td><td>${s.avg_r[i].toFixed(2)}★</td><td>${s.avg_d[i].toFixed(1)}%</td></tr>`;});})();

// Top products
(()=>{const rows=D.top,bm={'Bình dân':'sb0','Trung cấp':'sb1','Cao cấp':'sb2'},tb=document.getElementById('topTb');
rows.forEach(r=>{tb.innerHTML+=`<tr><td><span class="sb ${bm[r.seg]}">${r.seg}</span></td><td title="${r.title}">${r.title}</td><td style="font-weight:600">$${fR(r.price,2)}</td><td>${r.rating>0?r.rating.toFixed(1)+'★':'—'}</td><td style="font-weight:600;color:var(--pr)">${fN(r.sales)}</td><td>${r.disc>0?r.disc.toFixed(0)+'%':'—'}</td></tr>`;});})();

// Insights
(()=>{const s=D.seg,k=D.kpi,g=document.getElementById('insGrid');
const ins=[
{c:'#3266ad',t:'Bình dân: Chiến lược Thâm nhập',p:`Phân khúc dưới $20 chiếm <span class="val">${k.dom_seg==='Bình dân'?k.dom_pct+'%':((s.cnt[0]/(k.total)*100).toFixed(1))+'%'}</span> thị phần với doanh số trung vị <span class="val">${fN(s.med_s[0])}</span> đơn/tháng — cao nhất trong 3 phân khúc. Khách hàng cực kỳ nhạy cảm về giá. Phù hợp chiến lược chiếm lĩnh thị phần và tối đa hóa volume.`},
{c:'#F97316',t:'Trung cấp: Sweet Spot doanh thu',p:`Phân khúc $20–$70 cân bằng tốt nhất giữa giá bán và lượng bán. Rating trung bình <span class="val">${s.avg_r[1].toFixed(2)}★</span> cho thấy khách hàng hài lòng cao hơn. Khi nhân giá bán với volume, tổng doanh thu phân khúc này thường vượt trội — đây là vùng chiến lược nhất.`},
{c:'#9A3412',t:'Cao cấp: Chiến lược Hớt váng',p:`Phân khúc trên $70 có doanh số trung vị chỉ <span class="val">${fN(s.med_s[2])}</span> đơn/tháng. Thị trường ít co giãn theo giá — giảm giá sâu KHÔNG tăng mạnh volume. Nên duy trì giá ổn định, tập trung biên lợi nhuận và định vị thương hiệu thay vì đua tranh về giá.`}
];
ins.forEach(x=>{g.innerHTML+=`<div class="ins" style="border-left-color:${x.c}"><h4 style="color:${x.c}">${x.t}</h4><p>${x.p}</p></div>`;});})();
</script></body></html>"""

def render(df):
    d=_prep(df)
    if d.empty: st.warning("Không có dữ liệu giá hợp lệ."); return
    p=_payload(d)
    components.html(_HTML.replace("__PAYLOAD__",json.dumps(p,ensure_ascii=False)),height=2200,scrolling=False)