"""Kaggle kernel: label the 60 gold songs with two teacher prompts.

Diagnostic for the mood-labeling pipeline: the gold songs were excluded from
the pseudo-label training sample, so the teacher (Qwen2.5-7B-Instruct, 4-bit)
was never measured against human labels. This kernel labels them with

  A) the production prompt from ``sentiment_distill.py`` (as-used), and
  B) a stricter prompt (no forced emotion selection, conservative rule).

Outputs ``teacher_gold_labels.csv`` + ``teacher_gold_report.json``.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LLM_NAME = "Qwen/Qwen2.5-7B-Instruct"
GOLD_SIZE = 60
GOLD_SEED = 42
MAX_NEW_TOKENS = 60
INPUT_ROOT = Path("/kaggle/input")
OUT_DIR = Path("/kaggle/working")

SYSTEM_A = (
    "तपाईं नेपाली गीतका बोल विश्लेषण गर्ने विशेषज्ञ हुनुहुन्छ। "
    "प्रयोगकर्ताले गीतको बोल दिनेछन्। तपाईंले मात्र एक-लाइन JSON फर्काउनुहोस्।"
)
USER_A = (
    "गीतको बोल:\n{lyrics}\n\n"
    "माथिको बोल पढेर: (१) यी पाँच भावनामध्ये कुन-कुन स्पष्ट रूपमा छन्? "
    "(joy=खुशी, sadness=दुःख, anger=रिस, fear=डर, depression=निराशा) — १ देखि ३ वटा छान्नुहोस्, "
    "(२) समग्र sentiment (positive/negative/neutral) भन्नुहोस्।\n"
    'उदाहरण: {{"joy":1,"sadness":0,"anger":0,"fear":0,"depression":0,"sentiment":"positive"}}\n'
    'JSON ढाँचा: {{"joy":0,"sadness":0,"anger":0,"fear":0,"depression":0,"sentiment":"positive|negative|neutral"}}'
)

SYSTEM_B = (
    "तपाईं नेपाली गीतका बोलको भावना विश्लेषण गर्ने सतर्क विशेषज्ञ हुनुहुन्छ। "
    "तपाईंले मात्र एक-लाइन JSON फर्काउनुहोस्।"
)
USER_B = (
    "गीतको बोल:\n{lyrics}\n\n"
    "निर्देशन: तलका पाँच भावनामध्ये प्रत्येकलाई 1 वा 0 दिनुहोस्। "
    "भावना बोलभरि स्पष्ट रूपमा व्यक्त भएको भए मात्र 1 दिनुहोस्; शंका लागे 0 दिनुहोस्। "
    "अधिकांश गीतमा ० देखि २ भावना मात्र हुन्छन्, धेरैलाई 1 नदिनुहोस्।\n"
    "joy=खुशी/आनन्द, sadness=दुःख/पीडा, anger=रिस/आक्रोश, fear=डर/चिन्ता, "
    "depression=गहिरो निराशा (उदासी मात्र होइन)।\n"
    "अनि समग्र sentiment: positive, negative, वा neutral (मिश्रित/तटस्थ भए neutral)।\n"
    'JSON: {{"joy":0,"sadness":0,"anger":0,"fear":0,"depression":0,"sentiment":"positive|negative|neutral"}}'
)

SENTIMENT_MAP = {"positive": (1.0, 0.0), "negative": (0.0, 1.0), "neutral": (0.0, 0.0)}
EMOTIONS = ("joy", "sadness", "anger", "fear", "depression")


def find_cleaned_csv() -> Path:
    named = sorted(INPUT_ROOT.rglob("cleaned_lyrics.csv"))
    if named:
        return max(named, key=lambda p: p.stat().st_size)
    candidates = sorted(INPUT_ROOT.rglob("*.csv"))
    if not candidates:
        raise SystemExit("no CSV found under /kaggle/input")
    return max(candidates, key=lambda p: p.stat().st_size)


def truncate_for_llm(text: str, head: int = 1200, tail: int = 600) -> str:
    text = str(text)
    if len(text) <= head + tail:
        return text
    return text[:head] + "\n...\n" + text[-tail:]


def parse_label_json(raw: str) -> dict | None:
    match = re.search(r"\{.*?\}", raw, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not all(k in data for k in EMOTIONS + ("sentiment",)):
        return None
    sentiment = str(data["sentiment"]).strip().lower()
    if sentiment not in SENTIMENT_MAP:
        return None
    out = {k: 1 if int(data[k]) else 0 for k in EMOTIONS}
    pos, neg = SENTIMENT_MAP[sentiment]
    out["positive"] = int(pos)
    out["negative"] = int(neg)
    out["sentiment"] = sentiment
    return out


def ensure_bitsandbytes() -> None:
    try:
        import bitsandbytes  # noqa: F401
    except Exception:
        print("[check] installing bitsandbytes")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes"], check=False)


def load_llm():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    ensure_bitsandbytes()
    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type="nf4"
    )
    tokenizer = AutoTokenizer.from_pretrained(LLM_NAME)
    model = AutoModelForCausalLM.from_pretrained(LLM_NAME, quantization_config=bnb, device_map="auto")
    model.eval()
    print(f"[check] device: {model.device}")
    return model, tokenizer


def generate_label(model, tokenizer, system: str, user_template: str, lyrics: str) -> tuple[dict | None, str]:
    import torch

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_template.format(lyrics=truncate_for_llm(lyrics))},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        generated = model.generate(
            **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, temperature=None, top_p=None
        )
    answer = tokenizer.decode(generated[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    return parse_label_json(answer), answer.strip()[:300]


def main() -> None:
    df = pd.read_csv(find_cleaned_csv(), encoding="utf-8").fillna("")
    df = df.sort_values("song_id").reset_index(drop=True)
    gold_ids = np.sort(np.random.default_rng(GOLD_SEED).choice(df["song_id"].to_numpy(), size=GOLD_SIZE, replace=False))
    gold = df[df["song_id"].isin(gold_ids)].sort_values("song_id")
    print(f"[check] gold songs: {len(gold)}")

    model, tokenizer = load_llm()
    rows = []
    for count, (_, row) in enumerate(gold.iterrows(), start=1):
        record = {"song_id": int(row["song_id"])}
        for tag, system, template in (("a", SYSTEM_A, USER_A), ("b", SYSTEM_B, USER_B)):
            parsed, raw = generate_label(model, tokenizer, system, template, row["lyrics"])
            record[f"raw_{tag}"] = raw
            record[f"parsed_{tag}"] = int(parsed is not None)
            if parsed:
                for emotion in EMOTIONS:
                    record[f"{tag}_{emotion}"] = parsed[emotion]
                record[f"{tag}_sentiment"] = parsed["sentiment"]
        rows.append(record)
        if count % 10 == 0:
            print(f"[check] labeled {count}/{len(gold)}")

    labels = pd.DataFrame(rows)
    labels.to_csv(OUT_DIR / "teacher_gold_labels.csv", index=False, encoding="utf-8")

    report = {"llm": LLM_NAME, "gold_size": len(gold)}
    for tag in ("a", "b"):
        subset = labels[labels[f"parsed_{tag}"] == 1]
        report[f"variant_{tag}"] = {
            "parsed": int(len(subset)),
            "emotion_rates": {e: round(float(subset[f"{tag}_{e}"].mean()), 3) for e in EMOTIONS},
            "sentiment_distribution": subset[f"{tag}_sentiment"].value_counts().to_dict(),
        }
    (OUT_DIR / "teacher_gold_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
