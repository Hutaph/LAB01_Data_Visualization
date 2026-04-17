import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import re

def render(df_raw):
    df = df_raw.copy()
    
    # Preprocess shipping-related features
    if "is_prime" not in df.columns:
        df["is_prime"] = False
    else:
        df["is_prime"] = df["is_prime"].fillna(False).astype(bool)

    if "delivery_fee" not in df.columns:
        df["delivery_fee"] = 0.0
    else:
        df["delivery_fee"] = pd.to_numeric(df["delivery_fee"], errors="coerce").fillna(0.0)

    if "sales_volume_num" in df.columns:
        df["sales_volume_num"] = pd.to_numeric(df["sales_volume_num"], errors="coerce").fillna(0)
    else:
        df["sales_volume_num"] = 0

    if "price" in df.columns:
        df["current_price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    else:
        df["current_price"] = 0.0

    if "crawl_category" not in df.columns:
        df["crawl_category"] = "Không rõ"
    
    def group_category(cat):
        c = str(cat).lower()
        if c.startswith("electronics"): return "Hàng Điện Tử"
        if c.startswith("fashion"): return "Thời Trang Và Phụ Kiện"
        if c.startswith("home"): return "Đồ Gia Dụng Và Nội Thất"
        if c.startswith("beauty"): return "Sản Phẩm Làm Đẹp"
        if c.startswith("health"): return "Sức Khỏe Và Y Tế"
        if c.startswith("sports"): return "Thể Thao Và Dã Ngoại"
        if c.startswith("office"): return "Thiết Bị Văn Phòng"
        if c.startswith("baby"): return "Đồ Dùng Trẻ Em"
        if c.startswith("pet"): return "Vật Nuôi Và Thú Cưng"
        if c.startswith("tools"): return "Công Cụ Cải Tạo Nhà Cửa"
        if c.startswith("toys"): return "Đồ Chơi Điện Tử"
        if c.startswith("automotive"): return "Linh Kiện Phương Tiện"
        return "Danh Mục Khác"
        
    df["crawl_category"] = df["crawl_category"].fillna("Không rõ").apply(group_category)

    def parse_delivery_day(info):
        info_str = str(info)
        match = re.search(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b', info_str)
        if match:
            day_map = {'Mon': 'Thứ Hai', 'Tue': 'Thứ Ba', 'Wed': 'Thứ Tư', 'Thu': 'Thứ Năm', 'Fri': 'Thứ Sáu', 'Sat': 'Thứ Bảy', 'Sun': 'Chủ Nhật'}
            return day_map[match.group(1)]
        return "Không có dữ liệu"

    def parse_delivery_month(info):
        info_str = str(info)
        match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', info_str)
        if match:
            month_map = {'Jan':'Tháng 1','Feb':'Tháng 2','Mar':'Tháng 3','Apr':'Tháng 4','May':'Tháng 5','Jun':'Tháng 6','Jul':'Tháng 7','Aug':'Tháng 8','Sep':'Tháng 9','Oct':'Tháng 10','Nov':'Tháng 11','Dec':'Tháng 12'}
            return month_map[match.group(1)]
        return "Không có dữ liệu"
        
    if "delivery_info_clean" in df.columns:
        df["delivery_day"] = df["delivery_info_clean"].fillna("").apply(parse_delivery_day)
        df["delivery_month"] = df["delivery_info_clean"].fillna("").apply(parse_delivery_month)
    else:
        df["delivery_day"] = "Không có dữ liệu"
        df["delivery_month"] = "Không có dữ liệu"

    # Limit numeric types and drop invalid records
    df["current_price"] = df["current_price"].clip(lower=0)
    df["delivery_fee"] = df["delivery_fee"].clip(lower=0)
    
    # Thêm Doanh thu
    df["revenue"] = df["sales_volume_num"] * df["current_price"]

    select_cols = [
        "is_prime", "delivery_fee", "sales_volume_num", "current_price", "revenue", "crawl_category", "delivery_day", "delivery_month"
    ]
    export_df = df[select_cols].copy()

    # Filter out entries with invalid day/month for strictness in analysis if helpful, but keeping all for pie charts
    data_json = export_df.to_dict(orient="records")
    data_json_str = json.dumps(data_json, ensure_ascii=False)

    html_code = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #F97316;
            --secondary: #3B82F6;
            --dark: #9A3412;
            --bg: #FEF3E2;
            --card-bg: #FFFFFF;
            --text-primary: #1C1917;
            --text-secondary: #78716C;
            --border-radius: 8px;
            --font-family: 'Inter', sans-serif;
            --success: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            font-family: var(--font-family);
            color: var(--text-primary);
            padding: 20px;
        }}

        .section-header {{
            font-size: 16px; font-weight: 700; color: var(--dark); text-transform: uppercase;
            padding-bottom: 8px; border-bottom: 2px solid #FED7AA; margin: 32px 0 20px 0;
            display: flex; align-items: center; gap: 8px; letter-spacing: 0.5px;
        }}

        .filter-bar {{
            position: sticky; top: 0; z-index: 1000;
            display: flex; align-items: center; gap: 24px; margin-bottom: 24px;
            background: var(--card-bg); padding: 16px 20px; border-radius: var(--border-radius);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); flex-wrap: wrap; margin-top: 5px;
        }}
        .f-item {{ display: flex; flex-direction: column; gap: 6px; }}
        .f-label {{ font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; }}
        select {{
            padding: 8px 12px; border: 1px solid #D1D5DB; border-radius: 6px; width: 220px;
            font-family: inherit; font-size: 13px; color: var(--text-primary); outline: none; cursor: pointer;
        }}
        select:focus {{ border-color: var(--primary); }}

        .insight-card {{
            background: #FFFAF5; border: 1px solid #FED7AA; border-radius: var(--border-radius);
            padding: 24px; margin-bottom: 8px; display: flex; flex-direction: column; gap: 10px;
        }}
        .insight-title {{ font-size: 15px; font-weight: 700; color: var(--dark); text-transform: uppercase; display: flex; align-items: center; gap: 6px; letter-spacing: 0.5px; }}
        .insight-text {{ font-size: 14px; line-height: 1.6; color: var(--text-primary); font-weight: 400; }}
        .insight-text strong {{ color: var(--dark); font-weight: 600; }}

        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
        .kpi-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 4px solid var(--primary);
            display: flex; flex-direction: column; gap: 4px; position: relative;
        }}
        .kpi-title {{ font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; }}
        .kpi-value {{ font-size: 20px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.5px; }}

        .kpi-card.c-green {{ border-left-color: var(--success); }}
        .kpi-card.c-blue {{ border-left-color: var(--secondary); }}
        .kpi-card.c-red {{ border-left-color: var(--danger); }}

        .chart-row {{ display: flex; gap: 20px; margin-bottom: 24px; align-items: stretch; }}
        .chart-card {{
            background: var(--card-bg); border-radius: var(--border-radius); padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; flex: 1; min-width: 0;
        }}
        .chart-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
        .chart-title {{ font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }}
        .chart-subtitle {{ font-size: 12px; font-weight: 400; color: var(--text-secondary); line-height: 1.4; }}
        .chart-wrapper {{ position: relative; width: 100%; flex-grow: 1; min-height: 280px; display: flex; justify-content: center; align-items: center; }}
        
        .select-light {{ padding: 6px 10px; width: auto; font-weight: 500; border-radius: 6px; box-shadow: none; font-size: 12px; }}
    </style>
</head>
<body>

    <div class="filter-bar">
        <div class="f-item">
            <span class="f-label">Chỉ số Hiệu Suất Cần Tối Ưu</span>
            <select id="selMetric" onchange="applyFilters()">
                <option value="revenue">Tối Ưu Phân Bổ Theo Doanh Thu Bán Hàng ($)</option>
                <option value="sales">Tối Ưu Phân Bổ Theo Số Lượng Hàng Bán</option>
            </select>
        </div>
        <div class="f-item">
            <span class="f-label">Phân Tích Theo Danh Mục Sản Phẩm</span>
            <select id="selCategory" onchange="applyFilters()">
                <option value="ALL">Khảo Sát Toàn Bộ Danh Mục Sản Phẩm Hệ Thống</option>
            </select>
        </div>
    </div>

    <!-- S.M.A.R.T STRATEGY DIGEST -->
    <div class="insight-card" style="margin-top: 10px;">
        <div class="insight-title">📍 MỤC TIÊU CỦA TAB NÀY</div>
        <div class="insight-text" style="margin-bottom: 12px; color: var(--dark);">
            Sử dụng khuôn khổ S.M.A.R.T để đánh giá tính khả thi khi áp dụng <strong>Chính sách giao hàng Prime</strong> và sự ảnh hưởng của <strong>Biến động cước phí</strong> đến sức mua. Từ đó truy xuất chính xác ngưỡng giá cước kháng cự và các phân khúc danh mục tối ưu để bơm tiền trợ giá vận chuyển.
        </div>
        
        <div class="insight-title" style="font-size: 13px; color: #78716C;">CHI TIẾT TRIỂN KHAI S.M.A.R.T</div>
        <div class="insight-text" id="dynamic_insight"></div>
    </div>

    <div class="section-header">1. TỔNG QUAN PHÂN BỔ DỊCH VỤ VẬN CHUYỂN</div>
    
    <div class="kpi-row">
        <div class="kpi-card c-green">
            <div class="kpi-title">Tỷ Lệ Chấp Nhận Dịch Vụ Prime</div>
            <div class="kpi-value" id="kpi_prime_pct">0%</div>
        </div>
        <div class="kpi-card c-red">
            <div class="kpi-title">Chi Phí Vận Chuyển Bình Quân Các Đơn Hàng Tự Giao</div>
            <div class="kpi-value" id="kpi_avg_fee">$0.00</div>
        </div>
        <div class="kpi-card c-blue">
            <div class="kpi-title">Hiệu Suất Bình Quân Trên Một Sản Phẩm Thuộc Prime</div>
            <div class="kpi-value" id="kpi_metric_prime">0</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Hiệu Suất Bình Quân Trên Một Sản Phẩm Tự Giao Hàng</div>
            <div class="kpi-value" id="kpi_metric_non">0</div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Phân Bổ Tỷ Trọng Sản Phẩm Dựa Theo Tính Chất Vận Chuyển</div>
                    <div class="chart-subtitle">So sánh số lượng mã sản phẩm cung cấp thông qua dịch vụ Prime và phương thức tự giao hàng độc lập.</div>
                </div>
            </div>
            <div class="chart-wrapper"><canvas id="cPrimeDist"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Phân Bổ Định Lượng Dòng Tiền Theo Tỷ Trọng Chi Phí Vận Chuyển</div>
                    <div class="chart-subtitle">Xác định tổng thể các mức phí vận chuyển chủ yếu chi phối đến tổng dòng tiền hệ thống.</div>
                </div>
            </div>
            <div class="chart-wrapper"><canvas id="cDonutShip"></canvas></div>
        </div>
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Thống Kê Khối Lượng Doanh Nghiệp Phát Sinh Theo Khoảng Thời Gian Giao Nhận Dự Kiến</div>
                    <div class="chart-subtitle">Phân tích chu kỳ thời điểm người tiêu dùng lập lịch hoàn thành nhận hàng trong tương lai.</div>
                </div>
                <select id="selTimeView" class="select-light" onchange="applyFilters()">
                    <option value="day">Theo Các Ngày Cụ Thể Trong Tuần</option>
                    <option value="month">Theo Các Tháng Trong Năm</option>
                </select>
            </div>
            <div class="chart-wrapper"><canvas id="cDeliveryDays"></canvas></div>
        </div>
    </div>

    <div class="section-header">2. YẾU TỐ ẢNH HƯỞNG: PHÂN TÍCH QUAN HỆ GIỮA CHI PHÍ VẬN CHUYỂN VÀ SỰ THAY ĐỔI CỦA SỨC MUA THỰC THẾ</div>
    <div class="chart-row">
        <div class="chart-card" style="flex: 1.5;">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Đối Chiếu Mức Độ Biến Động Trung Bình Của Hiệu Suất So Với Thang Phí Vận Chuyển Xác Lập</div>
                    <div class="chart-subtitle">Đo lường mức sụt giảm chỉ số doanh nghiệp khi chi phí vận chuyển tăng tiến so với giá trị món hàng hoặc mức giá trị tuyệt đối.</div>
                </div>
                <select id="selLineMode" class="select-light" onchange="applyFilters()">
                    <option value="percent">Định dạng số liệu: Thay Đổi Tỷ Lệ Chi Phí Dự Kiến / Đơn Giá (%)</option>
                    <option value="cash">Định dạng số liệu: Thay Đổi Mức Phí Giao Hàng Tuyệt Đối ($)</option>
                </select>
            </div>
            <div class="chart-wrapper" style="min-height: 340px;"><canvas id="cFeeRatioRatio"></canvas></div>
        </div>
        <div class="chart-card" style="flex: 1;">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Chỉ Số Hiệu Suất Phân Bổ Qua Các Phân Khúc Đơn Giá Chấp Nhận Chi Trả</div>
                    <div class="chart-subtitle">So sánh mức tác động của phương thức tự giao hàng (Tốn Phí) và Prime (Miễn Phí) ở nhóm sản phẩm phân khúc đơn giá khác nhau.</div>
                </div>
            </div>
            <div class="chart-wrapper"><canvas id="cPriceSegment"></canvas></div>
        </div>
    </div>

    <div class="section-header">3. MỞ RỘNG HIỆU SUẤT TRÊN PHẠM VI TOÀN CỤC DANH MỤC</div>
    <div class="chart-row" style="flex-direction: column;">
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Đánh Giá Tính Cấp Thiết Khi Áp Dụng Dịch Vụ Prime Cục Bộ Phân Loại Qua Các Nhóm Ngành Hàng Tổng Quát</div>
                    <div class="chart-subtitle">Đo lường sức ảnh hưởng vận chuyển để tiến hành xây dựng chính sách hỗ trợ chi phí cho riêng từng danh mục sản phẩm cụ thể.</div>
                </div>
            </div>
            <div class="chart-wrapper" style="min-height: 500px;"><canvas id="cCategoryBreakdown"></canvas></div>
        </div>
    </div>

<script>
    const RAW_DATA = {data_json_str};
    let globalInstances = {{}};

    // Mẫu màu quy định nghiêm ngặt cho báo cáo
    const BRAND = {{
        prime: '#F97316',
        nonPrime: '#9CA3AF',
        piePrime: '#F97316',
        pieNon: '#E5E7EB',
        palette: ['#10B981', '#3B82F6', '#F59E0B', '#F97316', '#EF4444']
    }};

    const fmtN = (n) => new Intl.NumberFormat('en-US').format(Math.round(n));
    const fmtR = (n) => Number(n).toFixed(2);
    const fmtC = (n) => "$" + new Intl.NumberFormat('en-US').format(Math.round(n));

    function setup() {{
        let cats = new Set();
        RAW_DATA.forEach(d => {{
            if (d.crawl_category && d.crawl_category !== 'Không rõ') cats.add(d.crawl_category);
        }});
        
        let sel = document.getElementById('selCategory');
        Array.from(cats).sort().forEach(c => {{
            let opt = document.createElement('option');
            opt.value = c; opt.innerText = c;
            sel.appendChild(opt);
        }});
        
        initCharts();
        applyFilters();
    }}

    function applyFilters() {{
        let cat = document.getElementById('selCategory').value;
        let metric = document.getElementById('selMetric').value;

        let lbls = document.getElementsByClassName("lbl_metric");
        let metricStr = (metric === 'revenue') ? 'Doanh Thu' : 'Số Lượng Hàng Bán Ra';
        for(let l of lbls) l.innerText = metricStr;

        let filtered = RAW_DATA.filter(d => {{
            if (cat !== 'ALL' && d.crawl_category !== cat) return false;
            return true;
        }});

        updateKPIsandInsight(filtered, metric);
        updateCharts(filtered, metric);
    }}

    function updateKPIsandInsight(data, metric) {{
        let tProd = data.length;
        if (tProd === 0) return;

        let primeProds = data.filter(d => d.is_prime);
        let nonPrimeProds = data.filter(d => !d.is_prime);

        let primePct = (primeProds.length / tProd) * 100;
        document.getElementById('kpi_prime_pct').innerText = fmtR(primePct) + '%';

        let feeProds = data.filter(d => d.delivery_fee > 0 && !d.is_prime);
        let avgFee = feeProds.length > 0 ? feeProds.reduce((a,b)=>a+b.delivery_fee, 0)/feeProds.length : 0;
        document.getElementById('kpi_avg_fee').innerText = '$' + fmtR(avgFee);

        let valProp = (metric === 'revenue') ? 'revenue' : 'sales_volume_num';
        let prefix = (metric === 'revenue') ? "$" : "";

        let pValAvg = primeProds.length > 0 ? primeProds.reduce((a,b)=>a+(b[valProp]||0), 0)/primeProds.length : 0;
        let nValAvg = nonPrimeProds.length > 0 ? nonPrimeProds.reduce((a,b)=>a+(b[valProp]||0), 0)/nonPrimeProds.length : 0;
        
        document.getElementById('kpi_metric_prime').innerText = prefix + fmtN(pValAvg);
        document.getElementById('kpi_metric_non').innerText = prefix + fmtN(nValAvg);

        let mName = (metric === 'revenue') ? 'doanh thu' : 'số lượng bán hàng';
        
        let S = "<strong>Mục tiêu Cụ thể (Specific):</strong> Yêu cầu nghiên cứu định lượng mức độ sụt giảm " + mName + " bình quân thông qua biến số chi phí vận chuyển. Thiết lập cơ sở đưa ra kế hoạch tái cấu trúc giá cước vận chuyển riêng rẽ cho từng hạng mục phân khúc giá bán và từng danh mục ngành hàng cụ thể.<br/>";
        let M = "<strong>Đo lường (Measurable):</strong> Xác nhận các ngưỡng định lượng đánh dấu suy giảm hiệu suất phân phối đáng kể. Hệ thống theo dõi đặc tính chênh lệch khi chi phí cước dịch vụ vượt tỷ lệ 30% mức giá niêm yết của mặt hàng hoặc tỷ giá chi phí tuyệt đối vượt mức 50 Đô La.<br/>";
        let A = "<strong>Tính khả thi (Achievable):</strong> Quyết định phân luồng chính sách cước dựa vào tính chất sản phẩm. Cụ thể: Ứng dụng nguồn tài chính xúc tiến ưu đãi miễn phí giao hàng cho mặt hàng thiết yếu, bình dân và ấn định cấu trúc tính phí cố định đối với mặt hàng cao cấp thuộc nhóm khách hàng đặc quyền (Vượt kiểm định hiệu suất với " + prefix + fmtN(nValAvg) + " thu giá trị cao dù không nằm trong hệ thống ưu đãi).<br/>";
        let R = "<strong>Tính thực tiễn bài toán (Relevant):</strong> Đánh thẳng vào nhân tố Logistics. Đây là điểm cắt giảm hiệu lực chính trong khâu chốt giao dịch Thương mại Điện tử. Xác suất ước tính khi tinh giảm chính sách này đủ để củng cố biên độ phát triển danh thu vượt lên biên độ kỳ vọng 15%.<br/>";
        let T = "<strong>Khung thời gian áp dụng (Time-bound):</strong> Tổng hợp dữ liệu tập trung khung thời gian giao hàng nhằm chuẩn hóa các mốc biểu đồ lập lịch phân phối. Phương pháp này chỉ rõ ưu tiên ngân sách truyền thông tập trung vào các đoạn quy mô tháng/ngày thực nhận lớn nhất theo chuẩn quý báo cáo tiếp theo.<br/>";

        document.getElementById('dynamic_insight').innerHTML = S + M + A + R + T;
    }}

    function updateCharts(data, metric) {{
        let valProp = (metric === 'revenue') ? 'revenue' : 'sales_volume_num';
        
        // 0. Prime Pie
        let primeProds = data.filter(d => d.is_prime);
        let nonPrimeProds = data.filter(d => !d.is_prime);
        globalInstances.cPrimeDist.data.datasets[0].data = [primeProds.length, nonPrimeProds.length];
        let totalCount = primeProds.length + nonPrimeProds.length;
        globalInstances.cPrimeDist.options.plugins.tooltip.callbacks.label = function(ctx) {{
            let percent = totalCount > 0 ? ((ctx.raw / totalCount)*100).toFixed(1) : 0;
            return " " + fmtN(ctx.raw) + " Danh Mục (" + percent + "%)";
        }};
        globalInstances.cPrimeDist.update();

        // 1. Fee Distribution Pie
        let tPrimeVal=0, tLowVal=0, tMidVal=0, tHighVal=0;
        data.forEach(d => {{
            let v = d[valProp] || 0;
            if (d.is_prime || d.delivery_fee === 0) {{ tPrimeVal += v; }} 
            else if (d.delivery_fee <= 12) {{ tLowVal += v; }} 
            else if (d.delivery_fee <= 25) {{ tMidVal += v; }} 
            else {{ tHighVal += v; }}
        }});
        let sumPie = tPrimeVal + tLowVal + tMidVal + tHighVal;
        globalInstances.cDonutShip.data.datasets[0].data = [tPrimeVal, tLowVal, tMidVal, tHighVal];
        globalInstances.cDonutShip.options.plugins.tooltip.callbacks.label = function(ctx) {{
            let percent = sumPie > 0 ? ((ctx.raw / sumPie)*100).toFixed(1) : 0;
            return " " + (metric === 'revenue' ? "$" : "") + fmtN(ctx.raw) + " (" + percent + "%)";
        }};
        globalInstances.cDonutShip.update();

        // 2. Days / Time-Bound
        let timeView = document.getElementById('selTimeView').value;
        let timeLabels = [];
        let timeProp = "";
        
        if (timeView === 'day') {{
            timeLabels = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
            timeProp = "delivery_day";
        }} else {{
            timeLabels = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"];
            timeProp = "delivery_month";
        }}

        let timeStats = {{}};
        timeLabels.forEach(t => timeStats[t] = {{ sumP:0, cntP:0, sumN:0, cntN:0 }});
        
        data.forEach(d => {{
            let t = d[timeProp];
            if (timeStats[t]) {{
                let v = d[valProp] || 0;
                if (d.is_prime) {{ timeStats[t].sumP += v; timeStats[t].cntP++; }}
                else {{ timeStats[t].sumN += v; timeStats[t].cntN++; }}
            }}
        }});
        
        globalInstances.cDeliveryDays.data.labels = timeLabels;
        globalInstances.cDeliveryDays.data.datasets[0].data = timeLabels.map(t => timeStats[t].cntP>0 ? timeStats[t].sumP/timeStats[t].cntP : 0);
        globalInstances.cDeliveryDays.data.datasets[1].data = timeLabels.map(t => timeStats[t].cntN>0 ? timeStats[t].sumN/timeStats[t].cntN : 0);
        globalInstances.cDeliveryDays.update();

        // 3. Line Chart - Fee Ratio Breakdown
        let lineMode = document.getElementById('selLineMode').value;
        let bins = [];
        if (lineMode === 'percent') {{
            bins = [
                {{ label: "0%", min: 0, max: 0, sumV: 0, count: 0 }},
                {{ label: "Dưới 15%", min: 0.001, max: 0.15, sumV: 0, count: 0 }},
                {{ label: "Từ 15% đến 30%", min: 0.1501, max: 0.30, sumV: 0, count: 0 }},
                {{ label: "Từ 30% đến 60%", min: 0.3001, max: 0.60, sumV: 0, count: 0 }},
                {{ label: "Trên 60%", min: 0.6001, max: 9999, sumV: 0, count: 0 }}
            ];
            data.forEach(d => {{
                let fee = d.is_prime ? 0 : (d.delivery_fee || 0);
                let price = d.current_price || 0;
                let ratio = (price > 0) ? (fee / price) : ((fee>0)?999:0);
                for(let b of bins) {{
                    if (ratio >= b.min && ratio <= b.max) {{ b.sumV += (d[valProp] || 0); b.count++; break; }}
                }}
            }});
        }} else {{
            bins = [
                {{ label: "Miễn Phí ($0)", min: 0, max: 0, sumV: 0, count: 0 }},
                {{ label: "Dưới Khoảng $12", min: 0.001, max: 12, sumV: 0, count: 0 }},
                {{ label: "Mức Từ $12 Đến $25", min: 12.001, max: 25, sumV: 0, count: 0 }},
                {{ label: "Mức Từ $25 Đến $50", min: 25.001, max: 50, sumV: 0, count: 0 }},
                {{ label: "Cao Lớn Hơn $50", min: 50.001, max: 9999, sumV: 0, count: 0 }}
            ];
            data.forEach(d => {{
                let fee = d.is_prime ? 0 : (d.delivery_fee || 0);
                for(let b of bins) {{
                    if (fee >= b.min && fee <= b.max) {{ b.sumV += (d[valProp] || 0); b.count++; break; }}
                }}
            }});
        }}
        globalInstances.cFeeRatioRatio.data.labels = bins.map(b => b.label);
        globalInstances.cFeeRatioRatio.data.datasets[0].data = bins.map(b => b.count > 0 ? (b.sumV / b.count) : 0);
        globalInstances.cFeeRatioRatio.update();

        // 4. Price Bracket Bar Chart
        let segs = [
            {{ name: "Mức Giá Thấp Dưới $25", sumP:0, cntP:0, sumN:0, cntN:0 }},
            {{ name: "Mức Giá Chuẩn Từ $25 Đến $50", sumP:0, cntP:0, sumN:0, cntN:0 }},
            {{ name: "Mức Giá Từ Tệp Cao $50 Đến $100", sumP:0, cntP:0, sumN:0, cntN:0 }},
            {{ name: "Tệp Rất Cao Lớn Hơn $100", sumP:0, cntP:0, sumN:0, cntN:0 }}
        ];

        data.forEach(d => {{
            let v = d[valProp] || 0;
            let p = d.current_price || 0;
            let tg = null;
            if (p < 25) tg = segs[0];
            else if (p < 50) tg = segs[1];
            else if (p <= 100) tg = segs[2];
            else tg = segs[3];

            if (d.is_prime) {{ tg.sumP += v; tg.cntP++; }}
            else {{ tg.sumN += v; tg.cntN++; }}
        }});

        globalInstances.cPriceSegment.data.labels = segs.map(s => s.name);
        globalInstances.cPriceSegment.data.datasets[0].data = segs.map(s => s.cntP > 0 ? (s.sumP/s.cntP) : 0);
        globalInstances.cPriceSegment.data.datasets[1].data = segs.map(s => s.cntN > 0 ? (s.sumN/s.cntN) : 0);
        globalInstances.cPriceSegment.update();

        // 5. Category Breakdown (Horizontal Bar)
        let catStats = {{}};
        data.forEach(d => {{
            let cat = d.crawl_category || 'Danh Mục Khác';
            if (cat === 'Không rõ' || cat === 'N/A') return;
            if (!catStats[cat]) catStats[cat] = {{ sumP:0, cntP:0, sumN:0, cntN:0 }};
            let v = d[valProp] || 0;
            if (d.is_prime) {{ catStats[cat].sumP += v; catStats[cat].cntP++; }}
            else {{ catStats[cat].sumN += v; catStats[cat].cntN++; }}
        }});

        let catLabels = Object.keys(catStats).sort();
        globalInstances.cCategoryBreakdown.data.labels = catLabels;
        globalInstances.cCategoryBreakdown.data.datasets[0].data = catLabels.map(c => catStats[c].cntP > 0 ? (catStats[c].sumP/catStats[c].cntP) : 0);
        globalInstances.cCategoryBreakdown.data.datasets[1].data = catLabels.map(c => catStats[c].cntN > 0 ? (catStats[c].sumN/catStats[c].cntN) : 0);
        globalInstances.cCategoryBreakdown.update();
    }}

    function initCharts() {{
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#78716C';
        Chart.defaults.font.size = 12;

        let tooltipFormatter = function(ctx) {{
            let met = document.getElementById('selMetric').value;
            return (met === 'revenue' ? "$" : "") + fmtN(ctx.raw);
        }};
        let axisFormatter = function(val) {{
            let met = document.getElementById('selMetric').value;
            if(met==='revenue') {{
                if(val >= 1000) return "$" + (val/1000).toFixed(1) + "K";
                return "$" + val;
            }} else {{
                if(val >= 1000) return (val/1000).toFixed(1) + "K";
                return val;
            }}
        }};

        // Chart 0: cPrimeDist
        let ctxDist = document.getElementById('cPrimeDist').getContext('2d');
        globalInstances.cPrimeDist = new Chart(ctxDist, {{
            type: 'doughnut',
            data: {{
                labels: ['Cung Cấp Qua Phương Thức Sử Dụng Dịch Vụ Mở Rộng Của Tính Năng Prime FBA', 'Phát Hành Bằng Phương Thức Người Bán Chủ Trị Hệ Thống Tự Giao Nhận Trực Tiếp'],
                datasets: [{{ data: [0, 0], backgroundColor: [BRAND.piePrime, BRAND.pieNon], borderWidth: 1 }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }} // To prevent extremely long horizontal labels from clashing the UI
        }});

        // Chart 1: cDonutShip
        let ctxDonut = document.getElementById('cDonutShip').getContext('2d');
        globalInstances.cDonutShip = new Chart(ctxDonut, {{
            type: 'pie',
            data: {{
                labels: ['Sản Phẩm Áp Dụng Biên Độ Giao Hàng Miễn Cước', 'Sản Phẩm Tự Quy Định Thu Cước Thấp Tại Dưới Ngưỡng Mức Cục Bộ Giới Hạn $12', 'Sản Phẩm Tính Cước Giữa Ngưỡng Ranh Giới Trung Mức Độ Trung Định Mức Thu Cước Nằm Trong Dải Giao Hàng Xấp Xỉ Giá $25', 'Hạng Mục Quản Trị Hệ Số Vận Chuyển Tính Cước Phí Phụ Thêm Đặc Biệt Tại Mức Mở Lớn Hơn Không Gian Hoạch Định Hoặc Cồng Kềnh Mức $50 Trở Về Sau'],
                datasets: [{{ data: [0, 0, 0, 0], backgroundColor: BRAND.palette, borderWidth: 1 }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
        }});

        // Chart 2: cDeliveryDays
        let ctxDays = document.getElementById('cDeliveryDays').getContext('2d');
        globalInstances.cDeliveryDays = new Chart(ctxDays, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: 'Sản Phẩm Áp Dụng Dịch Vụ Prime', data: [], backgroundColor: BRAND.prime, borderRadius: 3, barPercentage: 0.8 }},
                    {{ label: 'Sản Phẩm Chọn Dịch Vụ Phân Phối Tự Giao Hàng', data: [], backgroundColor: BRAND.nonPrime, borderRadius: 3, barPercentage: 0.8 }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle' }} }}, tooltip: {{ callbacks: {{ label: tooltipFormatter }} }} }},
                scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ borderDash: [4, 4] }}, ticks: {{ callback: axisFormatter }} }} }}
            }}
        }});
        
        // Chart 3: cFeeRatioRatio
        let ctxRatio = document.getElementById('cFeeRatioRatio').getContext('2d');
        globalInstances.cFeeRatioRatio = new Chart(ctxRatio, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'Giá Trị Biến Động Trung Bình Được Định Lượng Doanh Nghiệp',
                    data: [],
                    backgroundColor: 'rgba(249, 115, 22, 0.85)',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: tooltipFormatter }} }} }},
                scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ borderDash: [4, 4] }}, ticks: {{ callback: axisFormatter }} }} }}
            }}
        }});

        // Chart 4: cPriceSegment
        let ctxPrice = document.getElementById('cPriceSegment').getContext('2d');
        globalInstances.cPriceSegment = new Chart(ctxPrice, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: 'Có Ứng Dụng Tích Hợp Hệ Thống Thực Thi Prime FBA', data: [], backgroundColor: BRAND.prime, borderRadius: 4, barPercentage: 0.7 }},
                    {{ label: 'Tiến Hành Triển Khai Xử Lý Khâu Thực Thi Nội Bộ Đơn Vị Phát Hành', data: [], backgroundColor: BRAND.nonPrime, borderRadius: 4, barPercentage: 0.7 }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle' }} }}, tooltip: {{ callbacks: {{ label: tooltipFormatter }} }} }},
                scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ borderDash: [4, 4] }}, ticks: {{ callback: axisFormatter }} }} }}
            }}
        }});

        // Chart 5: cCategoryBreakdown
        let ctxCat = document.getElementById('cCategoryBreakdown').getContext('2d');
        globalInstances.cCategoryBreakdown = new Chart(ctxCat, {{
            type: 'bar',
            data: {{
                labels: [],
                datasets: [
                    {{ label: 'Tiểu Chuẩn Phạm Vi Quét Quản Lý Danh Mục Áp Dụng Prime', data: [], backgroundColor: BRAND.prime, borderRadius: 4, barPercentage: 0.8 }},
                    {{ label: 'Thống Kê Số Liệu Khảo Sát Từng Đoạn Cắt Mặt Cắt Danh Mục Tự Quản Trị Hệ Logistic', data: [], backgroundColor: BRAND.nonPrime, borderRadius: 4, barPercentage: 0.8 }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'top', labels: {{ usePointStyle: true, pointStyle: 'circle' }} }}, tooltip: {{ callbacks: {{ label: tooltipFormatter }} }} }},
                scales: {{ x: {{ grid: {{ borderDash: [4, 4] }}, ticks: {{ callback: axisFormatter }} }}, y: {{ grid: {{ display: false }} }} }}
            }}
        }});
    }}

    document.addEventListener("DOMContentLoaded", setup);
</script>
</body>
</html>
    """
    
    components.html(html_code, height=2300, scrolling=False)
