"""FastAPI backend for the ProjectR Mood Studio web app.

Serves the static frontend plus a small JSON API over the mood attribution
engine: corpus search, explainable per-song mood payloads, and ad-hoc lyric
analysis. Run via ``scripts/run_web_app.py``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from music_rec.config import Config
from music_rec.mood_attribution import MoodAttributor, get_attributor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="ProjectR Mood Studio", version="0.1.0")

_corpus: pd.DataFrame | None = None
_payload_cache: dict[int, dict] = {}
_translit_helper = None


def _load_corpus() -> pd.DataFrame:
    global _corpus
    if _corpus is None:
        frame = pd.read_csv(Config().cleaned_lyrics_csv, encoding="utf-8").fillna("")
        _corpus = frame[["song_id", "title", "artist"]]
    return _corpus


def _attributor() -> MoodAttributor:
    return get_attributor()


class AnalyzeRequest(BaseModel):
    text: str
    transliterate: bool = True


@app.get("/api/search")
def search(q: str = "", limit: int = 12):
    query = q.strip().lower()
    if not query:
        return {"results": []}
    frame = _load_corpus()
    titles = frame["title"].str.lower()
    artists = frame["artist"].str.lower()
    mask = titles.str.contains(query, regex=False) | artists.str.contains(query, regex=False)
    hits = frame.loc[mask].copy()
    hits["_starts"] = hits["title"].str.lower().str.startswith(query)
    hits = hits.sort_values(["_starts", "title"], ascending=[False, True]).head(limit)
    return {
        "results": [
            {"song_id": int(row.song_id), "title": str(row.title), "artist": str(row.artist)}
            for row in hits.itertuples()
        ]
    }


@app.get("/api/song/{song_id}")
def song(song_id: int):
    if song_id in _payload_cache:
        return _payload_cache[song_id]
    try:
        payload = _attributor().attribute_song(song_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"song {song_id} not found")
    _payload_cache[song_id] = payload
    return payload


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty text")
    input_meta = None
    if req.transliterate:
        global _translit_helper
        if _translit_helper is None:
            from MusicAnalyzer import MusicAnalyzer

            _translit_helper = MusicAnalyzer(use_transliterator=True)
        norm = _translit_helper.normalize_input(req.text)
        text = norm["devanagari"]
        input_meta = {
            "script_detected": norm["script_detected"],
            "transliterated": norm["transliterated"],
            "devanagari": norm["devanagari"],
        }
    payload = _attributor().attribute_text(text)
    if input_meta:
        payload["input"] = input_meta
    return payload


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=503, detail="frontend not built yet")
    return FileResponse(index_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
