"""Fine-tune the transliterator on in-domain song pairs with Aksharantar replay.

The shipped checkpoint was trained on Aksharantar only, so it reads song-style
romanization through the wrong convention (``cha`` -> चा, ``vana`` -> वना) and
falls apart on proper nouns. This fine-tunes it on teacher-labeled corpus word
pairs, mixed with a replay slice of Aksharantar so the broad vocabulary does not
regress, and keeps the Aksharantar valid split as the early-stopping guard.

Writes a new checkpoint (the original is left untouched) plus a metadata JSON.

Usage:
    python scripts/finetune_transliterator.py --max-steps 20          # timing probe
    python scripts/finetune_transliterator.py --epochs 3
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import random
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from torch.nn.utils.rnn import pad_sequence  # noqa: E402

from lyrics_pipeline.transliterator import CharTransformer  # noqa: E402

LABELS = PROJECT_ROOT / "R_data" / "raw" / "gemini" / "translit_corpus_v1" / "labels.jsonl"
AKSHARANTAR_DIR = PROJECT_ROOT / "R_data" / "raw" / "aksharantar"
CHECKPOINT = PROJECT_ROOT / "new_char_transformer_best.pt"
VOCAB = PROJECT_ROOT / "new_char_vocab.pkl"
DEFAULT_OUT = PROJECT_ROOT / "new_char_transformer_domain.pt"
DEFAULT_META = PROJECT_ROOT / "music_rec_artifacts" / "transliteration_finetune_report.json"

ROMAN_TOKEN_RE = re.compile(r"[A-Za-z]+")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
WORD_EDGE_PUNCT = ",.;:!?\"'()[]{}।—–-"
# Characters a clean label may contain. Anything else is corruption picked up
# from the teacher (Cyrillic lookalikes such as ``ма``, Arabic ``ا``).
ALLOWED_CHAR_RE = re.compile(
    r"[\u0900-\u097F\sA-Za-z0-9,.;:!?\"'()\[\]{}।\u2014\u2013&/+-]"
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


def normalize_token(text: str) -> str:
    return normalize(text).strip(WORD_EDGE_PUNCT).strip()


def load_vocab(path: Path) -> dict:
    with open(path, "rb") as handle:
        return pickle.load(handle)


def build_model(vocab: dict, checkpoint: Path, device: torch.device) -> CharTransformer:
    model = CharTransformer(
        vocab["VOCAB_SIZE"],
        vocab["PAD_ID"],
        vocab["SOS_ID"],
        vocab["EOS_ID"],
        vocab["SRC_MAX_LEN"],
        vocab["TGT_MAX_LEN"],
    )
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    state = payload["model_state"] if isinstance(payload, dict) and "model_state" in payload else payload
    model.load_state_dict(state)
    return model.to(device)


def text_to_ids(text: str, vocab: dict, max_length: int) -> list[int]:
    ids = [vocab["SOS_ID"]]
    for char in normalize(text).lower():
        ids.append(vocab["char_to_id"].get(char, vocab["UNK_ID"]))
        if len(ids) >= max_length - 1:
            break
    ids.append(vocab["EOS_ID"])
    return ids[:max_length]


def in_domain_pairs(
    labels_path: Path, min_dominant_share: float = 0.0
) -> tuple[Counter, dict]:
    """Aligned (roman, Devanagari) word pairs from the teacher labels, denoised.

    Two filters, measured on the 34k-label run:

    - **Line filters** drop labels that carry no transliteration signal or carry
      corruption: lines whose Devanagari output is empty (English, credits,
      chord charts, Hindi) and lines containing characters outside the allowed
      script set (Cyrillic/Arabic lookalikes).
    - **Majority vote** keeps, for every roman token seen more than once, only
      the occurrences that match the dominant reading. Single-occurrence tokens
      are kept as-is: they are the long tail the model needs to see.
      ``min_dominant_share`` can additionally drop tokens whose reading is too
      split to trust (0.0 keeps everything).
    """
    pairs: Counter = Counter()
    stats = {
        "lines_total": 0,
        "lines_skipped_no_devanagari": 0,
        "lines_skipped_unexpected_script": 0,
        "lines_skipped_unaligned": 0,
        "pairs_raw": 0,
        "pairs_kept": 0,
        "tokens_dropped_low_share": 0,
        "occurrences_dropped_minority": 0,
    }
    rows: list[dict] = []
    if labels_path.suffix.lower() == ".jsonl":
        with open(labels_path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    else:
        with open(labels_path, encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

    raw: Counter = Counter()
    for row in rows:
        stats["lines_total"] += 1
        devanagari = row.get("devanagari") or ""
        if not DEVANAGARI_RE.search(devanagari):
            stats["lines_skipped_no_devanagari"] += 1
            continue
        if any(not ALLOWED_CHAR_RE.match(char) for char in devanagari):
            stats["lines_skipped_unexpected_script"] += 1
            continue
        roman_tokens = ROMAN_TOKEN_RE.findall(row.get("roman") or "")
        dev_tokens = [normalize_token(token) for token in devanagari.split()]
        dev_tokens = [token for token in dev_tokens if token]
        if len(roman_tokens) != len(dev_tokens):
            stats["lines_skipped_unaligned"] += 1
            continue
        for roman, devanagari_token in zip(roman_tokens, dev_tokens):
            if DEVANAGARI_RE.search(devanagari_token):
                raw[(roman.lower(), devanagari_token)] += 1

    stats["pairs_raw"] = sum(raw.values())
    readings: dict[str, Counter] = {}
    for (roman, devanagari), count in raw.items():
        readings.setdefault(roman, Counter())[devanagari] += count
    for (roman, devanagari), count in raw.items():
        options = readings[roman]
        total = sum(options.values())
        dominant, dominant_count = options.most_common(1)[0]
        if total >= 2:
            if dominant_count / total < min_dominant_share:
                stats["tokens_dropped_low_share"] += 1
                stats["occurrences_dropped_minority"] += count
                continue
            if devanagari != dominant:
                stats["occurrences_dropped_minority"] += count
                continue
        pairs[(roman, devanagari)] += count
    stats["pairs_kept"] = sum(pairs.values())
    return pairs, stats


def replay_pairs(path: Path, count: int, seed: int = 42) -> list[tuple[str, str]]:
    if not path.exists() or count <= 0:
        return []
    rng = random.Random(seed)
    reservoir: list[tuple[str, str]] = []
    with open(path, encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            roman = normalize(json.loads(line)["english word"]).lower()
            native = normalize(json.loads(line)["native word"])
            if not roman or not native:
                continue
            if len(reservoir) < count:
                reservoir.append((roman, native))
            else:
                j = rng.randint(0, index)
                if j < count:
                    reservoir[j] = (roman, native)
    return reservoir


def make_batches(
    pairs: list[tuple[str, str]],
    vocab: dict,
    batch_size: int,
    shuffle: bool,
    seed: int,
    device: torch.device | None = None,
):
    src_max, tgt_max = vocab["SRC_MAX_LEN"], vocab["TGT_MAX_LEN"]
    order = list(range(len(pairs)))
    if shuffle:
        random.Random(seed).shuffle(order)
    for start in range(0, len(order), batch_size):
        chunk = order[start : start + batch_size]
        src = pad_sequence(
            [torch.tensor(text_to_ids(pairs[i][0], vocab, src_max)) for i in chunk],
            batch_first=True,
            padding_value=vocab["PAD_ID"],
        )
        tgt = pad_sequence(
            [torch.tensor(text_to_ids(pairs[i][1], vocab, tgt_max)) for i in chunk],
            batch_first=True,
            padding_value=vocab["PAD_ID"],
        )
        if device is not None:
            src, tgt = src.to(device), tgt.to(device)
        yield src, tgt


def levenshtein(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + (left_char != right_char))
            )
        previous = current
    return previous[-1]


def ids_to_text(ids, vocab: dict) -> str:
    table = vocab["id_to_char"]
    specials = set(vocab.get("SPECIAL_TOKENS", []))
    out = []
    for index in ids:
        index = int(index)
        if index in (vocab["PAD_ID"], vocab["EOS_ID"]):
            break
        token = table[index] if isinstance(table, list) else table.get(index, "")
        if token and token not in specials:
            out.append(token)
    return "".join(out)


@torch.inference_mode()
def evaluate(
    model: CharTransformer,
    pairs: list[tuple[str, str]],
    vocab: dict,
    batch_size: int,
    device: torch.device | None = None,
) -> dict:
    model.eval()
    distance = chars = exact = 0
    for src, tgt in make_batches(pairs, vocab, batch_size, shuffle=False, seed=0, device=device):
        decoded = model.greedy_decode_batch(src)
        for row, target in zip(decoded, tgt):
            prediction = ids_to_text(row.tolist(), vocab)
            reference = ids_to_text(target.tolist(), vocab)
            distance += levenshtein(prediction, reference)
            chars += max(len(reference), 1)
            exact += int(prediction == reference)
    return {
        "n": len(pairs),
        "cer": round(distance / chars, 4) if chars else 0.0,
        "exact_match": round(exact / len(pairs), 4) if pairs else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--vocab", type=Path, default=VOCAB)
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--meta", type=Path, default=DEFAULT_META)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-pairs", type=int, default=60_000, help="in-domain pair cap")
    parser.add_argument("--replay-pairs", type=int, default=60_000, help="Aksharantar replay cap")
    parser.add_argument("--valid-pairs", type=int, default=2_000)
    parser.add_argument("--max-steps", type=int, default=0, help="stop early (timing probe)")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="auto uses CUDA when available (short fine-tunes are fine on the laptop GPU)",
    )
    parser.add_argument(
        "--min-dominant-share",
        type=float,
        default=0.0,
        help="Drop multi-occurrence tokens whose dominant reading is below this share",
    )
    parser.add_argument(
        "--force-save",
        action="store_true",
        help="Save every epoch even when the Aksharantar guard does not improve (experiments)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=0, help="torch CPU threads (0 = default)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_steps and args.out == DEFAULT_OUT:
        sys.exit(
            "--max-steps is a probe: pass an explicit --out so the installed "
            "checkpoint cannot be overwritten by a partial run"
        )
    if args.threads:
        torch.set_num_threads(args.threads)
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    vocab = load_vocab(args.vocab)
    model = build_model(vocab, args.checkpoint, device)

    in_domain, denoise = in_domain_pairs(args.labels, args.min_dominant_share)
    domain_pairs = [pair for pair, _ in in_domain.most_common(args.max_pairs)]
    replay = replay_pairs(AKSHARANTAR_DIR / "nep_train.json", args.replay_pairs, args.seed)
    train_pairs = domain_pairs + replay
    random.Random(args.seed).shuffle(train_pairs)

    valid_rows = []
    valid_path = AKSHARANTAR_DIR / "nep_valid.json"
    if valid_path.exists():
        with open(valid_path, encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                valid_rows.append((normalize(record["english word"]).lower(), normalize(record["native word"])))
    valid_pairs = valid_rows[: args.valid_pairs]

    print(f"device: {device}")
    print(
        f"denoise: lines {denoise['lines_total']} -> kept "
        f"{denoise['lines_total'] - denoise['lines_skipped_no_devanagari'] - denoise['lines_skipped_unexpected_script'] - denoise['lines_skipped_unaligned']}"
        f" (no-dev {denoise['lines_skipped_no_devanagari']}, script {denoise['lines_skipped_unexpected_script']}, "
        f"unaligned {denoise['lines_skipped_unaligned']}) | occurrences {denoise['pairs_raw']} -> {denoise['pairs_kept']}"
    )
    print(
        f"in-domain pairs={len(domain_pairs)} replay={len(replay)} train={len(train_pairs)} "
        f"valid={len(valid_pairs)}"
    )
    before = evaluate(model, valid_pairs, vocab, args.batch_size, device) if valid_pairs else None
    if before:
        print(f"valid before: cer={before['cer']:.4f} exact={before['exact_match']:.1%}")

    criterion = nn.CrossEntropyLoss(ignore_index=vocab["PAD_ID"], label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    steps_per_epoch = math.ceil(len(train_pairs) / args.batch_size)
    total_steps = steps_per_epoch * args.epochs
    warmup = min(500, max(total_steps // 10, 1))
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lambda step: (
            step / max(warmup, 1)
            if step < warmup
            else 0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * min((step - warmup) / max(total_steps - warmup, 1), 1.0)))
        ),
    )

    best = before["cer"] if before else float("inf")
    history = []
    step = 0
    started = time.perf_counter()
    model.train()
    for epoch in range(1, args.epochs + 1):
        running = 0.0
        seen = 0
        for src, tgt in make_batches(train_pairs, vocab, args.batch_size, True, args.seed + epoch, device):
            memory, src_padding_mask = model.encode(src)
            decoder_input = tgt[:, :-1]
            logits = model.decode_step(
                decoder_input,
                memory,
                src_padding_mask,
                decoder_input == vocab["PAD_ID"],
            )
            loss = criterion(logits.reshape(-1, vocab["VOCAB_SIZE"]), tgt[:, 1:].reshape(-1))
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            running += loss.item() * src.size(0)
            seen += src.size(0)
            step += 1
            if step % 50 == 0:
                rate = seen / max(time.perf_counter() - started, 1e-9)
                print(
                    f"epoch {epoch} step {step}/{total_steps} loss={running / max(seen, 1):.4f} "
                    f"{rate:.0f} pairs/s",
                    flush=True,
                )
            if args.max_steps and step >= args.max_steps:
                break
        if valid_pairs:
            after = evaluate(model, valid_pairs, vocab, args.batch_size, device)
            history.append({"epoch": epoch, "loss": round(running / max(seen, 1), 4), **after})
            print(f"epoch {epoch}: valid cer={after['cer']:.4f} exact={after['exact_match']:.1%}")
            if after["cer"] <= best or args.force_save:
                if after["cer"] <= best:
                    best = after["cer"]
                torch.save(
                    {"model_state": {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                     "phase_name": "domain_finetune",
                     "epoch": epoch,
                     "best_val_cer": best},
                    args.out,
                )
        else:
            torch.save(
                {"model_state": {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                 "phase_name": "domain_finetune",
                 "epoch": epoch,
                 "best_val_cer": None},
                args.out,
            )
        model.train()
        if args.max_steps and step >= args.max_steps:
            break

    meta = {
        "checkpoint_in": str(args.checkpoint),
        "checkpoint_out": str(args.out),
        "device": str(device),
        "epochs": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "min_dominant_share": args.min_dominant_share,
        "denoise": denoise,
        "in_domain_pairs": len(domain_pairs),
        "replay_pairs": len(replay),
        "valid_before": before,
        "valid_after": history[-1] if history else None,
        "history": history,
        "best_val_cer": best,
        "seconds": round(time.perf_counter() - started, 1),
        "steps": step,
    }
    args.meta.parent.mkdir(parents=True, exist_ok=True)
    args.meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "history"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
