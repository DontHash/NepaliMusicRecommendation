"""Clean and transliterate scraped Nepali lyrics for downstream ML tasks."""

from .cleaner import clean_artist, clean_lyrics_body, clean_title, detect_script_style
from .pipeline import LyricsCleaningPipeline, PipelineResult

__all__ = [
    "LyricsCleaningPipeline",
    "PipelineResult",
    "clean_artist",
    "clean_lyrics_body",
    "clean_title",
    "detect_script_style",
]
