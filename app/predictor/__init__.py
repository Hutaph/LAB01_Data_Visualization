"""
Predictor package
-----------------
This package centralizes prediction-related code for the web app.

- Exports helper functions to build/load/save preprocessing pipelines.
- Provides constants for the models folder used by the app.

Keep this package small: heavy logic lives in `predictor.pipeline` and
`predictor.feature_engineering`.
"""
from pathlib import Path

# Models are stored under app/services/models (binaries are kept there).
MODELS_DIR = Path(__file__).resolve().parents[1] / "services" / "models"

from .pipeline import (
    build_processor,
    load_processor,
    save_processor,
    ensure_processor,
    transform_with_feature_names,
)

__all__ = [
    "MODELS_DIR",
    "build_processor",
    "load_processor",
    "save_processor",
    "ensure_processor",
    "transform_with_feature_names",
]
