"""Optional syncedlyrics aggregator wrapper (per-provider isolation).

Lrclib is covered by ``data_collection.sources.lrclib``; this wrapper exists
for the extra providers (Musixmatch/NetEase) that occasionally have tracks
LRCLIB lacks. Each provider is queried separately because the upstream library
can raise on partial provider failures.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DEFAULT_PROVIDERS = ("Musixmatch", "NetEase")


def fetch_lyrics(title: str, artist: str, providers: tuple[str, ...] | list[str] | None = None) -> str | None:
    if not title:
        return None
    try:
        import syncedlyrics
    except ImportError:
        logger.warning("syncedlyrics not installed; skipping stage")
        return None
    logging.getLogger("syncedlyrics").setLevel(logging.CRITICAL)
    search_term = f"{title} {artist}".strip()
    for provider in providers or DEFAULT_PROVIDERS:
        try:
            result = syncedlyrics.search(search_term, providers=[provider], plain_only=True)
        except Exception as exc:  # noqa: BLE001 - upstream providers fail unpredictably
            logger.debug("syncedlyrics provider %s failed: %s", provider, exc)
            continue
        if result:
            text = str(result).strip()
            if text:
                return text
    return None
