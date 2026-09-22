"""FastAPI backend for the ProjectR Mood Studio web app.

Serves the static frontend plus a small JSON API over the mood attribution
engine: corpus search, explainable per-song mood payloads, and ad-hoc lyric
analysis. Run via ``scripts/run_web_app.py``.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

os.environ.setdefault("PROJECTR_EMBED_DEVICE", "cpu")

from music_rec.config import Config  # noqa: E402
from music_rec.embeddings import get_shared_model  # noqa: E402
from music_rec.mood_attribution import MoodAttributor, get_attributor  # noqa: E402
from music_rec.mood_neighbors import get_mood_neighbors  # noqa: E402
from music_rec.recommender import MusicRecommender  # noqa: E402

logger = logging.getLogger("web_app")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _warm_backend() -> None:
    try:
        config = Config()
        recommender = get_recommender()
        model = get_shared_model(config.embedding_model, config.embedding_device)
        recommender.lexical
        model.encode(["warmup"], convert_to_numpy=True, show_progress_bar=False)
    except Exception as error:  # pragma: no cover - warmup is best-effort
        print(f"[mood-studio] backend warmup failed: {error}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.environ.get("PROJECTR_NO_WARMUP") != "1":
        threading.Thread(target=_warm_backend, daemon=True).start()
    yield


app = FastAPI(title="ProjectR Mood Studio", version="0.1.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("unhandled error: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal error"})

_corpus: pd.DataFrame | None = None
_payload_cache: dict[int, dict] = {}
_translit_helper = None
_recommender: MusicRecommender | None = None


def _load_corpus() -> pd.DataFrame:
    global _corpus
    if _corpus is None:
        frame = pd.read_csv(Config().cleaned_lyrics_csv, encoding="utf-8").fillna("")
        _corpus = frame[["song_id", "title", "artist"]]
    return _corpus


def _attributor() -> MoodAttributor:
    return get_attributor()


class _UnavailableRecommender:
    def __init__(self, error: Exception):
        self.error = error

    def recommend_by_text(self, text: str):
        raise RuntimeError(f"recommender unavailable: {self.error}")


def get_recommender() -> MusicRecommender:
    global _recommender
    if _recommender is None:
        try:
            config = Config()
            config.use_window_search = False
            _recommender = MusicRecommender.load(config)
        except Exception as error:  # pragma: no cover - artifacts missing
            _recommender = _UnavailableRecommender(error)
    return _recommender


class AnalyzeRequest(BaseModel):
    text: str
    transliterate: bool = True


def _title_artist_hits(query: str, limit: int) -> list[dict]:
    frame = _load_corpus()
    titles = frame["title"].str.lower()
    artists = frame["artist"].str.lower()
    mask = titles.str.contains(query, regex=False) | artists.str.contains(query, regex=False)
    hits = frame.loc[mask].copy()
    hits["_starts"] = hits["title"].str.lower().str.startswith(query)
    hits = hits.sort_values(["_starts", "title"], ascending=[False, True]).head(limit)
    results = []
    for row in hits.itertuples():
        title = str(row.title)
        results.append(
            {
                "song_id": int(row.song_id),
                "title": title,
                "artist": str(row.artist),
                "match": "title" if query in title.lower() else "artist",
            }
        )
    return results


def _lyric_hits(recommender, text: str, limit: int, seen: set[int]) -> list[dict]:
    if limit <= 0:
        return []
    try:
        recommendations = recommender.recommend_by_text(text)
    except Exception as error:  # pragma: no cover - backend optional
        print(f"[mood-studio] lyric search unavailable: {error}")
        return []
    results = []
    for rec in recommendations:
        if rec.song_id in seen:
            continue
        seen.add(rec.song_id)
        results.append(
            {
                "song_id": int(rec.song_id),
                "title": str(rec.title),
                "artist": str(rec.artist),
                "match": "lyrics",
                "score": float(rec.score),
            }
        )
        if len(results) >= limit:
            break
    return results


@app.get("/api/search")
def search(
    q: str = "",
    limit: int = 12,
    recommender: MusicRecommender = Depends(get_recommender),
):
    query = q.strip().lower()
    if not query:
        return {"results": []}
    results = _title_artist_hits(query, limit)
    seen = {item["song_id"] for item in results}
    results.extend(_lyric_hits(recommender, q.strip(), limit - len(results), seen))
    return {"results": results}


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


@app.get("/api/song/{song_id}/neighbors")
def neighbors(song_id: int, k: int = 8):
    k = max(1, min(k, 25))
    try:
        items = get_mood_neighbors().neighbors(song_id, k)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"song {song_id} not found")
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))
    return {"song_id": song_id, "neighbors": items}


@app.get("/api/mood/top")
def mood_top(emotion: str = "sadness", k: int = 10):
    k = max(1, min(k, 50))
    try:
        items = get_mood_neighbors().top(emotion, k)
    except ValueError:
        raise HTTPException(status_code=400, detail="emotion must be joy, sadness or anger")
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))
    return {"emotion": emotion, "top": items}


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
