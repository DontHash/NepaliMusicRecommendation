"""FAISS cosine index over embeddings or fused feature vectors."""

from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np


def build_index(vectors: np.ndarray, index_path: Path) -> faiss.Index:
    vectors = np.ascontiguousarray(vectors.astype(np.float32))
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(index_path))
    return index


def load_index(index_path: Path) -> faiss.Index:
    return faiss.read_index(str(index_path))


def normalize(vectors: np.ndarray) -> np.ndarray:
    vectors = np.ascontiguousarray(vectors.astype(np.float32))
    faiss.normalize_L2(vectors)
    return vectors


def search(index: faiss.Index, query: np.ndarray, top_k: int):
    query = np.ascontiguousarray(query.astype(np.float32).reshape(1, -1))
    faiss.normalize_L2(query)
    scores, ids = index.search(query, top_k)
    return scores[0], ids[0]
