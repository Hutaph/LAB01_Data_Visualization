"""
Legacy pipeline builder (script)
--------------------------------

This script contains a copy of the preprocessing pipeline implementation
that historically was used to create the `sales_prediction_processor.joblib`.
Prefer using `app/predictor/pipeline.py` (importable as `predictor.pipeline`)
for programmatic access. This file is kept for backwards compatibility.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from services.models.feature_engineering import DiscountFeatureEngineer, OutlierClipper


class PreprocessorTransformer(BaseEstimator, TransformerMixin):
    """Normalize column names, fill basic defaults and coerce types."""

    SYNONYMS = {
        "review_count": "reviews",
        "offer_count": "number_of_offers",
        "category": "crawl_category",
        "is_choice": "is_amazon_choice",
        "is_climate": "is_climate_friendly",
        "has_variation": "has_variations",
        # keep lowest_offer_price the same name
    }

    PLACEHOLDERS = ["[]", "{}", "", "missing value", "N/A", "nan"]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X = X.copy()

        # replace common placeholder strings with NaN
        X = X.replace(self.PLACEHOLDERS, np.nan)

        # apply synonyms
        for src, dst in self.SYNONYMS.items():
            if dst not in X.columns and src in X.columns:
                X[dst] = X[src]

        # ensure expected numeric columns exist
        numeric_cols = [
            "price",
            "original_price",
            "rating",
            "reviews",
            "number_of_offers",
            "lowest_offer_price",
            "delivery_fee",
            "sales_volume_num",
        ]
        for c in numeric_cols:
            if c not in X.columns:
                X[c] = np.nan

        # coerce numeric types where possible
        for c in ["price", "original_price", "rating", "reviews", "number_of_offers", "lowest_offer_price", "delivery_fee", "sales_volume_num"]:
            if c in X.columns:
                X[c] = pd.to_numeric(X[c], errors="coerce")

        # original_price fallback to price
        if "original_price" in X.columns and "price" in X.columns:
            X["original_price"] = X["original_price"].fillna(X["price"])

        # booleans: normalize to 0/1 where present
        bool_cols = [
            "is_prime",
            "is_amazon_choice",
            "is_climate_friendly",
            "has_variations",
        ]
        for b in bool_cols:
            if b in X.columns:
                # convert truthy strings and booleans to int
                X[b] = X[b].map({True: 1, False: 0}).fillna(X[b])
                try:
                    X[b] = pd.to_numeric(X[b], errors="coerce").fillna(0).astype(int)
                except Exception:
                    X[b] = X[b].apply(lambda v: 1 if str(v).strip().lower() in ("true", "1", "yes", "y") else 0)
            else:
                X[b] = 0

        # ensure crawl_category exists (string)
        if "crawl_category" not in X.columns:
            X["crawl_category"] = X.get("crawl_category", np.nan)
        X["crawl_category"] = X["crawl_category"].astype(object)

        # sales_volume_num: if missing, assume 0
        if "sales_volume_num" not in X.columns or X["sales_volume_num"].isna().all():
            X["sales_volume_num"] = 0

        return X


class LogAndClipper(BaseEstimator, TransformerMixin):
    """Log-transform selected numeric cols and clip them to fit quantiles computed at fit time.

    Produces new columns named {col}_log_clipped for each col in `cols`.
    """

    def __init__(self, cols=None, lower_q=0.01, upper_q=0.99):
        self.cols = cols or [
            "price",
            "original_price",
            "reviews",
            "number_of_offers",
            "lowest_offer_price",
            "sales_volume_num",
            "delivery_fee",
        ]
        self.lower_q = lower_q
        self.upper_q = upper_q
        self.lower_ = {}
        self.upper_ = {}

    def fit(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        for col in self.cols:
            if col in X.columns:
                arr = pd.to_numeric(X[col], errors="coerce").fillna(0).astype(float)
                logv = np.log1p(arr)
                try:
                    self.lower_[col] = float(np.nanquantile(logv, self.lower_q))
                    self.upper_[col] = float(np.nanquantile(logv, self.upper_q))
                except Exception:
                    self.lower_[col] = float(np.nanmin(logv) if len(logv) else 0.0)
                    self.upper_[col] = float(np.nanmax(logv) if len(logv) else 0.0)
            else:
                self.lower_[col] = 0.0
                self.upper_[col] = 0.0
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X = X.copy()
        for col in self.cols:
            if col in X.columns:
                arr = pd.to_numeric(X[col], errors="coerce").fillna(0).astype(float)
                logv = np.log1p(arr)
                low = self.lower_.get(col, np.nan)
                high = self.upper_.get(col, np.nan)
                clipped = np.clip(logv, low, high)
                X[f"{col}_log_clipped"] = clipped
            else:
                X[f"{col}_log_clipped"] = 0.0
        return X


def build_processor(sample_df: pd.DataFrame) -> Pipeline:
    """Build and fit a preprocessing Pipeline from a sample DataFrame.

    The pipeline mirrors notebook steps: rename, fill, log+clip, one-hot category, scale numeric.
    """
    pre = PreprocessorTransformer()
    logclip = LogAndClipper()

    # columns produced by logclip
    log_cols = [f"{c}_log_clipped" for c in logclip.cols]

    # numeric columns to scale (rating + log clipped cols)
    cols_to_scale = ["rating"] + log_cols

    # boolean columns
    bool_cols = ["is_prime", "is_amazon_choice", "is_climate_friendly", "has_variations"]

    # categorical column
    cat_col = ["crawl_category"]

    # numeric pipeline: impute then scale
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
        ("scaler", StandardScaler()),
    ])

    # categorical pipeline
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    coltrans = ColumnTransformer([
        ("num", num_pipeline, cols_to_scale),
        ("cat", cat_pipeline, cat_col),
        ("bools", "passthrough", bool_cols),
    ], remainder="drop")

    pipe = Pipeline([
        ("pre", pre),
        ("logclip", logclip),
        ("discount", DiscountFeatureEngineer()),
        ("coltrans", coltrans),
    ])

    # fit pipeline
    pipe.fit(sample_df)
    return pipe


def load_processor(path: str | Path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Processor not found: {path}")
    return joblib.load(path)


def save_processor(proc, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(proc, path)


def ensure_processor(processor_path: str | Path, sample_df: pd.DataFrame | None = None):
    """Load an existing processor or build/save a new one using sample_df.

    Returns the fitted processor.
    """
    p = Path(processor_path)
    if p.exists():
        try:
            return load_processor(p)
        except Exception:
            # fallthrough to build
            pass

    if sample_df is None:
        raise RuntimeError("Processor missing and no sample_df provided to build one.")

    proc = build_processor(sample_df)
    save_processor(proc, p)
    return proc


def transform_with_feature_names(processor, X: pd.DataFrame) -> pd.DataFrame:
    """Transform DataFrame and return DataFrame with feature names if available.

    If names cannot be determined, returns a DataFrame with auto-generated column names.
    """
    arr = processor.transform(X)
    if isinstance(arr, np.ndarray):
        # try to get names
        cols = None
        try:
            if hasattr(processor, "get_feature_names_out"):
                cols = list(processor.get_feature_names_out())
        except Exception:
            cols = None
        if cols is None:
            # try column transformer inside pipeline
            try:
                ct = None
                for name, step in processor.steps:
                    if isinstance(step, ColumnTransformer):
                        ct = step
                        break
                    if name == "coltrans":
                        ct = step
                        break
                if ct is not None and hasattr(ct, "get_feature_names_out"):
                    cols = list(ct.get_feature_names_out())
            except Exception:
                cols = None

        if cols is None:
            cols = [f"f_{i}" for i in range(arr.shape[1])]
        return pd.DataFrame(arr, columns=cols)
    else:
        # assume processor returns DataFrame-like
        try:
            return pd.DataFrame(arr)
        except Exception:
            return pd.DataFrame(arr)
