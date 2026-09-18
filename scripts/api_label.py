"""Label songs with a Gemini model: batched, schema-constrained, resume-safe.

Reads ``GEMINI_API_KEY`` from ``.env`` (or the environment). Sends songs in
batches, requests strict JSON labels (positive/negative binaries + five
emotions + a short Nepali mood phrase), validates every item, and appends to a
JSONL cache so reruns skip already-labeled songs.

Usage:
    python scripts/api_label.py --split gold [--limit N] [--batch-size 30]
    python scripts/api_label.py --split corpus --run-name corpus_v1

Outputs under ``R_data/raw/gemini/<run-name>/``: ``labels.jsonl``,
``labels.csv``, ``api_label_report.json``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"
CLEANED = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
ENV = PROJECT_ROOT / ".env"
EMOTIONS = ("joy", "sadness", "anger", "fear", "depression")
OUT_ROOT = PROJECT_ROOT / "R_data" / "raw" / "gemini"

FEW_SHOT_IDS = (3235, 182, 757, 2252, 3980, 1013, 1860, 3091)

FEW_SHOT_PHRASES = {
    3235: "मायाको उल्लास, शिरदेखि पैतालासम्म",
    182: "टुटेको मायाको पीडा र अविश्वास",
    757: "वर्षाको आनन्द अनि जीवनको क्षणभंगुरता",
    2252: "व्यथासँगैको समर्पित माया",
    3980: "सडक जीवनको संघर्ष र क्रोध",
    1013: "पहिरोको डर र चिन्ता",
    1860: "बिग्रेको जीवनको विषाद र शोक",
    3091: "सतर्क मायाको आशा",
}

SYSTEM = """You are a meticulous annotator of Nepali song lyrics (Devanagari or Romanized Nepali) for an academic music-research database. Analyze the emotional content of each song; this is a literary/linguistic analysis of publicly available lyrics.

For each song produce sentiment polarity, five emotion flags, and a short mood phrase.

Definitions:
- positive / negative: two independent binaries for overall sentiment. Both true = bittersweet/mixed; neither true = neutral.
- joy: overt happiness, celebration, playful enjoyment, or expressed affectionate excitement in the lyrics. Romance, devotion, or affection WITHOUT expressed happiness is not joy.
- sadness: heartbreak, loss, grief, loneliness, separation, regret, longing caused by loss.
- anger: rage, resentment, hostility, accusation, protest, confrontation, defiance — including diss tracks and bitter social criticism.
- fear: threat, danger, anxiety, dread, worry, insecurity.
- depression: ONLY persistent hopelessness, profound emptiness, or loss of meaning; ordinary sadness, loneliness, or darkness stays sadness, never depression.

Rules:
- Label the emotion the song expresses, not merely its topic: romance is not automatically joy; a breakup is not automatically sadness.
- Set multiple emotion flags when several are genuinely present.
- Devotional or patriotic songs: flag joy only when the text expresses celebration or delight.
- If no core emotion dominates, leave all emotion flags false (neutral polarity: both binaries false).
- mood_phrase: one short Nepali phrase (at most 12 words) capturing the emotional core.
- confidence: high, medium, or low.
- Output every song exactly once, echoing its song_id."""

SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "song_id": {"type": "integer"},
            "positive": {"type": "boolean"},
            "negative": {"type": "boolean"},
            "joy": {"type": "boolean"},
            "sadness": {"type": "boolean"},
            "anger": {"type": "boolean"},
            "fear": {"type": "boolean"},
            "depression": {"type": "boolean"},
            "mood_phrase": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
        "required": [
            "song_id", "positive", "negative", "joy", "sadness", "anger",
            "fear", "depression", "mood_phrase", "confidence",
        ],
    },
}


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


def gold_json(row: pd.Series) -> str:
    return json.dumps(
        {
            "song_id": int(row["song_id"]),
            "positive": bool(row["positive"]),
            "negative": bool(row["negative"]),
            "joy": bool(row["joy"]),
            "sadness": bool(row["sadness"]),
            "anger": bool(row["anger"]),
            "fear": bool(row["fear"]),
            "depression": bool(row["depression"]),
            "mood_phrase": str(row["notes"] or ""),
            "confidence": str(row["confidence"] or "medium"),
        },
        ensure_ascii=False,
    )


def few_shot_block(gold: pd.DataFrame, cleaned: pd.DataFrame) -> str:
    lines = ["### Examples (human-reviewed labels)"]
    for sid in FEW_SHOT_IDS:
        sub = gold.loc[gold["song_id"].eq(sid)]
        if sub.empty:
            continue
        row = sub.iloc[0]
        lyr = cleaned.loc[cleaned["song_id"].eq(sid), "lyrics"]
        lines.append(f"<song id={sid}> {row['title']} — {row['artist']}")
        lines.append(str(lyr.iloc[0])[:800] if len(lyr) else "")
        lines.append("</song>")
        payload = json.loads(gold_json(row))
        payload["mood_phrase"] = FEW_SHOT_PHRASES.get(sid, payload["mood_phrase"])
        lines.append(f"output: {json.dumps(payload, ensure_ascii=False)}")
    return "\n".join(lines)


def build_prompt(block: str, batch: list[pd.Series], max_chars: int = 3000) -> str:
    lines = [block, "", "### Songs to label"]
    for row in batch:
        lines.append(f"<song id={int(row['song_id'])}> {row['title']} — {row['artist']}")
        lines.append(str(row["lyrics"])[:max_chars])
        lines.append("</song>")
    lines.append("")
    lines.append(f"Label all {len(batch)} songs above. Reply with ONLY the JSON array.")
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


def normalize(item: dict, expected: set[int]) -> dict | None:
    try:
        sid = int(item["song_id"])
    except (KeyError, TypeError, ValueError):
        return None
    if sid not in expected:
        return None
    out = {"song_id": sid}
    for field in ("positive", "negative", *EMOTIONS):
        out[field] = int(bool(item.get(field, False)))
    out["mood_phrase"] = str(item.get("mood_phrase", ""))[:200]
    conf = str(item.get("confidence", "medium")).lower()
    out["confidence"] = conf if conf in ("high", "medium", "low") else "medium"
    return out


def label_batch(
    client,
    model: str,
    prompt: str,
    expected: set[int],
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
                    temperature=0.15,
                    max_output_tokens=16384,
                ),
            )
            usage = getattr(resp, "usage_metadata", None)
            text = getattr(resp, "text", None) or ""
            parsed = parse_labels(text)
            if parsed is not None:
                items = [x for x in (normalize(it, expected) for it in parsed) if x]
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["gold", "corpus"], default="gold")
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--retry-forever", action="store_true")
    parser.add_argument("--retry-sleep", type=int, default=60)
    parser.add_argument("--sleep-between", type=int, default=0)
    parser.add_argument("--break-on-fail", action="store_true")
    parser.add_argument("--max-lyrics-chars", type=int, default=3000)
    parser.add_argument("--key-var", default="GEMINI_API_KEY")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-total", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--ids-file",
        type=Path,
        default=None,
        help="Optional file of song_ids (one per line, or a CSV with a song_id column) to restrict labeling",
    )
    parser.add_argument("--run-name", default="")
    parser.add_argument("--keep-few-shot", action="store_true")
    args = parser.parse_args()

    gold = pd.read_csv(GOLD, encoding="utf-8")
    cleaned = pd.read_csv(CLEANED, encoding="utf-8").fillna("")
    gold_ids = set(int(x) for x in gold["song_id"])

    if args.split == "gold":
        ids = sorted(gold_ids - (set() if args.keep_few_shot else set(FEW_SHOT_IDS)))
        subset = cleaned[cleaned["song_id"].isin(ids)].copy()
    else:
        ids = sorted(set(int(x) for x in cleaned["song_id"]) - gold_ids)
        subset = cleaned[cleaned["song_id"].isin(ids)].copy()

    subset = subset.sort_values("song_id").reset_index(drop=True)
    if args.ids_file:
        wanted: set[int] = set()
        text = args.ids_file.read_text(encoding="utf-8")
        if args.ids_file.suffix.lower() == ".csv":
            wanted = {int(value) for value in pd.read_csv(args.ids_file)["song_id"]}
        else:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                wanted.add(int(line.split(",")[0]))
        subset = subset[subset["song_id"].isin(wanted)].reset_index(drop=True)
    if args.shard_total > 1:
        subset = subset.iloc[args.shard_index :: args.shard_total].reset_index(drop=True)
    if args.limit:
        subset = subset.head(args.limit)

    run_name = args.run_name or f"{args.split}_v1"
    out_dir = OUT_ROOT / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "labels.jsonl"

    done: dict[int, dict] = {}
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                done[int(rec["song_id"])] = rec
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    todo = [row for _, row in subset.iterrows() if int(row["song_id"]) not in done]
    print(f"split={args.split} model={args.model} total={len(subset)} done={len(done)} todo={len(todo)}")

    if not todo:
        print("nothing to do")
    else:
        key = load_key(args.key_var)
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=180_000),
        )
        block = few_shot_block(gold, cleaned)

        n_batches = math.ceil(len(todo) / args.batch_size)
        tokens_in = tokens_out = 0
        errors = []
        with jsonl_path.open("a", encoding="utf-8") as fh:
            for i in range(n_batches):
                batch = todo[i * args.batch_size : (i + 1) * args.batch_size]
                expected = {int(r["song_id"]) for r in batch}
                prompt = build_prompt(block, batch, args.max_lyrics_chars)
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
                    print(f"batch {i + 1}/{n_batches}: FAILED ({err})", flush=True)
                    errors.append({"batch": i + 1, "error": err, "ids": sorted(expected)})
                    if err.startswith("PERMANENT"):
                        break
                    if args.break_on_fail:
                        break
                    continue
                for rec in items:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    done[rec["song_id"]] = rec
                fh.flush()
                ti = getattr(usage, "prompt_token_count", 0) or 0
                to = getattr(usage, "candidates_token_count", 0) or 0
                tokens_in += ti
                tokens_out += to
                print(f"batch {i + 1}/{n_batches}: labeled {len(items)} (in {ti} / out {to} tokens)", flush=True)
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
        print(json.dumps({k: v for k, v in report.items() if k != "errors"}, indent=1))

    all_recs: dict[int, dict] = {}
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                all_recs[int(rec["song_id"])] = rec
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    if all_recs:
        out = pd.DataFrame([all_recs[k] for k in sorted(all_recs)])
        cols = ["song_id", "positive", "negative", *EMOTIONS, "mood_phrase", "confidence"]
        out = out[cols]
        out.to_csv(out_dir / "labels.csv", index=False, encoding="utf-8")
        print(f"csv -> {out_dir / 'labels.csv'} ({len(out)} rows)")


if __name__ == "__main__":
    main()
