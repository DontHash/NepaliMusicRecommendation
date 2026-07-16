"""End-to-end lyrics dataset cleaning and transliteration."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .cleaner import (
    clean_artist,
    clean_lyrics_body,
    clean_title,
    detect_script_style,
)
from .transliterator import NepaliTransliterator

try:
    from tqdm.auto import tqdm
except ImportError:
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else []


@dataclass
class PipelineResult:
    category: str
    title: str
    artist: str
    title_clean: str
    artist_clean: str
    lyrics_original: str
    lyrics_cleaned: str
    lyrics_devanagari: str
    script_style_original: str
    script_style_cleaned: str
    line_count: int
    char_count: int
    transliterated: bool
    cleaning_actions: list[str] = field(default_factory=list)


class LyricsCleaningPipeline:
    def __init__(
        self,
        transliterator: NepaliTransliterator | None = None,
        transliterate: bool = True,
    ):
        self.transliterator = transliterator or NepaliTransliterator()
        self.transliterate = transliterate

    def process_row(self, row: dict[str, str]) -> PipelineResult:
        category = (row.get("Category") or "").strip()
        title = row.get("Title") or ""
        artist = row.get("Artist") or ""
        lyrics_original = row.get("Lyrics") or ""

        title_clean = clean_title(title)
        artist_clean = clean_artist(artist)
        lyrics_cleaned, actions = clean_lyrics_body(lyrics_original, title, artist)

        lyrics_devanagari = lyrics_cleaned
        did_transliterate = False
        if self.transliterate and self.transliterator.available:
            converted = self.transliterator.transliterate_text(lyrics_cleaned)
            if converted != lyrics_cleaned:
                did_transliterate = True
                actions.append("transliterated_roman_tokens")
            lyrics_devanagari = converted
        elif self.transliterate and detect_script_style(lyrics_cleaned) in {"romanized", "mixed"}:
            actions.append("transliteration_skipped_no_model")

        line_count = len([line for line in lyrics_devanagari.splitlines() if line.strip()])
        char_count = len(lyrics_devanagari)

        return PipelineResult(
            category=category,
            title=title,
            artist=artist,
            title_clean=title_clean,
            artist_clean=artist_clean,
            lyrics_original=lyrics_original,
            lyrics_cleaned=lyrics_cleaned,
            lyrics_devanagari=lyrics_devanagari,
            script_style_original=detect_script_style(lyrics_original),
            script_style_cleaned=detect_script_style(lyrics_devanagari),
            line_count=line_count,
            char_count=char_count,
            transliterated=did_transliterate,
            cleaning_actions=actions,
        )

    def process_file(
        self,
        input_csv: Path | str,
        output_csv: Path | str,
        report_json: Path | str | None = None,
    ) -> dict:
        input_csv = Path(input_csv)
        output_csv = Path(output_csv)
        rows = list(csv.DictReader(open(input_csv, encoding="utf-8", newline="")))

        results = []
        for row in tqdm(rows, desc="Processing lyrics", unit="song"):
            results.append(self.process_row(row))
        output_csv.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "category",
            "title_clean",
            "artist_clean",
            "lyrics_devanagari",
            "line_count",
            "char_count",
            "script_style_original",
            "script_style_cleaned",
            "transliterated",
        ]

        with open(output_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(
                    {
                        "category": result.category,
                        "title_clean": result.title_clean,
                        "artist_clean": result.artist_clean,
                        "lyrics_devanagari": result.lyrics_devanagari,
                        "line_count": result.line_count,
                        "char_count": result.char_count,
                        "script_style_original": result.script_style_original,
                        "script_style_cleaned": result.script_style_cleaned,
                        "transliterated": int(result.transliterated),
                    }
                )

        summary = self._build_report(results)
        if report_json:
            Path(report_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary

    @staticmethod
    def _build_report(results: list[PipelineResult]) -> dict:
        empty_after_cleaning = sum(1 for r in results if r.line_count == 0)
        transliterated_rows = sum(1 for r in results if r.transliterated)
        still_roman = sum(1 for r in results if r.script_style_cleaned in {"romanized", "mixed"})

        noise_counter: dict[str, int] = {}
        for result in results:
            for action in result.cleaning_actions:
                key = action.split(":", 1)[0]
                noise_counter[key] = noise_counter.get(key, 0) + 1

        samples = []
        for result in results[:3]:
            samples.append(
                {
                    "title_clean": result.title_clean,
                    "artist_clean": result.artist_clean,
                    "first_lines": result.lyrics_devanagari.splitlines()[:6],
                }
            )

        return {
            "total_rows": len(results),
            "empty_after_cleaning": empty_after_cleaning,
            "transliterated_rows": transliterated_rows,
            "rows_still_with_roman_letters": still_roman,
            "transliterator_loaded": any(r.transliterated for r in results) or still_roman == 0,
            "noise_actions": noise_counter,
            "samples": samples,
        }
