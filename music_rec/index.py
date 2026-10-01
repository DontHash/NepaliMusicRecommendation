"""FAISS cosine index over embeddings or fused feature vectors.

``auto`` keeps exact ``IndexFlatIP`` while the corpus is small and switches to
approximate HNSW once an exact scan no longer fits the latency budget
(``PROJECTR_INDEX=flat|hnsw|auto``). HNSW is built with inner-product metric
over L2-normalised vectors, so scores are cosines exactly like the flat index.
"""

from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np

AUTO_HNSW_THRESHOLD = 50_000
DEFAULT_HNSW_M = 32
DEFAULT_EF_CONSTRUCTION = 200
DEFAULT_EF_SEARCH = 64


def resolve_index_type(index_type: str | None, n_vectors: int) -> str:
    kind = (index_type or "auto").lower()
    if kind not in {"auto", "flat", "hnsw"}:
        raise ValueError(f"unknown index type {index_type!r}")
    if kind == "auto":
        return "hnsw" if n_vectors >= AUTO_HNSW_THRESHOLD else "flat"
    return kind


def build_index(
    vectors: np.ndarray,
    index_path: Path,
    *,
    index_type: str | None = "auto",
    hnsw_m: int = DEFAULT_HNSW_M,
    ef_construction: int = DEFAULT_EF_CONSTRUCTION,
    ef_search: int = DEFAULT_EF_SEARCH,
) -> faiss.Index:
    vectors = normalize(vectors)
    n_vectors, dim = vectors.shape
    kind = resolve_index_type(index_type, n_vectors)
    if kind == "hnsw":
        index = faiss.IndexHNSWFlat(dim, hnsw_m, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = ef_construction
        index.hnsw.efSearch = ef_search
    else:
        index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    faiss.write_index(index, str(index_path))
    return index


def load_index(index_path: Path, *, ef_search: int | None = None) -> faiss.Index:
    index = faiss.read_index(str(index_path))
    if ef_search is not None and hasattr(index, "hnsw"):
        index.hnsw.efSearch = max(int(ef_search), DEFAULT_EF_SEARCH)
    return index


def index_kind(index: faiss.Index) -> str:
    return "hnsw" if hasattr(index, "hnsw") else "flat"


def normalize(vectors: np.ndarray) -> np.ndarray:
    vectors = np.ascontiguousarray(vectors.astype(np.float32))
    faiss.normalize_L2(vectors)
    return vectors


def search(
    index: faiss.Index,
    query: np.ndarray,
    top_k: int,
    *,
    ef_search: int | None = None,
):
    if ef_search is not None and hasattr(index, "hnsw"):
        index.hnsw.efSearch = max(int(ef_search), top_k)
    query = np.ascontiguousarray(query.astype(np.float32).reshape(1, -1))
    faiss.normalize_L2(query)
    scores, ids = index.search(query, top_k)
    return scores[0], ids[0]
