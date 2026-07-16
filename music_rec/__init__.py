"""Nepali lyrics music recommendation system (content-based POC)."""

import os

# Force the PyTorch-only path in transformers (avoids Keras 3 / TF import errors).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

from .config import Config

__all__ = ["Config"]
