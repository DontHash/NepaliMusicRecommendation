"""Kaggle kernel: song-domain sentiment via LLM pseudo-label distillation.

Stage 1: Qwen2.5-7B-Instruct (4-bit) labels a sample of songs with five binary
emotions (joy, sadness, anger, fear, depression) and a three-class sentiment.
Stage 2: muRIL-base is fine-tuned multi-label on those pseudo-labels (7 sigmoid
outputs incl. positive/negative) and then infers every song.

Input: cleaned_lyrics.csv attached as a Kaggle dataset. Outputs to /kaggle/working:
mood_pseudo_labels.csv, sentiment_scores_v2.csv, sentiment_distill_report.json.
"""

from __future__ import annotations

import gc
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LLM_NAME = "Qwen/Qwen2.5-7B-Instruct"
MU_RIL = "google/muril-base-cased"
LABELS = ("joy", "sadness", "anger", "fear", "depression", "positive", "negative")
SENTIMENT_MAP = {"positive": (1.0, 0.0), "negative": (0.0, 1.0), "neutral": (0.0, 0.0)}
N_PSEUDO = 2000
GOLD_SIZE = 60
GOLD_SEED = 42
SAMPLE_SEED = 7
MAX_NEW_TOKENS = 60
TRAIN_MAX_LEN = 256
TRAIN_EPOCHS = 2
TRAIN_BATCH = 8
TRAIN_LR = 2e-5
INFER_BATCH = 32
CHECKPOINT_EVERY = 200
INPUT_ROOT = Path("/kaggle/input")
OUT_DIR = Path("/kaggle/working")

SYSTEM_PROMPT = (
    "तपाईं नेपाली गीतका बोल विश्लेषण गर्ने विशेषज्ञ हुनुहुन्छ। "
    "प्रयोगकर्ताले गीतको बोल दिनेछन्। तपाईंले मात्र JSON फर्काउनुहोस्।"
)
USER_TEMPLATE = (
    "गीतको बोल:\n{lyrics}\n\n"
    "माथिको बोलमा तलका भावनाहरू छन्/छैनन् (1=छ, 0=छैन) र समग्र sentiment के हो? "
    'JSON ढाँचा: {{"joy":0,"sadness":0,"anger":0,"fear":0,"depression":0,"sentiment":"positive|negative|neutral"}}'
)


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
    if not all(k in data for k in ("joy", "sadness", "anger", "fear", "depression", "sentiment")):
        return None
    sentiment = str(data["sentiment"]).strip().lower()
    if sentiment not in SENTIMENT_MAP:
        return None
    out = {k: 1 if int(data[k]) else 0 for k in ("joy", "sadness", "anger", "fear", "depression")}
    pos, neg = SENTIMENT_MAP[sentiment]
    out["positive"] = int(pos)
    out["negative"] = int(neg)
    out["sentiment"] = sentiment
    return out


def load_llm():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    def _load(name: str):
        tokenizer = AutoTokenizer.from_pretrained(name)
        model = AutoModelForCausalLM.from_pretrained(
            name, quantization_config=bnb_config, device_map="auto"
        )
        model.eval()
        return model, tokenizer

    try:
        from transformers import BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
        print(f"[distill] loading {LLM_NAME} in 4-bit")
        return *_load(LLM_NAME), LLM_NAME
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"[distill] 4-bit load failed ({exc}); falling back to Qwen2.5-3B fp16")
        fallback = "Qwen/Qwen2.5-3B-Instruct"
        tokenizer = AutoTokenizer.from_pretrained(fallback)
        model = AutoModelForCausalLM.from_pretrained(fallback, torch_dtype=torch.float16, device_map="auto")
        model.eval()
        return model, tokenizer, fallback


def label_songs(model, tokenizer, df: pd.DataFrame, label_ids: np.ndarray) -> pd.DataFrame:
    import torch

    rows = []
    done_ids: set[int] = set()
    checkpoint = OUT_DIR / "mood_pseudo_labels.csv"
    subset = df[df["song_id"].isin(label_ids)].sort_values("song_id")
    for count, (_, row) in enumerate(subset.iterrows(), start=1):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(lyrics=truncate_for_llm(row["lyrics"]))},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, temperature=None, top_p=None
            )
        answer = tokenizer.decode(generated[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
        parsed = parse_label_json(answer)
        if parsed is None:
            strict = messages + [{"role": "user", "content": "फेरि प्रयास: मात्र JSON लेख्नुहोस्।"}]
            prompt = tokenizer.apply_chat_template(strict, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                generated = model.generate(
                    **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, temperature=None, top_p=None
                )
            answer = tokenizer.decode(generated[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
            parsed = parse_label_json(answer)
        if parsed is None:
            continue
        parsed["song_id"] = int(row["song_id"])
        rows.append(parsed)
        done_ids.add(int(row["song_id"]))
        if count % 50 == 0:
            print(f"[distill] labeled {count}/{len(subset)}")
        if count % CHECKPOINT_EVERY == 0:
            pd.DataFrame(rows).to_csv(checkpoint, index=False, encoding="utf-8")
            print(f"[distill] checkpoint saved ({len(rows)} labels)")

    labeled = pd.DataFrame(rows)
    labeled.to_csv(checkpoint, index=False, encoding="utf-8")
    print(f"[distill] labeling done: {len(labeled)}/{len(subset)} parsed")
    return labeled


class LyricsMoodDataset:
    def __init__(self, texts, labels, tokenizer, max_len=TRAIN_MAX_LEN):
        import torch

        self.items = []
        for text, label in zip(texts, labels):
            ids = tokenizer.encode(str(text), add_special_tokens=True)
            if len(ids) > max_len:
                ids = [ids[0]] + ids[-(max_len - 1) :]
            self.items.append((ids, label, torch.tensor(label, dtype=torch.float)))
        self.pad_token_id = tokenizer.pad_token_id or 0

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        ids, _, label_tensor = self.items[index]
        return {"input_ids": ids, "labels": label_tensor}

    def collate(self, features):
        import torch

        width = max(len(f["input_ids"]) for f in features)
        input_ids = torch.full((len(features), width), self.pad_token_id, dtype=torch.long)
        attention = torch.zeros((len(features), width), dtype=torch.long)
        for row, feature in enumerate(features):
            length = len(feature["input_ids"])
            input_ids[row, :length] = torch.tensor(feature["input_ids"], dtype=torch.long)
            attention[row, :length] = 1
        labels = torch.stack([f["labels"] for f in features])
        return {"input_ids": input_ids, "attention_mask": attention, "labels": labels}


def train_muril(df: pd.DataFrame, labeled: pd.DataFrame):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

    merged = df.merge(labeled, on="song_id", how="inner")
    split = int(len(merged) * 0.9)
    train_df = merged.iloc[:split]
    eval_df = merged.iloc[split:]
    print(f"[distill] training muRIL on {len(train_df)} songs (eval {len(eval_df)})")

    tokenizer = AutoTokenizer.from_pretrained(MU_RIL)
    model = AutoModelForSequenceClassification.from_pretrained(
        MU_RIL,
        num_labels=len(LABELS),
        problem_type="multi_label_classification",
        id2label={i: name for i, name in enumerate(LABELS)},
        label2id={name: i for i, name in enumerate(LABELS)},
    )

    label_cols = list(LABELS)
    train_ds = LyricsMoodDataset(train_df["lyrics"].tolist(), train_df[label_cols].to_numpy(), tokenizer)
    eval_ds = LyricsMoodDataset(eval_df["lyrics"].tolist(), eval_df[label_cols].to_numpy(), tokenizer)

    base_args = dict(
        output_dir=str(OUT_DIR / "muril_ckpt"),
        num_train_epochs=TRAIN_EPOCHS,
        per_device_train_batch_size=TRAIN_BATCH,
        per_device_eval_batch_size=16,
        learning_rate=TRAIN_LR,
        weight_decay=0.01,
        logging_steps=50,
        save_strategy="no",
        report_to=[],
        fp16=torch.cuda.is_available(),
    )
    try:
        args = TrainingArguments(eval_strategy="epoch", **base_args)
    except TypeError:
        args = TrainingArguments(evaluation_strategy="epoch", **base_args)
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=train_ds.collate,
    )
    trainer.train()
    metrics = trainer.evaluate()
    return model, tokenizer, {k: float(v) for k, v in metrics.items()}


def infer_all(model, tokenizer, df: pd.DataFrame) -> pd.DataFrame:
    import torch

    texts = df["lyrics"].fillna("").astype(str).tolist()
    probs: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(texts), INFER_BATCH):
            batch = texts[start : start + INFER_BATCH]
            enc_ids = []
            for text in batch:
                ids = tokenizer.encode(text, add_special_tokens=True)
                if len(ids) > TRAIN_MAX_LEN:
                    ids = [ids[0]] + ids[-(TRAIN_MAX_LEN - 1) :]
                enc_ids.append(ids)
            width = max(len(x) for x in enc_ids)
            pad_id = tokenizer.pad_token_id or 0
            input_ids = torch.tensor([x + [pad_id] * (width - len(x)) for x in enc_ids], device=model.device)
            attn = torch.tensor(
                [[1] * len(x) + [0] * (width - len(x)) for x in enc_ids], device=model.device
            )
            logits = model(input_ids=input_ids, attention_mask=attn).logits
            probs.append(torch.sigmoid(logits).cpu().numpy())
            done = min(start + INFER_BATCH, len(texts))
            if done % 500 < INFER_BATCH or done == len(texts):
                print(f"[distill] inferred {done}/{len(texts)}")
    prob_matrix = np.vstack(probs)
    out = pd.DataFrame({"song_id": df["song_id"].to_numpy()})
    for i, name in enumerate(LABELS):
        out[name] = prob_matrix[:, i]
    scores = out["positive"] - out["negative"]
    out["sentiment_score"] = scores
    out["sentiment_label"] = np.where(scores > 0.15, "positive", np.where(scores < -0.15, "negative", "neutral"))
    return out


def main() -> None:
    df = pd.read_csv(find_cleaned_csv(), encoding="utf-8").fillna("")
    df = df.sort_values("song_id").reset_index(drop=True)
    all_ids = df["song_id"].to_numpy()

    gold_ids = np.sort(np.random.default_rng(GOLD_SEED).choice(all_ids, size=GOLD_SIZE, replace=False))
    eligible = np.setdiff1d(all_ids, gold_ids)
    label_ids = np.sort(
        np.random.default_rng(SAMPLE_SEED).choice(eligible, size=min(N_PSEUDO, len(eligible)), replace=False)
    )
    print(f"[distill] songs: {len(df)} | gold excluded: {len(gold_ids)} | pseudo-labeled: {len(label_ids)}")
    (OUT_DIR / "gold_ids.json").write_text(json.dumps([int(x) for x in gold_ids]), encoding="utf-8")

    llm, tokenizer, llm_name = load_llm()
    labeled = label_songs(llm, tokenizer, df, label_ids)
    del llm
    gc.collect()
    try:
        import torch

        torch.cuda.empty_cache()
    except Exception:
        pass

    model, muril_tokenizer, train_metrics = train_muril(df, labeled)
    scores = infer_all(model, muril_tokenizer, df)
    scores.to_csv(OUT_DIR / "sentiment_scores_v2.csv", index=False, encoding="utf-8")

    report = {
        "llm": llm_name,
        "songs": int(len(df)),
        "pseudo_labeled": int(len(labeled)),
        "gold_excluded": int(len(gold_ids)),
        "train_metrics": train_metrics,
        "pseudo_label_distribution": {
            name: int(labeled[name].sum()) for name in LABELS
        },
        "sentiment_distribution": scores["sentiment_label"].value_counts().to_dict(),
        "score_mean": float(scores["sentiment_score"].mean()),
    }
    (OUT_DIR / "sentiment_distill_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
