"""
Lightweight data loader wrappers for the predictor package.

This module re-uses existing `services.data_loader` helpers to provide a
consistent import path for code that builds or fits the processing pipeline.
"""
from services.data_loader import load_data as load_processed_data

__all__ = ["load_processed_data"]
