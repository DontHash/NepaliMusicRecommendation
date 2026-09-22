"""ONNX Runtime query-text encoder (no transformers/torch import at runtime).

Loads the artifact produced by ``scripts/export_embedding_onnx.py`` and
reproduces SentenceTransformer's mpnet encoding: fast tokenizer, mean pooling
over the attention mask. Used for short free-text queries, where avoiding the
~9s transformers import dominates first-query latency. Validate numerical
parity with ``scripts/check_onnx_parity.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np

DEFAULT_MAX_SEQ_LENGTH = 128


class OnnxEncoder:
    def __init__(
        self,
        model_path: Path,
        tokenizer_path: Path,
        *,
        dim: int = 768,
        max_seq_length: int = DEFAULT_MAX_SEQ_LENGTH,
    ):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        self._tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self._tokenizer.enable_truncation(max_length=max_seq_length)
        self.dim = int(dim)
        self.max_seq_length = int(max_seq_length)

    def encode(
        self,
        texts: str | Sequence[str],
        batch_size: int = 32,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
        **kwargs,
    ) -> np.ndarray:
        items = [texts] if isinstance(texts, str) else list(texts)
        vectors = []
        for text in items:
            encoding = self._tokenizer.encode(text or "")
            input_ids = np.asarray([encoding.ids], dtype=np.int64)
            attention_mask = np.asarray([encoding.attention_mask], dtype=np.int64)
            hidden = self.session.run(
                ["last_hidden_state"],
                {"input_ids": input_ids, "attention_mask": attention_mask},
            )[0]
            weights = attention_mask[..., None].astype(np.float32)
            pooled = (hidden * weights).sum(axis=1) / np.clip(
                weights.sum(axis=1), 1e-9, None
            )
            vectors.append(pooled[0].astype(np.float32))
        return np.vstack(vectors)
