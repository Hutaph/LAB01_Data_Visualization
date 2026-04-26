"""
scripts/export_member02_charts.py
=================================
Tạo và lưu toàn bộ biểu đồ minh chứng cho phần 4.3.2 – Phân tích của Thành viên 2.

Output: reports/images/
    ├── m02_fig1_histogram.png         (Phân phối mức giảm giá)
    ├── m02_fig2_line_sales.png        (Hiệu quả doanh số theo bin giảm giá)
    ├── m02_fig3_doughnut.png          (Phân khúc ưu đãi thị trường)
    ├── m02_fig4_comparison_top5.png   (Đối chiếu Top 5 Giảm giá vs Top 5 Doanh số)
    ├── m02_fig5_correlation.png       (Tương quan Giảm giá & Doanh số theo ngành - CHÍNH)
    └── m02_fig6_prime_vs_all.png      (So sánh Prime vs Toàn sàn)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from scipy.interpolate import make_interp_spline

# ── Config ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR   = PROJECT_ROOT / "reports" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT / "app"))
from utils.category_mapping import add_display_column

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
})

C_PRIMARY = "#F97316"
C_DARK    = "#EA580C"
C_DARK2   = "#9A3412"
C_MUTED   = "#FED7AA"
C_GRAY    = "#78716C"
C_BG      = "#FEF3E2"

BINS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101]
BIN_LABELS = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '>90%']

# ── Load Data ───────────────────────────────────────────────────────────────
def load_data():
    """Tìm file CSV mới nhất trong data/processed, ưu tiên file visualization."""
    # Danh sách từ khóa loại trừ để tránh đọc nhầm file modeling/train/test
    exclude = ["modeling", "train", "test", "val", "pipeline"]
    
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Thư mục dữ liệu không tồn tại: {DATA_DIR}")

    csv_files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not csv_files:
        raise FileNotFoundError(f"Không tìm thấy file CSV nào trong {DATA_DIR}")

    # 1. Ưu tiên tuyệt đối file 'viz' và không chứa từ khóa nhạy cảm
    chosen_path = None
    for p in csv_files:
        stem_lower = p.stem.lower()
        if "amazon_products_viz" in stem_lower and not any(kw in stem_lower for kw in exclude):
            chosen_path = p
            break

    # 2. Fallback: File bất kỳ không chứa từ khóa nhạy cảm
    if not chosen_path:
        for p in csv_files:
            stem_lower = p.stem.lower()
            if not any(kw in stem_lower for kw in exclude):
                chosen_path = p
                break

    # 3. Last resort
    if not chosen_path: chosen_path = csv_files[0]
    
    df = pd.read_csv(chosen_path)
    print(f"[INFO] Loaded: {chosen_path.name} ({len(df):,} rows)")

    def _num(col, default=0.0):
        if col in df.columns: return pd.to_numeric(df[col], errors="coerce").fillna(default)
        return pd.Series(default, index=df.index)

    df["price"] = _num("price")
    df["original_price"] = _num("original_price") if "original_price" in df.columns else df["price"]
    df["discount_rate"] = np.where(df["original_price"] > 0, 
                                   (df["original_price"] - df["price"]) / df["original_price"] * 100, 0.0).clip(0, 100)
    df["sales_volume_num"] = _num("sales_volume_num")
    df["is_prime"] = df["is_prime"].fillna(False).astype(bool) if "is_prime" in df.columns else False
    
    cat_col = "crawl_category" if "crawl_category" in df.columns else "category"
    df[cat_col] = df[cat_col].fillna("Không rõ")
    df = add_display_column(df, source_col=cat_col, target_col="display_category")
    return df

def fmt_k(val):
    if val >= 1e6: return f"{val/1e6:.1f}M"
    if val >= 1e3: return f"{val/1e3:.1f}K"
    return str(int(val))

# ── Charts ──────────────────────────────────────────────────────────────────

def export_fig1_2_3(df):
    # 1. Histogram & Line Data
    counts, sales = [], []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        sub = df[(df["discount_rate"] >= lo) & (df["discount_rate"] < hi)]
        counts.append(len(sub))
        with_s = sub[sub["sales_volume_num"] > 0]["sales_volume_num"]
        # Use Median for more robust analysis of typical performance
        sales.append(with_s.median() if len(with_s) > 0 else 0)

    # Figure 1: Histogram (Phân phối Mức giảm giá)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(BIN_LABELS, counts, color=C_PRIMARY, width=0.7, zorder=3)
    ax.set_title("Phân phối Mức giảm giá (%)", fontweight="bold", pad=15)
    ax.set_ylabel("Số lượng sản phẩm")
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "m02_fig1_histogram.png")
    
    # Figure 2: Line (Hiệu quả Doanh số) - SMOOTHED
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    # Interpolation for smoothing
    x_numeric = np.arange(len(BIN_LABELS))
    x_smooth = np.linspace(x_numeric.min(), x_numeric.max(), 300)
    spl = make_interp_spline(x_numeric, sales, k=3)
    sales_smooth = spl(x_smooth)
    # Clip to zero (prevent negative dips if any)
    sales_smooth = np.clip(sales_smooth, 0, None)

    ax.plot(x_smooth, sales_smooth, color=C_DARK2, linewidth=3, zorder=3)
    ax.scatter(x_numeric, sales, color=C_DARK2, s=50, zorder=4, edgecolors='white', linewidth=1.5)
    ax.fill_between(x_smooth, sales_smooth, alpha=0.1, color=C_DARK2)
    
    ax.set_xticks(x_numeric)
    ax.set_xticklabels(BIN_LABELS)
    ax.set_title("Hiệu quả Doanh số theo Mức giảm (Trung vị)", fontweight="bold", pad=15)
    ax.set_ylabel("Doanh số trung vị (lượt)")
    ax.grid(True, linestyle='--', alpha=0.3, zorder=0)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "m02_fig2_line_sales.png")

    # Figure 3: Doughnut (Phân khúc Ưu đãi)
    segments = [len(df[df["discount_rate"]<=0]), 
                len(df[(df["discount_rate"]>0)&(df["discount_rate"]<=20)]),
                len(df[(df["discount_rate"]>20)&(df["discount_rate"]<=50)]),
                len(df[df["discount_rate"]>50])]
    
    fig, ax = plt.subplots(figsize=(6, 6))
    labels = ["Gốc", "<20%", "20-50%", ">50%"]
    colors = [C_GRAY, C_MUTED, C_PRIMARY, C_DARK2]
    
    patches, texts = ax.pie(segments, colors=colors, wedgeprops={'width':0.4, 'edgecolor':'w'}, startangle=90)
    
    ax.legend(patches, labels, loc="lower center", bbox_to_anchor=(0.5, -0.05), ncol=4, frameon=False, fontsize=9)
    ax.set_title("Phân khúc Ưu đãi thị trường", fontweight="bold", pad=15)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "m02_fig3_doughnut.png")

def export_fig4_comparison(df):
    agg = df.groupby("display_category").agg(
        avg_d=("discount_rate","mean"), 
        total_s=("sales_volume_num","sum")
    ).reset_index()
    
    top5_d = agg.nlargest(5, "avg_d").sort_values("avg_d")
    top5_s = agg.nlargest(5, "total_s").sort_values("total_s")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Left: Top 5 Discount
    ax1.barh(top5_d["display_category"], top5_d["avg_d"], color=C_PRIMARY, zorder=3)
    ax1.set_title("Top 5 Ngành hàng Giảm giá sâu nhất (%)", fontweight="bold", pad=15)
    ax1.set_xlabel("Mức giảm trung bình (%)")
    ax1.grid(axis='x', linestyle='--', alpha=0.3, zorder=0)

    # Right: Top 5 Sales
    ax2.barh(top5_s["display_category"], top5_s["total_s"], color=C_DARK2, zorder=3)
    ax2.set_title("Top 5 Ngành hàng Doanh số cao nhất", fontweight="bold", pad=15)
    ax2.set_xlabel("Tổng doanh số (lượt bán)")
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: fmt_k(x)))
    ax2.grid(axis='x', linestyle='--', alpha=0.3, zorder=0)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "m02_fig4_comparison_top5.png")
    print(f"[SAVED] m02_fig4_comparison_top5.png - Dashboard-style combined chart")

def export_fig5_correlation(df):
    """
    Biểu đồ then chốt: Tương quan giữa Giảm giá và Doanh số theo ngành.
    Chứng minh Chăm sóc da (ít giảm, nhiều bán) vs Thời trang (nhiều giảm, ít bán).
    """
    agg = df.groupby("display_category").agg(
        avg_d=("discount_rate", "mean"),
        total_s=("sales_volume_num", "sum"),
        count=("asin", "count")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    scatter = ax.scatter(agg["avg_d"], agg["total_s"], s=agg["count"]*0.5, alpha=0.6, c=agg["avg_d"], cmap="Oranges", edgecolors="gray")
    
    # Highlight key industries mentioned in text
    targets = ["Chăm sóc Da", "Thời trang Nữ", "Thời trang Nam", "Thực phẩm Chức năng"]
    for i, row in agg.iterrows():
        if row["display_category"] in targets:
            ax.annotate(row["display_category"], (row["avg_d"], row["total_s"]), 
                        xytext=(10, 5), textcoords='offset points', fontweight='bold', fontsize=10)
            ax.scatter(row["avg_d"], row["total_s"], s=row["count"]*0.8, edgecolors='black', facecolors='none', linewidth=1.5)

    ax.set_title("Tương quan Giảm giá trung bình vs Tổng doanh số theo Ngành hàng", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Mức giảm giá trung bình (%)", fontsize=11)
    ax.set_ylabel("Tổng doanh số (lượt bán)", fontsize=11)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.0f}%"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: fmt_k(x)))
    ax.grid(True, linestyle="--", alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "m02_fig5_correlation.png")
    print(f"[SAVED] m02_fig5_correlation.png - Biểu đồ tương quan chính")

def export_fig6_prime(df):
    # So sánh Prime vs Non-Prime
    prime = df[df["is_prime"]]
    non_prime = df[~df["is_prime"]]
    
    labels = ['Giảm giá TB (%)', 'Tỷ lệ KM (%)', 'Giá bán TB ($)']
    p_vals = [prime["discount_rate"].mean(), (len(prime[prime["discount_rate"]>0])/len(prime)*100), prime["price"].mean()]
    a_vals = [df["discount_rate"].mean(), (len(df[df["discount_rate"]>0])/len(df)*100), df["price"].mean()]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width/2, p_vals, width, label='Prime', color=C_PRIMARY)
    ax.bar(x + width/2, a_vals, width, label='Toàn sàn', color=C_GRAY)
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_title("So sánh Chỉ số: Prime vs Toàn sàn", fontweight="bold")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "m02_fig6_prime_vs_all.png")

if __name__ == "__main__":
    try:
        df = load_data()
        export_fig1_2_3(df)
        export_fig4_comparison(df)
        export_fig5_correlation(df)
        export_fig6_prime(df)
        print(f"\n✅ Tất cả biểu đồ đã được lưu tại: {OUTPUT_DIR}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
