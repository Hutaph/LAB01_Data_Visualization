"""
Custom feature engineering transformers used by the prediction pipeline.

This module provides lightweight transformers that were used in model
training and may be referenced by pickled processor objects. Exporting
these classes from a stable import path (`predictor.feature_engineering`)
helps with unpickling saved pipelines during runtime.
"""
import pandas as pd


class DiscountFeatureEngineer:
    """Compute discount and discount rate from `price` and `original_price`.

    This mirrors the notebook logic: `discount = original_price - price`,
    `discount_rate = discount / original_price`.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X["discount"] = X.get("original_price", 0) - X.get("price", 0)
        # avoid division by zero
        X["discount_rate"] = X["discount"] / X["original_price"].replace({0: pd.NA}).astype(float)
        X["discount_rate"] = X["discount_rate"].fillna(0.0)
        return X


class OutlierClipper:
    """A tolerant no-op OutlierClipper implementation.

    The real clipping logic is done in the pipeline's `LogAndClipper`.
    This class exists so older pickled objects that reference
    `OutlierClipper` can be unpickled without errors.
    """

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X
