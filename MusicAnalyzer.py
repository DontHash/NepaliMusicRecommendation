"""Analyze Nepali lyrics: mood (linear probe), keywords, category. Edit LYRICS below or use CLI."""

from __future__ import annotations

# Edit LYRICS, then: python MusicAnalyzer.py
LYRICS = """
लाखौं हजारौं मध्ये तिम्रो मुस्कानले
किन हो मलाई पागल बनाउँछ?
लाखौं प्रयास गर्दा पनि
किन हो मलाई तिम्रै यादले सताउछ?
माया के हो भनेर
तिम्रै वरिपरि रहँदा यो मनले थाहा पाउँछ
आज भोलि, सुन्दा तिम्रो बोली
यो मुटु असाध्यै रमाउँछ
घामलाई हेरी बस्छु, बादलमा नी तिमी देख्छु
तिमी बिना कसरी बिताउने होला जिन्दगी?
ढाटेको केही छैन, तिम्रो लागि मेरो माया—
कति रैछ हेरिदेउन, यो सानो मुटुमा
चन्द्रमा र तारागण सामु, सारा संसार सामु
देखाइदिन्छु कति माया गर्छु तिमीलाई
भन्नेले भन्नेछन्, माया, मात्र तिमी पाए बालै छैन अरू कोहीको
सातौं जुनी भरि तिम्रै मुहार हेरी
तिम्रै हात समाई जीवन बिताउला
भनन मात्र तिमी, माया
सारा संसार तिम्रै हातमा थमाइदिउला
बादलहरु हेरी, तिम्रै गीत कोरी
आँखाहरू बन्द गरी मुस्कुराउँछु म
हिजो आज, सुन्दा त्यो आवाज
यो मुटु असाध्यै रमाउँछ
घामलाई हेरी बस्छु, बादलमा नी तिमी देख्छु
तिमी बिना कसरी बिताउने होला जिन्दगी?
ढाटेको केही छैन, तिम्रो लागि मेरो माया—
कति रैछ हेरिदेउन, यो सानो मुटुमा
चन्द्रमा र तारागण सामु, सारा संसार सामु
देखाइदिन्छु कति माया गर्छु तिमीलाई
भन्नेले भन्नेछन्, माया, मात्र तिमी पाए बालै छैन अरू कोहीको
लाखौं हजारौं मध्ये तिम्रै मुस्कानले
किन हो मलाई पागल बनाउँछ?
"""

TOP_KEYWORDS = 10
OUTPUT_AS_JSON = False
USE_TRANSLITERATION = True

import argparse
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from music_rec.config import Config
from music_rec.tokenization import normalize_nfc, tokenize

_ROMAN_RE = re.compile(r"[A-Za-z]")
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

NEPALI_STOPWORDS = {
    "र", "मा", "को", "का", "की", "हो", "छ", "छु", "छौ", "छन", "छन्", "थियो", "हुन",
    "हुन्", "भयो", "गर", "गरे", "गर्छ", "गर्छु", "म", "मेरो", "मलाई", "मेरा", "हामी",
    "हाम्रो", "तिमी", "तिम्रो", "तिमिलाई", "तिमीलाई", "तँ", "उ", "ऊ", "उनी", "उसको",
    "यो", "त्यो", "यी", "ती", "यस", "त्यस", "के", "को", "कुन", "कहाँ", "किन", "कसरी",
    "अनि", "तर", "पनि", "नि", "न", "त", "नै", "ल", "है", "हौ", " हो", "अब", "फेरि",
    "सँग", "संग", "लाई", "बाट", "देखि", "सम्म", "भन्दा", "जस्तो", "जस्तै", "जब", "तब",
    "हरे", "ओ", "ए", "आ", "हे", "ना", "ल", "हुन्छ", "गर्ने", "भएको", "गरेको",
}

def _mood(label: str, score: float) -> str:
    if score <= -0.35:
        return "Melancholic / Sad"
    if score >= 0.35:
        return "Upbeat / Joyful"
    if label.lower().startswith("pos"):
        return "Warm / Hopeful"
    if label.lower().startswith("neg"):
        return "Reflective / Bittersweet"
    return "Neutral / Calm"


def probe_predict(embedding: np.ndarray, coef: np.ndarray, intercept: np.ndarray) -> np.ndarray:
    """Sigmoid of the linear mood probe for one L2-normalized embedding."""
    return 1.0 / (1.0 + np.exp(-(coef @ embedding + intercept)))


def sentiment_label(score: float, positive_threshold: float, negative_threshold: float) -> str:
    if score > positive_threshold:
        return "positive"
    if score < -negative_threshold:
        return "negative"
    return "neutral"


class MusicAnalyzer:
    def __init__(self, config: Config | None = None, use_transliterator: bool = True):
        self.config = config or Config()
        self.use_transliterator = use_transliterator
        self._probe = None
        self._embed_model = None
        self._transliterator = None
        self._corpus = None
        self._corpus_embeddings = None
        self._tfidf = None
        self._tfidf_matrix = None

    def _load_probe(self):
        if self._probe is not None:
            return self._probe
        path = self.config.mood_probe_npz
        if not path.exists():
            raise FileNotFoundError(
                f"Mood probe not found at {path}. Train it first: "
                "python scripts/train_mood_probe.py --pseudo <labels.csv>"
            )
        data = np.load(path, allow_pickle=False)
        self._probe = {
            "coef": data["coef"].astype(np.float32),
            "intercept": data["intercept"].astype(np.float32),
            "labels": [str(x) for x in data["labels"]],
        }
        return self._probe

    def _load_embedder(self):
        if self._embed_model is None:
            from music_rec.embeddings import get_shared_model

            self._embed_model = get_shared_model(
                self.config.embedding_model, self.config.embedding_device
            )
        return self._embed_model

    def _load_transliterator(self):
        if self._transliterator is None:
            from lyrics_pipeline.transliterator import NepaliTransliterator

            self._transliterator = NepaliTransliterator(
                checkpoint_path=self.config.transliterator_checkpoint,
                vocab_path=self.config.transliterator_vocab,
            )
        return self._transliterator

    def _load_corpus(self):
        if self._corpus is not None:
            return
        import pandas as pd

        if not self.config.cleaned_lyrics_csv.exists():
            raise FileNotFoundError(
                f"Corpus not found at {self.config.cleaned_lyrics_csv}. "
                "Run scripts/run_music_rec.py audit first."
            )
        self._corpus = pd.read_csv(self.config.cleaned_lyrics_csv, encoding="utf-8")
        if self.config.embeddings_npy.exists():
            self._corpus_embeddings = _l2_normalize(
                np.load(self.config.embeddings_npy).astype(np.float32)
            )

    def _load_tfidf(self):
        if self._tfidf is not None:
            return
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._load_corpus()

        def analyzer(text: str):
            toks = tokenize(text)
            return [
                t for t in toks
                if t not in NEPALI_STOPWORDS and len(t) > 1 and not t.isdigit()
            ]

        self._tfidf = TfidfVectorizer(analyzer=analyzer, min_df=2, max_df=0.6)
        self._tfidf_matrix = self._tfidf.fit_transform(
            self._corpus["lyrics"].fillna("").astype(str)
        )

    def normalize_input(self, text: str) -> dict:
        """Detect script and transliterate Romanized -> Devanagari if needed."""
        original = normalize_nfc(text).strip()
        has_roman = bool(_ROMAN_RE.search(original))
        has_dev = bool(_DEVANAGARI_RE.search(original))
        script = "mixed" if (has_roman and has_dev) else "romanized" if has_roman else "devanagari"

        devanagari = original
        transliterated = False
        if self.use_transliterator and has_roman:
            translit = self._load_transliterator()
            if translit.available:
                devanagari = translit.transliterate_text(original)
                transliterated = True
        return {
            "original": original,
            "script_detected": script,
            "devanagari": devanagari,
            "transliterated": transliterated,
        }

    def analyze_sentiment(self, devanagari_text: str) -> dict:
        probe = self._load_probe()
        model = self._load_embedder()

        from music_rec.embeddings import _encode_chunked

        max_len = min(self.config.embed_window_tokens, model.max_seq_length)
        stride = max(1, min(self.config.embed_window_stride, max_len - 1))
        matrix, _, _ = _encode_chunked(
            model,
            [devanagari_text],
            self.config.embed_batch_size,
            max_len,
            stride,
            1,
            quiet=True,
        )
        embedding = matrix[0]
        norm = float(np.linalg.norm(embedding)) or 1.0
        probs = probe_predict(embedding / norm, probe["coef"], probe["intercept"])
        by_label = {label: float(p) for label, p in zip(probe["labels"], probs)}

        score = by_label.get("positive", 0.0) - by_label.get("negative", 0.0)
        label = sentiment_label(
            score,
            self.config.probe_positive_threshold,
            self.config.probe_negative_threshold,
        )
        emotions = {
            name: round(by_label.get(name, 0.0), 4) for name in ("joy", "sadness", "anger")
        }
        return {
            "label": label,
            "score": round(score, 4),
            "mood": _mood(label, score),
            "emotions": emotions,
            "probabilities": {name: round(p, 4) for name, p in by_label.items()},
        }

    def extract_keywords(self, devanagari_text: str, top_n: int = 10) -> list[dict]:
        self._load_tfidf()
        vec = self._tfidf.transform([devanagari_text])
        if vec.nnz == 0:
            return []
        feature_names = self._tfidf.get_feature_names_out()
        coo = vec.tocoo()
        ranked = sorted(zip(coo.col, coo.data), key=lambda x: x[1], reverse=True)
        return [
            {"keyword": feature_names[idx], "weight": round(float(w), 4)}
            for idx, w in ranked[:top_n]
        ]

    def predict_category(self, devanagari_text: str, k: int = 10) -> dict:
        self._load_corpus()
        if self._corpus_embeddings is None or "category" not in self._corpus.columns:
            return {"category": None, "confidence": None, "neighbors": []}

        query = self._load_embedder().encode([devanagari_text], convert_to_numpy=True)[0]
        query = query.astype(np.float32)
        query /= np.linalg.norm(query) or 1.0
        sims = self._corpus_embeddings @ query
        top_idx = np.argsort(-sims)[:k]

        categories = self._corpus.iloc[top_idx]["category"].fillna("unknown").tolist()
        from collections import Counter

        counts = Counter(categories)
        best, best_count = counts.most_common(1)[0]
        neighbors = [
            {
                "song_id": int(self._corpus.iloc[i]["song_id"]),
                "title": str(self._corpus.iloc[i]["title"]),
                "artist": str(self._corpus.iloc[i]["artist"]),
                "similarity": round(float(sims[i]), 4),
            }
            for i in top_idx[:5]
        ]
        return {
            "category": best,
            "confidence": round(best_count / k, 3),
            "neighbors": neighbors,
        }

    def analyze(self, text: str, top_keywords: int = 10) -> dict:
        norm = self.normalize_input(text)
        dev = norm["devanagari"]
        return {
            "input": norm,
            "sentiment": self.analyze_sentiment(dev),
            "keywords": self.extract_keywords(dev, top_n=top_keywords),
            "category": self.predict_category(dev),
        }


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _format_report(result: dict) -> str:
    inp = result["input"]
    sent = result["sentiment"]
    cat = result["category"]
    lines = []
    lines.append("=" * 60)
    lines.append("  MUSIC ANALYZER REPORT")
    lines.append("=" * 60)
    lines.append(f"Script detected : {inp['script_detected']}")
    if inp["transliterated"]:
        lines.append(f"Transliterated  : {inp['devanagari'][:120]}")
    lines.append("")
    lines.append("SENTIMENT")
    lines.append(f"  Label  : {sent['label']}")
    lines.append(f"  Score  : {sent['score']:+.3f}   (range -1 .. +1)")
    lines.append(f"  Mood   : {sent['mood']}")
    if sent.get("emotions"):
        emo = "  ".join(f"{k}={v:.2f}" for k, v in sent["emotions"].items())
        lines.append(f"  Emo    : {emo}")
    probs = "  ".join(f"{k}={v:.2f}" for k, v in sent["probabilities"].items())
    lines.append(f"  Probs  : {probs}")
    lines.append("")
    lines.append("KEYWORDS (terms that would lead to this song)")
    if result["keywords"]:
        kw = ", ".join(k["keyword"] for k in result["keywords"])
        lines.append(f"  {kw}")
    else:
        lines.append("  (no distinctive keywords found)")
    lines.append("")
    lines.append("CATEGORY")
    lines.append(f"  Predicted : {cat['category']}  (confidence {cat['confidence']})")
    if cat["neighbors"]:
        lines.append("  Closest songs:")
        for n in cat["neighbors"]:
            lines.append(f"    - {n['title']} — {n['artist']}  (sim {n['similarity']})")
    lines.append("=" * 60)
    return "\n".join(lines)


def run_from_variable():
    text = LYRICS
    if not text or not text.strip():
        raise SystemExit("Please set the LYRICS variable at the top of MusicAnalyzer.py.")

    analyzer = MusicAnalyzer(use_transliterator=USE_TRANSLITERATION)
    result = analyzer.analyze(text, top_keywords=TOP_KEYWORDS)

    if OUTPUT_AS_JSON:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_report(result))


def main():
    parser = argparse.ArgumentParser(description="Analyze Nepali song lyrics.")
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--text", type=str, help="Lyrics text (Romanized or Devanagari)")
    src.add_argument("--file", type=Path, help="Path to a lyrics text file")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a report")
    parser.add_argument("--top-keywords", type=int, default=TOP_KEYWORDS)
    parser.add_argument("--no-transliterate", action="store_true", help="Disable transliteration")
    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.file:
        text = args.file.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    if not text or not text.strip():
        parser.error("No lyrics provided (use --text, --file, or stdin).")

    analyzer = MusicAnalyzer(use_transliterator=not args.no_transliterate)
    result = analyzer.analyze(text, top_keywords=args.top_keywords)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_report(result))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        run_from_variable()
