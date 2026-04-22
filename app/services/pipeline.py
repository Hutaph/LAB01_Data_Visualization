"""
Services pipeline shim
---------------------

This module keeps the old import path `services.pipeline` working by
re-exporting the core functions implemented in `predictor.pipeline`.
Existing code that imports from `services.pipeline` will continue to work.
"""
from predictor.pipeline import (
    build_processor,
    load_processor,
    save_processor,
    ensure_processor,
    transform_with_feature_names,
)

__all__ = [
    "build_processor",
    "load_processor",
    "save_processor",
    "ensure_processor",
    "transform_with_feature_names",
]
