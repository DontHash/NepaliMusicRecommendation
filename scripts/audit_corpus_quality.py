"""Audit corpus text quality for scrape artifacts and quarantine candidates.

Scans ``music_rec_artifacts/cleaned_lyrics.csv`` for crawler-site artifacts in
both English and transliterated Devanagari forms, using two signals:

* pattern families (crawler footers, video/music credits, hashtags, emojis,
  annotation tags, embeds, URLs),
* cross-song repeated template lines (a line shared by many songs is a
  scrape-template candidate, reported separately because shared refrains such
  as "हो हो हो" are genuine lyrics).

Writes a JSON summary, a per-song flag table for manual review, and a
quarantine CSV for songs whose text is unrecoverably damaged.

Usage:
    python scripts/audit_corpus_quality.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lyrics_pipeline.patterns import EMOJI_RE, INVISIBLE_CHARS_RE  # noqa: E402
from music_rec.config import Config  # noqa: E402

ARTIFACT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "crawler_footer",
        re.compile(
            r"(?:डाउनलोड\s*लिरिक्स|क्लिक\s*हेरे|स्टार्ट\s*टाइमर|वाच\s*ओन|युट्यु[बभ]|"
            r"download\s+lyrics|click\s+here|start\s+timer|watch\s+on\s+youtube)",
            re.IGNORECASE,
        ),
    ),
    (
        "video_credits",
        re.compile(
            r"(?:विदेओ\s*क्रेडिट्स|क्रेडिट्स|कास्ट\s*[:：]|वोकल\s*[:：]|निर्देशक\s*[:：]|"
            r"निर्माता\s*[:：]|गायक\s*[:：]|स्टुडियो\s*[:：]|कोरियोग्राफर|सिनेमाटोग्राफर|"
            r"video\s+credits?|cast\s*[:：]|vocals?\s*[:：])",
            re.IGNORECASE,
        ),
    ),
    (
        "romanize_block",
        re.compile(r"(?:रोमानाइज|डिस्क्रिप्सन|विवरण\s*[:：]|romaniz)", re.IGNORECASE),
    ),
    (
        "contributor_block",
        re.compile(r"(?:कन्ट्रिब्युटर्ड|contribut)", re.IGNORECASE),
    ),
    (
        "embed_marker",
        re.compile(r"(?:नएम्बेड|एम्बेड|\bembed\b)", re.IGNORECASE),
    ),
    ("hashtag", re.compile(r"(?<!\w)#[^\s#]+")),
    (
        "url",
        re.compile(
            r"(?:https?://|www\.|एचटीटीपी|डब्ल्यूडब्ल्यूडब्ल्यू|डब्लुडब्लु|हट्टप)",
            re.IGNORECASE,
        ),
    ),
    (
        "lyrics_credit",
        re.compile(r"(?:लिरिक्स\s*[:：]|lyrics\s*[:：])", re.IGNORECASE),
    ),
    ("annotation_tag", re.compile(r"^\[[^\]]{2,40}\]$")),
    ("emoji", EMOJI_RE),
    ("music_credit", re.compile(r"^[♬♪♩♫]|सोङ\s*[:：]")),
)

METADATA_LEXICON = (
    "लिरिक्स",
    "क्रेडिट्स",
    "विदेओ",
    "डाउनलोड",
    "स्टुडियो",
    "रेकर्डिङ",
    "रेकर्डिस्ट",
    "मिक्स",
    "मास्टर",
    "क्लिक",
    "वाच",
    "युट्युब",
    "डिस्क्रिप्सन",
    "रोमानाइज",
    "स्पेसियल",
    "थ्याङ्क्स",
    "डिजिटल",
    "म्युजिक",
    "भर्सन",
    "कोरियोग्राफर",
    "प्रोडक्सन",
    "आउडियो",
    "सिनेमाटोग्राफर",
    "निर्देशक",
    "डाइरेक्टर",
    "गायक",
    "एरेन्जर",
    "कन्ट्रिब्युटर",
    "रिपोर्ट",
    "हेडफोन्स",
    "एम्बेड",
    "नेपालिसंग",
    "पब्लिसिटी",
    "म्यानेजमेन्ट",
    "प्रोड्युसर",
    "प्रोड्युस्ड",
    "कम्पोज्ड",
    "परफर्म्ड",
    "डिजाइन",
    "कोपीराइट",
    "प्रेजेन्ट्स",
    "ब्याकग्राउन्ड",
    "एक्जिक्युटिभ",
    "क्यामेरा",
    "डाइरेक्सन",
    "कलाकार",
)

KNOWN_BAD: dict[int, str] = {
    1855: "legacy source text is phonetic Devanagari of English lyrics; unrecoverable",
    1860: "legacy source text corrupted (non-Nepali word salad); unrecoverable",
}


def _normalize_line(line: str) -> str:
    text = unicodedata.normalize("NFKC", line or "")
    text = INVISIBLE_CHARS_RE.sub("", text)
    text = text.lower()
    text = re.sub(r"[^\w\s\u0900-\u097F]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _ascii_ratio(line: str) -> float:
    letters = [char for char in line if char.isalpha()]
    if not letters:
        return 0.0
    ascii_letters = sum(1 for char in letters if char.isascii())
    return ascii_letters / len(letters)


def _metadata_like(line: str) -> bool:
    if any(token in line for token in METADATA_LEXICON):
        return True
    return _ascii_ratio(line) >= 0.5


def _source_map(corpus_final_path: Path) -> dict[str, str]:
    frame = pd.read_csv(corpus_final_path, encoding="utf-8").fillna("")
    mapping: dict[str, str] = {}
    for title, artist, source in zip(
        frame["title_clean"], frame["artist_clean"], frame["source"]
    ):
        mapping.setdefault(f"{title}\x1f{artist}", str(source))
    return mapping


def _gold_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    frame = pd.read_csv(path, encoding="utf-8")
    if "song_id" not in frame.columns:
        return set()
    return {int(value) for value in frame["song_id"]}


def find_shared_templates(
    songs: list[tuple[int, str]], min_songs: int, min_chars: int
) -> dict[str, set[int]]:
    counts: dict[str, set[int]] = {}
    for song_id, lyrics in songs:
        seen: set[str] = set()
        for line in str(lyrics).splitlines():
            norm = _normalize_line(line)
            if len(norm) < min_chars or norm in seen:
                continue
            seen.add(norm)
            counts.setdefault(norm, set()).add(song_id)
    return {line: ids for line, ids in counts.items() if len(ids) >= min_songs}


def scan_corpus(
    cleaned_path: Path,
    corpus_final_path: Path,
    min_songs_template: int,
    min_template_chars: int,
    artifact_ratio: float,
    top_templates: int,
) -> tuple[dict, pd.DataFrame]:
    frame = pd.read_csv(cleaned_path, encoding="utf-8").fillna("")
    sources = _source_map(corpus_final_path)
    mood_gold = _gold_ids(PROJECT_ROOT / "eval" / "mood_gold.csv")
    line_gold = _gold_ids(PROJECT_ROOT / "eval" / "line_mood_gold.csv")

    songs = [(int(row.song_id), str(row.lyrics)) for row in frame.itertuples()]
    templates = find_shared_templates(songs, min_songs_template, min_template_chars)

    pattern_songs: dict[str, int] = {name: 0 for name, _ in ARTIFACT_PATTERNS}
    pattern_lines: dict[str, int] = {name: 0 for name, _ in ARTIFACT_PATTERNS}
    rows: list[dict] = []
    total_lines = 0

    for row in frame.itertuples():
        song_id = int(row.song_id)
        key = f"{row.title}\x1f{row.artist}"
        source = sources.get(key, "")
        lines = [line for line in str(row.lyrics).splitlines() if line.strip()]
        total_lines += len(lines)

        hit_lines = 0
        hit_types: set[str] = set()
        repeat_lines = 0
        meta_repeat_lines = 0
        for line in lines:
            norm = _normalize_line(line)
            line_hits = [name for name, regex in ARTIFACT_PATTERNS if regex.search(line)]
            if line_hits:
                hit_lines += 1
                hit_types.update(line_hits)
                for name in line_hits:
                    if name in pattern_lines:
                        pattern_lines[name] += 1
            if len(norm) >= min_template_chars and norm in templates:
                repeat_lines += 1
                if _metadata_like(norm):
                    meta_repeat_lines += 1

        for name in hit_types:
            if name in pattern_songs:
                pattern_songs[name] += 1

        ratio = hit_lines / len(lines) if lines else 0.0
        reason = KNOWN_BAD.get(song_id, "")
        quarantine = bool(reason) or ratio >= artifact_ratio
        if not reason and quarantine:
            reason = f"artifact ratio {ratio:.0%} of lines ({hit_lines}/{len(lines)})"
        rows.append(
            {
                "song_id": song_id,
                "title": row.title,
                "artist": row.artist,
                "source": source,
                "total_lines": len(lines),
                "artifact_lines": hit_lines,
                "artifact_ratio": round(ratio, 4),
                "artifact_types": ",".join(sorted(hit_types)),
                "repeat_lines": repeat_lines,
                "meta_repeat_lines": meta_repeat_lines,
                "in_mood_gold": song_id in mood_gold,
                "in_line_gold": song_id in line_gold,
                "quarantine": quarantine,
                "quarantine_reason": reason if quarantine else "",
            }
        )

    songs_frame = pd.DataFrame(rows).sort_values(
        ["artifact_ratio", "artifact_lines"], ascending=False
    )

    per_source: dict[str, dict] = {}
    for source, group in songs_frame.groupby("source"):
        label = source or "(unknown)"
        per_source[label] = {
            "songs": int(len(group)),
            "artifact_songs": int(group["artifact_lines"].gt(0).sum()),
            "quarantine_songs": int(group["quarantine"].sum()),
            "lyrics_lines": int(group["total_lines"].sum()),
            "artifact_lines": int(group["artifact_lines"].sum()),
            "artifact_ratio": round(
                float(group["artifact_lines"].sum() / max(group["total_lines"].sum(), 1)),
                4,
            ),
        }

    top = sorted(templates.items(), key=lambda item: len(item[1]), reverse=True)
    template_rows = []
    for line, song_ids in top[:top_templates]:
        sample = sorted(song_ids)[:5]
        sample_sources = sorted(
            {
                sources.get(f"{row.title}\x1f{row.artist}", "")
                for row in frame.itertuples()
                if int(row.song_id) in sample
            }
        )
        template_rows.append(
            {
                "line": line,
                "songs": len(song_ids),
                "metadata_like": _metadata_like(line),
                "sample_song_ids": sample,
                "sample_sources": sample_sources,
            }
        )

    report = {
        "corpus": str(cleaned_path),
        "corpus_final": str(corpus_final_path),
        "total_songs": int(len(frame)),
        "total_lines": total_lines,
        "songs_with_artifacts": int(songs_frame["artifact_lines"].gt(0).sum()),
        "artifact_lines_total": int(songs_frame["artifact_lines"].sum()),
        "patterns": {
            name: {"songs": pattern_songs[name], "lines": pattern_lines[name]}
            for name, _ in ARTIFACT_PATTERNS
        },
        "shared_templates": {
            "count": len(templates),
            "metadata_like": sum(1 for line in templates if _metadata_like(line)),
            "min_songs": min_songs_template,
            "top": template_rows,
        },
        "per_source": per_source,
        "known_bad": {str(key): value for key, value in KNOWN_BAD.items()},
        "quarantine_songs": int(songs_frame["quarantine"].sum()),
        "gold_impact": {
            "mood_gold_songs": sorted(
                set(songs_frame.loc[songs_frame["in_mood_gold"], "song_id"])
                & set(songs_frame.loc[songs_frame["artifact_lines"].gt(0), "song_id"])
            ),
            "line_gold_songs": sorted(
                set(songs_frame.loc[songs_frame["in_line_gold"], "song_id"])
                & set(songs_frame.loc[songs_frame["artifact_lines"].gt(0), "song_id"])
            ),
        },
    }
    return report, songs_frame


def main() -> None:
    config = Config()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--cleaned", type=Path, default=config.cleaned_lyrics_csv)
    parser.add_argument(
        "--corpus-final",
        type=Path,
        default=PROJECT_ROOT / "CSVs Dataset" / "corpus_final.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=config.artifacts_dir / "corpus_quality_report.json",
    )
    parser.add_argument(
        "--songs-out",
        type=Path,
        default=config.artifacts_dir / "corpus_quality_songs.csv",
    )
    parser.add_argument(
        "--quarantine-out",
        type=Path,
        default=config.artifacts_dir / "corpus_quarantine.csv",
    )
    parser.add_argument("--min-songs-template", type=int, default=4)
    parser.add_argument("--min-template-chars", type=int, default=12)
    parser.add_argument("--artifact-ratio", type=float, default=0.5)
    parser.add_argument("--top-templates", type=int, default=40)
    args = parser.parse_args()

    report, songs_frame = scan_corpus(
        args.cleaned,
        args.corpus_final,
        args.min_songs_template,
        args.min_template_chars,
        args.artifact_ratio,
        args.top_templates,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    columns = [
        "song_id",
        "title",
        "artist",
        "source",
        "total_lines",
        "artifact_lines",
        "artifact_ratio",
        "artifact_types",
        "repeat_lines",
        "meta_repeat_lines",
        "in_mood_gold",
        "in_line_gold",
        "quarantine",
        "quarantine_reason",
    ]
    songs_frame[columns].to_csv(args.songs_out, index=False, encoding="utf-8")

    quarantine = songs_frame[songs_frame["quarantine"]][columns]
    quarantine.to_csv(args.quarantine_out, index=False, encoding="utf-8")

    print(f"total songs           {report['total_songs']}")
    print(f"total lines           {report['total_lines']}")
    print(f"songs with artifacts  {report['songs_with_artifacts']}")
    print(f"artifact lines        {report['artifact_lines_total']}")
    print(f"shared templates      {report['shared_templates']['count']}")
    print(f"quarantine songs      {report['quarantine_songs']}")
    print(f"mood gold affected    {report['gold_impact']['mood_gold_songs']}")
    print(f"line gold affected    {report['gold_impact']['line_gold_songs']}")
    print(f"report                {args.report}")
    print(f"songs table           {args.songs_out}")
    print(f"quarantine table      {args.quarantine_out}")


if __name__ == "__main__":
    main()
