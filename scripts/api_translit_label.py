"""Label Romanized Nepali lines with a Gemini teacher: batched, resume-safe.

Reads ``GEMINI_API_KEY`` from ``.env`` (or the environment), sends lines in
batches, requests strict JSON (Devanagari line + confidence), validates every
item, and appends to a JSONL cache so reruns skip already-labeled lines.

Splits:
- ``gold``: the committed line gold (``eval/translit_gold_lines.csv``) — the
  teacher sanity check (A1 gate). Few-shot examples are hand-written, so the
  measurement is not contaminated by the gold.
- ``corpus``: deterministic sample of cleaned romanized corpus lines
  (``R_data/corpus/corpus_raw.csv``), for in-domain fine-tuning data.

Outputs under ``R_data/raw/gemini/<run-name>/``: ``labels.jsonl``,
``labels.csv``, ``api_label_report.json``.

Usage:
    python scripts/api_translit_label.py --split gold --run-name translit_gold_v1
    python scripts/api_translit_label.py --split corpus --run-name translit_corpus_v1 --sample 2000
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lyrics_pipeline.cleaner import clean_lyrics_body  # noqa: E402

GOLD_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
CORPUS_RAW = PROJECT_ROOT / "R_data" / "corpus" / "corpus_raw.csv"
ENV = PROJECT_ROOT / ".env"
OUT_ROOT = PROJECT_ROOT / "R_data" / "raw" / "gemini"

SYSTEM = """You are a meticulous annotator of Nepali song lyrics for an academic music-research database. Your task is to convert Romanized Nepali lines into standard Devanagari. This is a linguistic annotation task on publicly available lyrics.

Rules:
- Write standard Nepali orthography as used in Devanagari song lyrics.
- The verb "cha"/"chha"/"chh" is छ: huncha -> हुन्छ, garchu -> गर्छु, chau -> छौ, lauchau -> लाउँछौं.
- "bh" is भ, "v" before a vowel is भ in song spelling (vana -> भन, vanne -> भन्ने), plain "b" is ब (bata -> बाट).
- Keep English words in Latin script: never transliterate English into Devanagari.
- Preserve token boundaries: one Roman token becomes exactly one Devanagari token. Do not merge or split words.
- Copy punctuation, parentheses and dashes unchanged; do not introduce danda and do not change spacing.
- Use chandrabindu and anusvara as standard: kaha -> कहाँ, kahi -> कहीँ, sanga -> सँग, chhau -> छौ, huncha -> हुन्छ.
- Names use conventional Devanagari spelling.
- If a line is fully English, return it unchanged.
- confidence: high, medium, or low.
- Output every line exactly once, echoing its line_id."""

SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "line_id": {"type": "string"},
            "devanagari": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
        "required": ["line_id", "devanagari", "confidence"],
    },
}

# Hand-written examples (policy: eval/translit_policy.md). Deliberately not
# taken from the gold set so the gold measurement stays clean.
FEW_SHOT = [
    ("huncha ki nai hunna", "हुन्छ कि नै हुन्न"),
    ("ma timilai maya garchu", "म तिमीलाई माया गर्छु"),
    ("kaha janchau bhana na", "कहाँ जान्छौ भन न"),
    ("mero kura vana", "मेरो कुरा भन"),
    ("yo katha aaja prastut gardai", "यो कथा आज प्रस्तुत गर्दै"),
    ("I love you bhanne geet", "I love you भन्ने गीत"),
    ("sanga bina kahile", "सँग बिना कहिले"),
]

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
ROMAN_WORD_RE = re.compile(r"[A-Za-z]{2,}")


def load_key(var_name: str = "GEMINI_API_KEY") -> str:
    key = None
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(var_name + "="):
                key = line.split("=", 1)[1].strip()
    if not key:
        key = os.environ.get(var_name) or os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit(f"no {var_name} in .env or environment")
    return key


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


def load_gold_lines() -> list[dict]:
    with open(GOLD_LINES, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sample_corpus_lines(sample: int, seed: int = 42, mode: str = "coverage") -> list[dict]:
    """Deterministic, deduplicated romanized lines; IDs stable across runs.

    ``mode="coverage"`` greedily prefers lines that carry roman tokens not yet
    covered by earlier picks (weighted by corpus token frequency), so a small
    teacher budget buys lexicon coverage over the real vocabulary rather than a
    plain random slice. ``mode="random"`` is a seeded uniform sample.
    """
    gold = {normalize(row["roman"]) for row in load_gold_lines()}
    seen: set[str] = set()
    candidates: list[dict] = []
    with open(CORPUS_RAW, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("script") != "romanized":
                continue
            text, _ = clean_lyrics_body(
                row.get("Lyrics") or "", row.get("Title") or "", row.get("Artist") or ""
            )
            for line in text.splitlines():
                line = normalize(line)
                if len(ROMAN_WORD_RE.findall(line)) < 2 or line in seen or line in gold:
                    continue
                seen.add(line)
                candidates.append(
                    {
                        "line_id": "c_" + hashlib.sha1(line.encode("utf-8")).hexdigest()[:12],
                        "roman": line,
                        "source": row.get("source", ""),
                        "tokens": sorted({token.lower() for token in re.findall(r"[A-Za-z]+", line)}),
                    }
                )

    import random

    if mode == "random":
        rng = random.Random(seed)
        selected = rng.sample(candidates, min(sample, len(candidates)))
    else:
        # Lazy-greedy weighted set cover: pick the line with the largest
        # uncovered token-frequency mass, re-scoring stale heap entries as the
        # covered set grows (submodularity makes this near-optimal).
        import heapq

        frequency: dict[str, int] = {}
        for row in candidates:
            for token in row["tokens"]:
                frequency[token] = frequency.get(token, 0) + 1
        rng = random.Random(seed)
        heap = []
        for index, row in enumerate(candidates):
            score = sum(frequency[token] for token in row["tokens"])
            heap.append((-score, rng.random(), index))
        heapq.heapify(heap)
        covered: set[str] = set()
        selected: list[dict] = []
        chosen: set[int] = set()
        while heap and len(selected) < sample:
            _, tie, index = heapq.heappop(heap)
            row = candidates[index]
            gain = sum(frequency[token] for token in row["tokens"] if token not in covered)
            if gain <= 0:
                continue
            if heap and gain < -heap[0][0]:
                heapq.heappush(heap, (-gain, tie, index))
                continue
            selected.append(row)
            chosen.add(index)
            covered.update(row["tokens"])
        if len(selected) < sample:
            pool = [index for index in range(len(candidates)) if index not in chosen]
            for index in rng.sample(pool, min(sample - len(selected), len(pool))):
                selected.append(candidates[index])
    selected.sort(key=lambda row: row["line_id"])
    return selected


def few_shot_block() -> str:
    lines = ["### Examples (policy-consistent)"]
    for roman, devanagari in FEW_SHOT:
        lines.append(f"<line id=x>{roman}</line>")
        lines.append(f"output: {json.dumps({'line_id': 'x', 'devanagari': devanagari, 'confidence': 'high'}, ensure_ascii=False)}")
    return "\n".join(lines)


def build_prompt(block: str, batch: list[dict]) -> str:
    lines = [block, "", "### Lines to transliterate"]
    for row in batch:
        lines.append(f"<line id={row['line_id']}>{row['roman']}</line>")
    lines.append("")
    lines.append(f"Transliterate all {len(batch)} lines above. Reply with ONLY the JSON array.")
    return "\n".join(lines)


def parse_labels(raw: str) -> list[dict] | None:
    text = (raw or "").strip()
    for candidate in (text, re.search(r"\[.*\]", text, re.DOTALL)):
        if candidate is None:
            continue
        if not isinstance(candidate, str):
            candidate = candidate.group(0)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list) and data:
            return data
    return None


def normalize_item(item: dict, expected: set[str]) -> dict | None:
    line_id = str(item.get("line_id", "")).strip()
    if line_id not in expected:
        return None
    devanagari = normalize(item.get("devanagari", ""))
    if not devanagari or "\ufffd" in devanagari:
        return None
    conf = str(item.get("confidence", "medium")).lower()
    return {
        "line_id": line_id,
        "devanagari": devanagari,
        "confidence": conf if conf in ("high", "medium", "low") else "medium",
    }


def label_batch(
    client,
    model: str,
    prompt: str,
    expected: set[str],
    attempts: int = 3,
    retry_forever: bool = False,
    retry_sleep: int = 60,
):
    last_err = None
    attempt = 0
    while True:
        try:
            from google.genai import types

            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json",
                    response_schema=SCHEMA,
                    temperature=0.1,
                    max_output_tokens=32768,
                ),
            )
            usage = getattr(resp, "usage_metadata", None)
            text = getattr(resp, "text", None) or ""
            parsed = parse_labels(text)
            if parsed is not None:
                items = [x for x in (normalize_item(it, expected) for it in parsed) if x]
                if len(items) == len(expected):
                    return items, usage, None
                last_err = f"incomplete: {len(items)}/{len(expected)}"
            else:
                finish = None
                block = None
                try:
                    finish = resp.candidates[0].finish_reason
                except Exception:  # noqa: BLE001
                    pass
                try:
                    block = resp.prompt_feedback.block_reason
                except Exception:  # noqa: BLE001
                    pass
                last_err = f"unparseable (finish={finish}, block={block}, head={text[:150]!r})"
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {str(exc)[:200]}"
            if "403" in last_err or "404" in last_err:
                return [], None, f"PERMANENT {last_err}"

        attempt += 1
        if retry_forever:
            print(f"    retry in {retry_sleep}s ({last_err[:90]})", flush=True)
            time.sleep(retry_sleep)
            continue
        if attempt >= attempts:
            return [], None, last_err
        time.sleep(5 * attempt)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["gold", "corpus"], default="gold")
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--batch-size", type=int, default=80)
    parser.add_argument("--sample", type=int, default=2000, help="corpus split: lines to sample")
    parser.add_argument("--sample-mode", choices=["coverage", "random"], default="coverage")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--retry-forever", action="store_true")
    parser.add_argument("--retry-sleep", type=int, default=60)
    parser.add_argument("--sleep-between", type=int, default=0)
    parser.add_argument("--break-on-fail", action="store_true")
    parser.add_argument("--key-var", default="GEMINI_API_KEY")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-total", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-name", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.split == "gold":
        subset = [
            {"line_id": row["line_id"], "roman": row["roman"], "source": row["source"]}
            for row in load_gold_lines()
        ]
    else:
        subset = sample_corpus_lines(args.sample, args.seed, args.sample_mode)
    if args.shard_total > 1:
        subset = subset[args.shard_index :: args.shard_total]
    if args.limit:
        subset = subset[: args.limit]

    run_name = args.run_name or f"translit_{args.split}_v1"
    out_dir = OUT_ROOT / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "labels.jsonl"

    done: dict[str, dict] = {}
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                done[str(record["line_id"])] = record
            except (json.JSONDecodeError, KeyError):
                continue

    todo = [row for row in subset if row["line_id"] not in done]
    print(f"split={args.split} model={args.model} total={len(subset)} done={len(done)} todo={len(todo)}")

    if todo:
        key = load_key(args.key_var)
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=180_000))
        block = few_shot_block()
        by_id = {row["line_id"]: row for row in subset}

        n_batches = math.ceil(len(todo) / args.batch_size)
        tokens_in = tokens_out = 0
        errors = []
        with jsonl_path.open("a", encoding="utf-8") as handle:
            for index in range(n_batches):
                batch = todo[index * args.batch_size : (index + 1) * args.batch_size]
                expected = {row["line_id"] for row in batch}
                prompt = build_prompt(block, batch)
                items, usage, err = label_batch(
                    client,
                    args.model,
                    prompt,
                    expected,
                    attempts=args.attempts,
                    retry_forever=args.retry_forever,
                    retry_sleep=args.retry_sleep,
                )
                if not items and err:
                    print(f"batch {index + 1}/{n_batches}: FAILED ({err})", flush=True)
                    errors.append({"batch": index + 1, "error": err, "ids": sorted(expected)})
                    if err.startswith("PERMANENT") or args.break_on_fail:
                        break
                    continue
                for record in items:
                    record["roman"] = by_id[record["line_id"]]["roman"]
                    record["source"] = by_id[record["line_id"]]["source"]
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    done[record["line_id"]] = record
                handle.flush()
                ti = getattr(usage, "prompt_token_count", 0) or 0
                to = getattr(usage, "candidates_token_count", 0) or 0
                tokens_in += ti
                tokens_out += to
                print(
                    f"batch {index + 1}/{n_batches}: labeled {len(items)} "
                    f"(in {ti} / out {to} tokens)",
                    flush=True,
                )
                if args.sleep_between:
                    time.sleep(args.sleep_between)

        report = {
            "split": args.split,
            "model": args.model,
            "run_name": run_name,
            "batch_size": args.batch_size,
            "total": len(subset),
            "labeled": len(done),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "errors": errors,
        }
        (out_dir / "api_label_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps({key: value for key, value in report.items() if key != "errors"}, indent=1))

    records: dict[str, dict] = {}
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                records[str(record["line_id"])] = record
            except (json.JSONDecodeError, KeyError):
                continue
    if records:
        rows = [records[key] for key in sorted(records)]
        with open(out_dir / "labels.csv", "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["line_id", "roman", "devanagari", "confidence", "source"]
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"csv -> {out_dir / 'labels.csv'} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
