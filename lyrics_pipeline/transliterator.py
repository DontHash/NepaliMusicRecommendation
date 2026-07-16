"""Optional char-transformer transliteration for romanized Nepali tokens."""

from __future__ import annotations

import pickle
import re
import unicodedata
from pathlib import Path

from .patterns import DEVANAGARI_RE, ROMAN_TOKEN_RE

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

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
        self.transformer = nn.Transformer(
            d_model=embed_dim,
            nhead=num_heads,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=ff_dim,
            dropout=dropout,
            batch_first=True,
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

    def decode_step(self, tgt, memory, memory_padding_mask):
        tgt_emb = self.positional_encoding(self.embedding(tgt))
        tgt_mask = self.make_causal_mask(tgt.size(1), tgt.device)
        tgt_padding_mask = self.make_padding_mask(tgt)
        decoded = self.transformer.decoder(
            tgt=tgt_emb,
            memory=memory,
            tgt_mask=tgt_mask,
            tgt_key_padding_mask=tgt_padding_mask,
            memory_key_padding_mask=memory_padding_mask,
        )
        return self.output_layer(decoded)

    def beam_search_decode(self, src, beam_size=5, max_len=None):
        max_len = max_len or self.tgt_max_len
        memory, src_padding_mask = self.encode(src)
        beams = [(torch.tensor([[self.sos_id]], device=src.device), 0.0, False)]
        completed = []

        for _ in range(max_len - 1):
            candidates = []
            for sequence, score, done in beams:
                if done:
                    candidates.append((sequence, score, True))
                    continue
                logits = self.decode_step(sequence, memory, src_padding_mask)
                log_probs = F.log_softmax(logits[:, -1], dim=-1)
                topk_log_probs, topk_ids = torch.topk(log_probs, beam_size, dim=-1)
                for rank in range(beam_size):
                    token_id = topk_ids[0, rank].item()
                    token_score = topk_log_probs[0, rank].item()
                    new_sequence = torch.cat(
                        [sequence, torch.tensor([[token_id]], device=src.device)], dim=1
                    )
                    candidates.append((new_sequence, score + token_score, token_id == self.eos_id))

            candidates.sort(key=lambda item: item[1], reverse=True)
            beams = []
            for sequence, score, done in candidates:
                if done:
                    completed.append((sequence, score))
                else:
                    beams.append((sequence, score, False))
                if len(beams) >= beam_size:
                    break
            if not beams:
                break

        if completed:
            completed.sort(key=lambda item: item[1] / max(item[0].size(1), 1), reverse=True)
            return completed[0][0]
        beams.sort(key=lambda item: item[1] / max(item[0].size(1), 1), reverse=True)
        return beams[0][0]

    def greedy_decode(self, src, max_len=None):
        max_len = max_len or self.tgt_max_len
        memory, src_padding_mask = self.encode(src)
        generated = torch.full((src.size(0), 1), self.sos_id, dtype=torch.long, device=src.device)
        for _ in range(max_len - 1):
            logits = self.decode_step(generated, memory, src_padding_mask)
            next_token = logits[:, -1].argmax(dim=-1, keepdim=True)
            generated = torch.cat([generated, next_token], dim=1)
            if torch.all(next_token.squeeze(1) == self.eos_id):
                break
        return generated


class NepaliTransliterator:
    """Word-level roman to Devanagari using an optional char-transformer checkpoint."""

    def __init__(
        self,
        checkpoint_path: Path | str | None = None,
        vocab_path: Path | str | None = None,
        beam_size: int = 5,
        device: str | None = None,
        decode: str = "greedy",
    ):
        self.beam_size = beam_size
        self.decode = decode
        self.model = None
        self.char_to_id = None
        self.id_to_char = None
        self.special_tokens = None
        self.device = None
        self._word_cache: dict[str, str] = {}

        if not TORCH_AVAILABLE:
            return

        checkpoint_path = self._resolve_existing(
            checkpoint_path,
            "char_transformer_442.pt",
            "new_char_transformer_best.pt",
            "char_transformer_best.pt",
        )
        vocab_path = self._resolve_existing(
            vocab_path,
            "char_vocab.pkl",
            "new_char_vocab.pkl",
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
        for idx in ids:
            token = self.id_to_char[int(idx)]
            if token == "<eos>":
                break
            if token in self.special_tokens:
                continue
            chars.append(token)
        return "".join(chars)

    def transliterate_word(self, word: str) -> str:
        if not word or not ROMAN_TOKEN_RE.search(word):
            return word
        if not self.available:
            return word

        key = word.lower()
        if key in self._word_cache:
            return self._word_cache[key]

        src_ids = torch.tensor(self._text_to_ids(word), dtype=torch.long).unsqueeze(0).to(self.device)
        with torch.no_grad():
            if self.decode == "beam":
                output_ids = self.model.beam_search_decode(src_ids, beam_size=self.beam_size)[0].tolist()
            else:
                output_ids = self.model.greedy_decode(src_ids)[0].tolist()
        result = self._ids_to_text(output_ids)
        self._word_cache[key] = result
        return result

    def transliterate_line(self, line: str) -> str:
        if not line:
            return line
        if DEVANAGARI_RE.search(line) and not ROMAN_TOKEN_RE.search(line):
            return line

        parts = re.findall(r"[A-Za-z]+|[^A-Za-z]+", line)
        converted = []
        for part in parts:
            if ROMAN_TOKEN_RE.fullmatch(part):
                converted.append(self.transliterate_word(part))
            else:
                converted.append(part)
        return "".join(converted)

    def transliterate_text(self, text: str) -> str:
        return "\n".join(self.transliterate_line(line) for line in text.splitlines())
