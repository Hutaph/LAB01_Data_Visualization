class DiscountFeatureEngineer:
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X["discount"] = X["original_price"] - X["price"]
        X["discount_rate"] = X["discount"] / X["original_price"]
        return X


class OutlierClipper:
    """Minimal placeholder so pipelines saved from other environments
    that reference an `OutlierClipper` class can be unpickled here.
    This implementation is a no-op transformer and preserves input.
    It accepts any constructor arguments to be tolerant to different saved states.
    """
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X
