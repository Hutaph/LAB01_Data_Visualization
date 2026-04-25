
    const RAW_DATA = [];
    let GI = {};
    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR = (n) => typeof n === 'number' ? Number(n).toFixed(2) : n;

    function setup() {
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.size = 10;
        
        let cats = new Set();
        RAW_DATA.forEach(d => { if(d['Danh Mục Sản Phẩm'] && d['Danh Mục Sản Phẩm'] !== 'Không Rõ') cats.add(d['Danh Mục Sản Phẩm']); });
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {
            let opt = document.createElement('option'); opt.value = c; opt.innerText = c; sel.appendChild(opt);
        });
        
        initCharts();
        applyFilters();
    }

    function applyFilters() {
        let cat = document.getElementById('selCategory').value;
        let data = RAW_DATA.filter(d => (cat === 'ALL' || d['Danh Mục Sản Phẩm'] === cat));
        updateData(data);
    }

    function updateData(data) {
        let p_cheap=[], p_mid=[], p_high=[];
        if(data.length > 0) {
            let sortedP = [...data].sort((a,b)=>a.current_price - b.current_price);
            let third = Math.floor(sortedP.length/3);
            p_cheap = sortedP.slice(0, third).map(d=>d.current_price);
            p_mid = sortedP.slice(third, third*2).map(d=>d.current_price);
            p_high = sortedP.slice(third*2).map(d=>d.current_price);
        }
        let maxC = p_cheap.length>0 ? p_cheap[p_cheap.length-1] : 0;
        let maxM = p_mid.length>0 ? p_mid[p_mid.length-1] : 0;

        let agg = {};
        let ratioList = ['0%', '1-10%', '10-20%', '20-30%', '30-50%', '>50%'];
        let rAgg = {};
        ratioList.forEach(k => { rAgg[k] = {s:0,c:0}; });

        ['Giá Thấp','Giá Tầm Trung','Giá Cao Cấp'].forEach(k=> {
            agg[k] = { freeS:0, freeC:0, paidS:0, paidC:0 };
        });

        data.forEach(d => {
            let seg = 'Giá Tầm Trung';
            if(d.current_price <= maxC) seg = 'Giá Thấp';
            else if(d.current_price > maxM) seg = 'Giá Cao Cấp';
            
            if(d.delivery_fee === 0) {
                agg[seg].freeS += (d.sales_volume_num||0); agg[seg].freeC++;
            } else {
                agg[seg].paidS += (d.sales_volume_num||0); agg[seg].paidC++;
            }

            if (d.current_price > 0) {
                let ratio = (d.delivery_fee / d.current_price) * 100;
                let rK = '>50%';
                if (ratio === 0) rK = '0%';
                else if (ratio <= 10) rK = '1-10%';
                else if (ratio <= 20) rK = '10-20%';
                else if (ratio <= 30) rK = '20-30%';
                else if (ratio <= 50) rK = '30-50%';
                
                rAgg[rK].s += (d.sales_volume_num || 0);
                rAgg[rK].c++;
            }
        });

        GI.c1_bar.data.labels = ['Giá Thấp','Giá Tầm Trung','Giá Cao Cấp'];
        GI.c1_bar.data.datasets[0].data = [agg['Giá Thấp'].freeC>0?agg['Giá Thấp'].freeS/agg['Giá Thấp'].freeC:0, agg['Giá Tầm Trung'].freeC>0?agg['Giá Tầm Trung'].freeS/agg['Giá Tầm Trung'].freeC:0, agg['Giá Cao Cấp'].freeC>0?agg['Giá Cao Cấp'].freeS/agg['Giá Cao Cấp'].freeC:0];
        GI.c1_bar.data.datasets[1].data = [agg['Giá Thấp'].paidC>0?agg['Giá Thấp'].paidS/agg['Giá Thấp'].paidC:0, agg['Giá Tầm Trung'].paidC>0?agg['Giá Tầm Trung'].paidS/agg['Giá Tầm Trung'].paidC:0, agg['Giá Cao Cấp'].paidC>0?agg['Giá Cao Cấp'].paidS/agg['Giá Cao Cấp'].paidC:0];
        GI.c1_bar.update();

        GI.c1_ratio.data.labels = ratioList;
        GI.c1_ratio.data.datasets[0].data = ratioList.map(k => rAgg[k].c > 0 ? rAgg[k].s / rAgg[k].c : 0);
        GI.c1_ratio.update();

        let sortedS = [...data].sort((a,b)=>(b.sales_volume_num||0) - (a.sales_volume_num||0));
        let top20count = Math.max(1, Math.floor(data.length*0.2));
        let top20 = sortedS.slice(0, top20count);
        let pSales = 0, npSales = 0;
        top20.forEach(d => {
            if(d.is_prime) pSales += (d.sales_volume_num||0);
            else npSales += (d.sales_volume_num||0);
        });
        
        GI.c2_donut.data.datasets[0].data = [pSales, npSales];
        GI.c2_donut.update();

        let pPriceSum = 0, pPriceC = 0;
        let npPriceSum = 0, npPriceC = 0;
        data.forEach(d => {
            if(d.is_prime) { pPriceSum += d.current_price; pPriceC++; }
            else { npPriceSum += d.current_price; npPriceC++; }
        });
        GI.c2_bar.data.datasets[0].data = [pPriceC>0 ? pPriceSum/pPriceC : 0, npPriceC>0 ? npPriceSum/npPriceC : 0];
        GI.c2_bar.update();

        let c_fast=0, c_slow=0, s_fast=0, s_slow=0;
        data.forEach(d=> {
            if(d.est_delivery_days != null && !isNaN(d.est_delivery_days)) {
                if(d.est_delivery_days <= 20) { c_fast++; s_fast += (d.sales_volume_num||0); }
                else { c_slow++; s_slow += (d.sales_volume_num||0); }
            }
        });
        
        GI.c3_combo.data.labels = [`≤ 20 ngày (${fmtN(c_fast)} sp)`, `> 20 ngày (${fmtN(c_slow)} sp)`];
        GI.c3_combo.data.datasets[0].data = [c_fast>0?s_fast/c_fast:0, c_slow>0?s_slow/c_slow:0];
        GI.c3_combo.update();

        let validItems = data.filter(d=>d.est_delivery_days != null && !isNaN(d.est_delivery_days));
        validItems.sort((a,b) => (b.sales_volume_num||0) - (a.sales_volume_num||0));
        let top20 = validItems.slice(0, 20);
        let top20Agg = {};
        top20.forEach(d => {
            let k = d.est_delivery_days + ' ngày';
            top20Agg[k] = (top20Agg[k]||0) + 1;
        });
        
        let t20Labels = Object.keys(top20Agg).sort((a,b)=> parseInt(a)-parseInt(b));
        let t20Data = t20Labels.map(k=>top20Agg[k]);
        
        GI.c3_donut.data.labels = t20Labels;
        GI.c3_donut.data.datasets[0].data = t20Data;
        GI.c3_donut.data.datasets[0].backgroundColor = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        GI.c3_donut.update();

    }

    function initCharts() {
        const legOpts = { position:'bottom', labels:{boxWidth:10, padding:5, font:{size:9}} };
        const baseOpts = { responsive:true, maintainAspectRatio:false, layout:{padding:0}, animation: { duration: 1000 } };

        GI.c1_bar = new Chart(document.getElementById('c1_bar').getContext('2d'), {
            type:'bar', data: { labels:[], datasets:[{label:'Miễn Phí Vận Chuyển', data:[], backgroundColor:'#3b82f6', borderRadius:4},{label:'Có Phí Vận Chuyển', data:[], backgroundColor:'#f97316', borderRadius:4}] }, 
            options: { ...baseOpts, plugins:{legend:legOpts, tooltip:{callbacks:{label: function(c){ return c.dataset.label + ': ' + fmtN(c.raw) + ' Lượt bán mỗi tháng'; }}}}, scales:{y:{grid:{color:'rgba(0,0,0,0.05)'}, ticks:{callback:function(v){return fmtN(v) + ' Lượt';}, font:{size:9}}}, x:{ticks:{font:{size:9}}}} }
        });
        
        GI.c1_ratio = new Chart(document.getElementById('c1_ratio').getContext('2d'), {
            type:'bar', data: { labels:[], datasets:[{label:'Doanh Số Trung Bình', data:[], backgroundColor:'#f97316', borderRadius:4}] }, 
            options: { ...baseOpts, plugins:{legend:{display:false}, tooltip:{callbacks:{label: function(c){ return 'Doanh Số: ' + fmtN(c.raw) + ' Lượt bán'; }}}}, scales:{x: {grid: {display:false}, ticks:{font:{size:9}}}, y:{grid:{color:'rgba(0,0,0,0.05)'}, ticks:{callback:function(v){return fmtN(v) + ' Lượt';}, font:{size:9}}}} }
        });
        
        GI.c2_donut = new Chart(document.getElementById('c2_donut').getContext('2d'), {
            type:'doughnut', data: { labels:['Có Prime','Không Nhãn Prime'], datasets:[{data:[], backgroundColor:['#10b981','#cbd5e1'], borderWidth:0}] },
            options: { ...baseOpts, cutout:'60%', plugins:{legend:legOpts, tooltip:{callbacks:{label: function(c){ return c.label + ': ' + fmtN(c.raw) + ' Lượt Tương Tác/Bán'; }}}}, animation: { duration: 1000, animateScale: true } }
        });

        GI.c2_bar = new Chart(document.getElementById('c2_bar').getContext('2d'), {
            type:'bar', data: { labels:['Được gắn Prime','Chưa Gắn Prime'], datasets:[{label:'Giá Trung Bình', data:[], backgroundColor:['#10b981','#cbd5e1'], borderRadius:4}] },
            options: { ...baseOpts, plugins:{legend:{display:false}, tooltip:{callbacks:{label: function(c){ return 'Trung Bình: $' + fmtR(c.raw); }}}}, scales:{x: {grid: {display:false}, ticks:{font:{size:9}}}, y:{grid:{color:'rgba(0,0,0,0.05)'}, ticks:{callback:function(v){return '$' + fmtN(v);}, font:{size:9}}}} }
        });

        GI.c3_combo = new Chart(document.getElementById('c3_combo').getContext('2d'), {
            type:'bar', data: { labels:[], datasets:[{type:'bar',label:'Doanh Số Trung Bình',data:[],backgroundColor:'#facc15', borderRadius:4}] },
            options: { ...baseOpts, plugins:{legend:legOpts, tooltip:{callbacks:{label: function(c){ return 'Doanh Số: ' + fmtN(c.raw) + ' Lượt Bán Mỗi Tháng'; }}}}, scales:{x:{grid:{display:false}, ticks:{font:{size:9}}}, y:{grid:{color:'rgba(0,0,0,0.05)'},ticks:{callback:function(v){return fmtN(v) + ' Lượt Bán';}, font:{size:9}}} } }
        });

        GI.c3_donut = new Chart(document.getElementById('c3_donut').getContext('2d'), {
            type:'doughnut', data: { labels:[], datasets:[{data:[], backgroundColor:['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'], borderWidth:0}] },
            options: { ...baseOpts, cutout:'60%', plugins:{legend:legOpts, tooltip:{callbacks:{label: function(c){ return c.label + ': ' + fmtN(c.raw) + ' Sản Phẩm'; }}}}, animation: { duration: 1000, animateScale: true } }
        });
    }

    document.addEventListener("DOMContentLoaded", setup);
