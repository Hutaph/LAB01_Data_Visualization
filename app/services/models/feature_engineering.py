"""
Backward-compatible shim for `services.models.feature_engineering`.

This module imports and re-exports the real implementations from
`predictor.feature_engineering` so that pickled objects referencing
`services.models.feature_engineering.DiscountFeatureEngineer` or
`OutlierClipper` can be unpickled successfully.
"""
from predictor.feature_engineering import DiscountFeatureEngineer, OutlierClipper

__all__ = ["DiscountFeatureEngineer", "OutlierClipper"]
