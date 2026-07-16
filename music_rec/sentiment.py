"""Train/infer muRIL mood scores for lyrics (score = P(pos) - P(neg))."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import Config


def _tail_truncate(text: str, tokenizer, max_len: int):
    """Tokenize and keep the LAST max_len-2 tokens, re-adding special tokens."""
    ids = tokenizer.encode(text, add_special_tokens=False)
    if len(ids) > max_len - 2:
        ids = ids[-(max_len - 2):]
    return tokenizer.prepare_for_model(
        ids, max_length=max_len, truncation=True, padding="max_length"
    )


def load_nepali_sentiment():
    """Load Shushant/NepaliSentiment with a couple of fallbacks."""
    from datasets import load_dataset

    candidates = ["Shushant/NepaliSentiment", "Shushant/nepali_sentiment"]
    last_err = None
    for name in candidates:
        try:
            return load_dataset(name)
        except Exception as e:  # pragma: no cover - network dependent
            last_err = e
    raise RuntimeError(f"Could not load NepaliSentiment dataset: {last_err}")


def train_classifier(config: Config | None = None) -> str:
    config = config or Config()
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
    )

    ds = load_nepali_sentiment()
    tokenizer = AutoTokenizer.from_pretrained(config.sentiment_base_model)

    split = ds["train"] if "train" in ds else ds[list(ds.keys())[0]]
    cols = split.column_names
    text_col = next((c for c in ("text", "sentence", "Sentences", "data") if c in cols), cols[0])
    label_col = next(
        (c for c in ("label", "labels", "Sentiment", "sentiment") if c in cols), cols[-1]
    )

    RAW_TO_NAME = {"0": "negative", "1": "neutral", "2": "positive"}
    label2id = {"negative": 0, "neutral": 1, "positive": 2}
    num_labels = 3

    def _valid(example):
        return str(example[label_col]) in RAW_TO_NAME

    ds = ds.filter(_valid)

    def preprocess(batch):
        enc = tokenizer(
            [str(t) for t in batch[text_col]],
            truncation=True,
            max_length=config.sentiment_max_len,
            padding=False,
        )
        enc["labels"] = [label2id[RAW_TO_NAME[str(l)]] for l in batch[label_col]]
        return enc

    tokenized = {k: v.map(preprocess, batched=True, remove_columns=v.column_names) for k, v in ds.items()}
    train_split = tokenized["train"] if "train" in tokenized else list(tokenized.values())[0]
    eval_split = tokenized.get("validation") or tokenized.get("test")

    model = AutoModelForSequenceClassification.from_pretrained(
        config.sentiment_base_model,
        num_labels=num_labels,
        id2label={i: l for l, i in label2id.items()},
        label2id=label2id,
    )

    args = TrainingArguments(
        output_dir=str(config.sentiment_model_dir / "checkpoints"),
        num_train_epochs=config.sentiment_epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        learning_rate=2e-5,
        weight_decay=0.01,
        logging_steps=50,
        save_strategy="no",
        report_to=[],
        use_cpu=not torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_split,
        eval_dataset=eval_split,
        data_collator=DataCollatorWithPadding(tokenizer),
    )
    trainer.train()

    config.sentiment_model_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(config.sentiment_model_dir)
    tokenizer.save_pretrained(config.sentiment_model_dir)
    (config.sentiment_model_dir / "label_map.json").write_text(
        json.dumps(label2id, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[sentiment] model saved -> {config.sentiment_model_dir}")
    return str(config.sentiment_model_dir)


def infer_sentiment(config: Config | None = None, batch_size: int = 16) -> pd.DataFrame:
    config = config or Config()
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(config.sentiment_model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(config.sentiment_model_dir)
    model.eval()

    label2id = json.loads((config.sentiment_model_dir / "label_map.json").read_text(encoding="utf-8"))
    id2label = {v: k for k, v in label2id.items()}

    def label_polarity(name: str) -> int:
        n = name.lower()
        if any(t in n for t in ("pos", "1", "happy")):
            return 1
        if any(t in n for t in ("neg", "0", "sad")):
            return -1
        return 0

    df = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8")
    texts = df["lyrics"].fillna("").astype(str).tolist()

    scores: list[float] = []
    labels: list[str] = []
    max_len = config.sentiment_max_len

    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            # Tail truncation: keep the END of each lyric.
            enc_ids = []
            for t in batch:
                ids = tokenizer.encode(t, add_special_tokens=True)
                if len(ids) > max_len:
                    ids = [ids[0]] + ids[-(max_len - 1):]
                enc_ids.append(ids)
            maxb = max(len(x) for x in enc_ids)
            pad_id = tokenizer.pad_token_id or 0
            input_ids = torch.tensor([x + [pad_id] * (maxb - len(x)) for x in enc_ids])
            attn = torch.tensor([[1] * len(x) + [0] * (maxb - len(x)) for x in enc_ids])

            logits = model(input_ids=input_ids, attention_mask=attn).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()

            for row in probs:
                pos = sum(row[i] for i in range(len(row)) if label_polarity(id2label[i]) == 1)
                neg = sum(row[i] for i in range(len(row)) if label_polarity(id2label[i]) == -1)
                scores.append(float(pos - neg))
                labels.append(id2label[int(row.argmax())])
            print(f"[sentiment-infer] {min(start + batch_size, len(texts))}/{len(texts)}")

    out = pd.DataFrame(
        {"song_id": df["song_id"], "sentiment_label": labels, "sentiment_score": scores}
    )
    out.to_csv(config.sentiment_scores_csv, index=False, encoding="utf-8")
    print(f"[sentiment] scores saved -> {config.sentiment_scores_csv}")
    return out


if __name__ == "__main__":
    train_classifier()
    infer_sentiment()
