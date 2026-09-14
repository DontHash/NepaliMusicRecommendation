"""Optional char-transformer transliteration for romanized Nepali tokens.

Decoding is batched across words (and across beam hypotheses) so a whole
song can be transliterated in a handful of model calls instead of one
model call per word.
"""

from __future__ import annotations

import pickle
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path

from .patterns import DEVANAGARI_RE, ROMAN_TOKEN_RE

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.nn.utils.rnn import pad_sequence

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    TORCH_AVAILABLE = False


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text


class PositionalEncoding(nn.Module):
    def __init__(self, embed_dim, dropout=0.1, max_len=256):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        position = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, embed_dim, 2, dtype=torch.float32)
            * (-torch.log(torch.tensor(10000.0)) / embed_dim)
        )
        pe = torch.zeros(max_len, embed_dim)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        x = x + self.pe[:, : x.size(1)]
        return self.dropout(x)


class CharTransformer(nn.Module):
    def __init__(
        self,
        vocab_size,
        pad_id,
        sos_id,
        eos_id,
        src_max_len,
        tgt_max_len,
        embed_dim=256,
        num_heads=8,
        ff_dim=512,
        num_encoder_layers=3,
        num_decoder_layers=3,
        dropout=0.15,
    ):
        super().__init__()
        self.pad_id = pad_id
        self.sos_id = sos_id
        self.eos_id = eos_id
        self.src_max_len = src_max_len
        self.tgt_max_len = tgt_max_len
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_id)
        self.positional_encoding = PositionalEncoding(
            embed_dim, dropout=dropout, max_len=max(src_max_len, tgt_max_len) + 16
        )
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=ff_dim,
            dropout=dropout,
            batch_first=True,
        )
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=ff_dim,
            dropout=dropout,
            batch_first=True,
        )
        # Container keeps the ``transformer.encoder/decoder`` state-dict keys
        # of the trained checkpoints. Nested tensors are disabled: the
        # prototype ragged path is slow on CPU and adds nothing here.
        self.transformer = nn.Module()
        self.transformer.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_encoder_layers,
            norm=nn.LayerNorm(embed_dim),
            enable_nested_tensor=False,
        )
        self.transformer.decoder = nn.TransformerDecoder(
            decoder_layer, num_decoder_layers, norm=nn.LayerNorm(embed_dim)
        )
        self.output_layer = nn.Linear(embed_dim, vocab_size)

    def make_padding_mask(self, tokens):
        return tokens == self.pad_id

    def make_causal_mask(self, size, device):
        return torch.triu(torch.ones(size, size, device=device, dtype=torch.bool), diagonal=1)

    def encode(self, src):
        src_emb = self.positional_encoding(self.embedding(src))
        src_padding_mask = self.make_padding_mask(src)
        memory = self.transformer.encoder(src_emb, src_key_padding_mask=src_padding_mask)
        return memory, src_padding_mask

    def decode_step(self, tgt, memory, memory_padding_mask=None):
        tgt_emb = self.positional_encoding(self.embedding(tgt))
        tgt_mask = self.make_causal_mask(tgt.size(1), tgt.device)
        decoded = self.transformer.decoder(
            tgt=tgt_emb,
            memory=memory,
            tgt_mask=tgt_mask,
            memory_key_padding_mask=memory_padding_mask,
        )
        return self.output_layer(decoded)

    def greedy_decode_batch(self, src, max_len=None):
        """Greedy decode a batch of sources with one decoder pass per step.

        Rows that hit <eos> are frozen (padded) so the batch always advances
        in lock-step; the frozen tail is never emitted.
        """
        max_len = max(max_len or self.tgt_max_len, 2)
        batch = src.size(0)
        with torch.inference_mode():
            memory, src_padding_mask = self.encode(src)
            gen = torch.full((batch, 1), self.sos_id, dtype=torch.long, device=src.device)
            done = torch.zeros(batch, 1, dtype=torch.bool, device=src.device)
            for _ in range(max_len - 1):
                logits = self.decode_step(gen, memory, src_padding_mask)
                next_token = logits[:, -1].argmax(dim=-1, keepdim=True)
                done = done | (next_token == self.eos_id)
                next_token = torch.where(
                    done, torch.full_like(next_token, self.pad_id), next_token
                )
                gen = torch.cat([gen, next_token], dim=1)
                if bool(done.all()):
                    break
            return gen

    def beam_search_decode_batch(self, src, beam_size=5, max_len=None):
        """Vectorized beam search over a batch of sources.

        All beam hypotheses of all batch rows are decoded in a single
        decoder pass per step. Finished beams are parked with frozen
        scores (like a ``completed`` list) and never expanded again; the
        final choice is the best length-normalized score across all
        parked and live beams.
        """
        max_len = max(max_len or self.tgt_max_len, 2)
        batch = src.size(0)
        vocab_size = None
        with torch.inference_mode():
            memory, src_padding_mask = self.encode(src)  # (B, S, d), (B, S)
            memory = memory.repeat_interleave(beam_size, dim=0)
            src_padding_mask = src_padding_mask.repeat_interleave(beam_size, dim=0)

            device = src.device
            seqs = torch.full((batch, beam_size, 1), self.sos_id, dtype=torch.long, device=device)
            scores = torch.zeros(batch, beam_size, device=device)
            done = torch.zeros(batch, beam_size, dtype=torch.bool, device=device)
            lengths = torch.ones(batch, beam_size, device=device)

            for step in range(max_len - 1):
                flat = seqs.reshape(batch * beam_size, seqs.size(-1))
                logits = self.decode_step(flat, memory, src_padding_mask)
                lp = F.log_softmax(logits[:, -1], dim=-1)
                vocab_size = lp.size(-1)
                lp = lp.reshape(batch, beam_size, vocab_size)

                # Finished beams are parked: they never win slots again.
                cand = scores.unsqueeze(-1) + lp
                cand = torch.where(
                    done.unsqueeze(-1),
                    torch.full_like(cand, float("-inf")),
                    cand,
                )
                flat_scores = cand.reshape(batch, beam_size * vocab_size)
                top_scores, top_idx = torch.topk(flat_scores, beam_size, dim=1)
                prev = top_idx // vocab_size
                tok = top_idx % vocab_size

                chosen = seqs.gather(1, prev.unsqueeze(-1).expand(-1, -1, seqs.size(-1)))
                seqs = torch.cat([chosen, tok.unsqueeze(-1)], dim=-1)
                scores = top_scores

                newly_done = tok == self.eos_id
                lengths = torch.where(newly_done, torch.full_like(lengths, float(seqs.size(-1))), lengths)
                done = done | newly_done
                if bool(done.all()):
                    break

            # Non-finished beams normalize by their actual length.
            lengths = torch.where(done, lengths, torch.full_like(lengths, float(seqs.size(-1))))
            norm = scores / lengths
            best = norm.argmax(dim=1)
            out = seqs.gather(
                1, best.unsqueeze(-1).unsqueeze(-1).expand(-1, -1, seqs.size(-1))
            ).squeeze(1)
            return out

    def greedy_decode(self, src, max_len=None):
        return self.greedy_decode_batch(src, max_len=max_len)[0:1]

    def beam_search_decode(self, src, beam_size=5, max_len=None):
        return self.beam_search_decode_batch(src, beam_size=beam_size, max_len=max_len)[0:1]


class NepaliTransliterator:
    """Word-level roman to Devanagari using an optional char-transformer checkpoint."""

    def __init__(
        self,
        checkpoint_path: Path | str | None = None,
        vocab_path: Path | str | None = None,
        beam_size: int = 5,
        device: str | None = None,
        decode: str = "greedy",
        batch_size: int = 256,
        cache_size: int = 200_000,
    ):
        self.beam_size = beam_size
        self.decode = decode
        self.batch_size = max(batch_size, 1)
        self.model = None
        self.char_to_id = None
        self.id_to_char = None
        self.special_tokens = None
        self.device = None
        self._word_cache: OrderedDict[str, tuple[list[int], str]] = OrderedDict()
        self._cache_size = max(cache_size, 1)

        if not TORCH_AVAILABLE:
            return

        checkpoint_path = self._resolve_existing(
            checkpoint_path,
            "new_char_transformer_best.pt",
            "char_transformer_442.pt",
            "char_transformer_best.pt",
        )
        vocab_path = self._resolve_existing(
            vocab_path,
            "new_char_vocab.pkl",
            "char_vocab.pkl",
        )
        if checkpoint_path is None or vocab_path is None:
            return

        with open(vocab_path, "rb") as f:
            vocab = pickle.load(f)

        self.char_to_id = vocab["char_to_id"]
        self.id_to_char = vocab["id_to_char"]
        self.special_tokens = set(vocab.get("SPECIAL_TOKENS", []))
        pad_id = vocab["PAD_ID"]
        sos_id = vocab["SOS_ID"]
        eos_id = vocab["EOS_ID"]
        unk_id = vocab["UNK_ID"]
        src_max_len = vocab["SRC_MAX_LEN"]
        tgt_max_len = vocab["TGT_MAX_LEN"]
        vocab_size = vocab["VOCAB_SIZE"]

        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = CharTransformer(
            vocab_size,
            pad_id,
            sos_id,
            eos_id,
            src_max_len,
            tgt_max_len,
        ).to(self.device)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        state_dict = checkpoint["model_state"] if isinstance(checkpoint, dict) and "model_state" in checkpoint else checkpoint
        self.model.load_state_dict(state_dict)
        self.model.eval()

        self._pad_id = pad_id
        self._sos_id = sos_id
        self._eos_id = eos_id
        self._unk_id = unk_id
        self._src_max_len = src_max_len
        self._tgt_max_len = tgt_max_len

    @property
    def available(self) -> bool:
        return self.model is not None

    @staticmethod
    def _resolve_existing(primary: Path | str | None, *fallback_names: str) -> Path | None:
        candidates: list[Path] = []
        if primary:
            candidates.append(Path(primary))
        project_root = Path(__file__).resolve().parents[1]
        for name in fallback_names:
            candidates.extend(
                [
                    Path.cwd() / name,
                    project_root / name,
                    project_root / "CSVs Dataset" / name,
                    project_root / "R_data" / "datasets" / name,
                ]
            )
        for path in candidates:
            if path.exists():
                return path
        return None

    def _text_to_ids(self, text: str) -> list[int]:
        text = normalize_text(text).lower()
        ids = [self._sos_id]
        for char in text:
            ids.append(self.char_to_id.get(char, self._unk_id))
            if len(ids) >= self._src_max_len - 1:
                break
        ids.append(self._eos_id)
        return ids[: self._src_max_len]

    def _ids_to_text(self, ids) -> str:
        chars = []
        table = self.id_to_char
        is_list = isinstance(table, list)
        for idx in ids:
            idx = int(idx)
            if idx == self._pad_id or idx == self._eos_id:
                break
            if is_list:
                token = table[idx] if 0 <= idx < len(table) else ""
            else:
                token = table.get(idx, "")
            if not token or token in self.special_tokens:
                continue
            chars.append(token)
        return "".join(chars)

    def _cache_get(self, key: str) -> tuple[list[int], str] | None:
        hit = self._word_cache.get(key)
        if hit is not None:
            self._word_cache.move_to_end(key)
        return hit

    def _cache_put(self, key: str, value: tuple[list[int], str]) -> None:
        self._word_cache[key] = value
        self._word_cache.move_to_end(key)
        while len(self._word_cache) > self._cache_size:
            self._word_cache.popitem(last=False)

    def _decode_batch(self, id_lists: list[list[int]]) -> list[str]:
        """Decode id-lists in dense length-sorted batches.

        Words are sorted by source length and chunked so each batch only
        pads to its own chunk maximum (bounded padding). Nested tensors are
        disabled at construction, so the boolean padding masks run through
        the plain dense path and results stay bit-identical to per-word
        decoding while amortizing per-call overhead across ~batch_size words.
        """
        results: list[str] = [""] * len(id_lists)
        order = sorted(range(len(id_lists)), key=lambda i: len(id_lists[i]))

        for start in range(0, len(order), self.batch_size):
            chunk = order[start : start + self.batch_size]
            src = pad_sequence(
                [torch.tensor(id_lists[i], dtype=torch.long) for i in chunk],
                batch_first=True,
                padding_value=self._pad_id,
            ).to(self.device)
            with torch.inference_mode():
                if self.decode == "beam":
                    decoded = self.model.beam_search_decode_batch(src, beam_size=self.beam_size)
                else:
                    decoded = self.model.greedy_decode_batch(src)
            for rank, i in enumerate(chunk):
                results[i] = self._ids_to_text(decoded[rank].tolist())
        return results

    def transliterate_tokens(self, tokens: list[str]) -> list[str]:
        """Transliterate a list of tokens, batching unknown words together.

        Non-roman tokens (Devanagari, digits, punctuation) are returned
        unchanged. Cached words never touch the model.
        """
        tokens = list(tokens)
        out: list[str] = [""] * len(tokens)
        fresh: list[tuple[int, str]] = []
        for i, tok in enumerate(tokens):
            if not tok or not ROMAN_TOKEN_RE.fullmatch(tok):
                out[i] = tok
                continue
            key = tok.lower()
            hit = self._cache_get(key)
            if hit is not None:
                out[i] = hit[1]
            else:
                fresh.append((i, key))

        if not fresh:
            return out
        if not self.available:
            for i, _ in fresh:
                out[i] = tokens[i]
            return out

        seen: dict[str, list[int]] = {}
        for i, key in fresh:
            seen.setdefault(key, []).append(i)
        keys = list(seen)
        id_lists = [self._text_to_ids(key) for key in keys]
        decoded = self._decode_batch(id_lists)
        for rank, key in enumerate(keys):
            self._cache_put(key, (id_lists[rank], decoded[rank]))
            for i in seen[key]:
                out[i] = decoded[rank]
        return out

    def transliterate_word(self, word: str) -> str:
        if not word or not ROMAN_TOKEN_RE.search(word):
            return word
        if not self.available:
            return word
        return self.transliterate_tokens([word])[0]

    def transliterate_line(self, line: str) -> str:
        if not line:
            return line
        if DEVANAGARI_RE.search(line) and not ROMAN_TOKEN_RE.search(line):
            return line

        parts = re.findall(r"[A-Za-z]+|[^A-Za-z]+", line)
        roman_positions = [i for i, part in enumerate(parts) if ROMAN_TOKEN_RE.fullmatch(part)]
        if not roman_positions:
            return line
        converted = self.transliterate_tokens([parts[i] for i in roman_positions])
        for pos, result in zip(roman_positions, converted):
            parts[pos] = result
        return "".join(parts)

    def transliterate_text(self, text: str) -> str:
        """Transliterate multi-line text with one shared batch per call."""
        if not text:
            return text
        lines = text.splitlines()
        parts_per_line: list[list[str]] = []
        roman_jobs: list[tuple[int, int, str]] = []
        for line_index, line in enumerate(lines):
            parts = re.findall(r"[A-Za-z]+|[^A-Za-z]+", line)
            parts_per_line.append(parts)
            for part_index, part in enumerate(parts):
                if ROMAN_TOKEN_RE.fullmatch(part):
                    roman_jobs.append((line_index, part_index, part))
        if not roman_jobs:
            return text

        converted = self.transliterate_tokens([job[2] for job in roman_jobs])
        for (line_index, part_index, _), result in zip(roman_jobs, converted):
            parts_per_line[line_index][part_index] = result
        return "\n".join("".join(parts) for parts in parts_per_line)
