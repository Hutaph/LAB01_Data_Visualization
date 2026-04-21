from pathlib import Path
import re

import pandas as pd
import streamlit as st

COLOR_SEQUENCE = ["#FF9900", "#FFC266", "#E47911", "#FFD9A3", "#CC7A00"]

def _to_bool(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.lower()
    return text.isin(["true", "1", "yes", "y"])

def _parse_sales_volume(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    parsed = text.str.extract(r"(\d+(?:\.\d+)?)\s*([kK]?)\+")
    num = pd.to_numeric(parsed[0], errors="coerce")
    is_k = parsed[1].fillna("").str.lower().eq("k")
    return (num * is_k.map({True: 1000, False: 1})).round().astype("Int64")

def _parse_delivery_fee(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    fee = text.str.extract(r"\$(\d+(?:\.\d+)?)\s*delivery", expand=False)
    return pd.to_numeric(fee, errors="coerce")

def _resolve_latest_csv() -> Path:
    app_dir = Path(__file__).resolve().parents[1]
    root_dir = app_dir.parent
    candidates = [
        root_dir / "data" / "Processed",
        root_dir / "data" / "processed",
        app_dir / "data",
    ]

    csv_files: list[Path] = []
    for folder in candidates:
        if folder.exists():
            csv_files.extend(sorted(folder.glob("*.csv")))

    if not csv_files:
        raise FileNotFoundError(
            "Không tìm thấy file CSV trong data/Processed hoặc data/processed."
        )

    preferred = [p for p in csv_files if p.stem.lower() == "amazon_products_viz_drop"]
    if preferred:
        return preferred[-1]

    return max(csv_files, key=lambda p: p.stat().st_mtime)

@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, dict]:
    csv_path = _resolve_latest_csv()
    df = pd.read_csv(csv_path, low_memory=False)

    for col in [
        "price",
        "original_price",
        "rating",
        "reviews",
        "sales_volume_num",
        "delivery_fee",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "sales_volume_num" not in df.columns and "sales_volume" in df.columns:
        df["sales_volume_num"] = _parse_sales_volume(df["sales_volume"])
    elif "sales_volume_num" in df.columns:
        df["sales_volume_num"] = df["sales_volume_num"].astype("Int64")
    else:
        df["sales_volume_num"] = pd.Series(pd.NA, index=df.index, dtype="Int64")

    if "delivery_fee" not in df.columns and "delivery_info" in df.columns:
        df["delivery_fee"] = _parse_delivery_fee(df["delivery_info"])

    if "is_best_seller" in df.columns:
        df["is_best_seller"] = _to_bool(df["is_best_seller"])
    else:
        df["is_best_seller"] = False

    if "is_amazon_choice" in df.columns:
        df["is_amazon_choice"] = _to_bool(df["is_amazon_choice"])
    else:
        df["is_amazon_choice"] = False

    df["price_clean"] = (
        pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
        if "price" in df.columns
        else 0.0
    )
    df["rating_clean"] = (
        pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
        if "rating" in df.columns
        else 0.0
    )

    crawl_text = "N/A"
    m = re.search(r"(\d{8})", csv_path.stem)
    if m:
        dt = pd.to_datetime(m.group(1), format="%Y%m%d", errors="coerce")
        if pd.notna(dt):
            crawl_text = dt.strftime("%d/%m/%Y")

    file_time = pd.Timestamp(csv_path.stat().st_mtime, unit="s").strftime(
        "%d/%m/%Y %H:%M"
    )
    meta = {
        "path": str(csv_path),
        "crawl_range": crawl_text,
        "file_time": file_time,
    }
    return df, meta
