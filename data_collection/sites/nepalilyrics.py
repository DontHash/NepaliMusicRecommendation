"""nepalilyrics.net adapter (sitemap-only, per robots policy).

Robots policy for generic agents allows site pages except /admin, /api, /search.
This adapter additionally restricts itself to sitemap-listed /en/songs/ pages and never
requests API, search, or admin paths. Requests use the shared honest UA and a 2.5s
per-request rate limit (see config.RATE_LIMITS).
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .base import SongPage, strip_chord_lines

DOMAIN = "nepalilyrics.net"
BASE = "https://nepalilyrics.net"
SITEMAP_URL = f"{BASE}/sitemap.xml"
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
SONG_PATH_PREFIX = "/en/songs/"
ALLOWED_HOSTS = {"nepalilyrics.net", "www.nepalilyrics.net"}
FORBIDDEN_PATH_FRAGMENTS = ("/api", "/search", "/admin")
TITLE_RE = re.compile(
    r"^(?P<title>.+?)\s+-\s+(?P<artist>.+?)(?:\s+Lyrics\s*&\s*Chords)?$",
    re.IGNORECASE,
)
CHORD_NODE_SELECTOR = ".font-mono, [class*='chord']"


def allowed_url(url: str) -> bool:
    parts = urlsplit(url)
    if parts.netloc.lower() not in ALLOWED_HOSTS:
        return False
    path = parts.path.lower()
    if any(fragment in path for fragment in FORBIDDEN_PATH_FRAGMENTS):
        return False
    return path.startswith(SONG_PATH_PREFIX)


def discover(client, max_pages: int = 0) -> list[str]:
    xml = client.get_text(f"site_{DOMAIN}", SITEMAP_URL)
    if not xml:
        return []
    return sorted({url for url in LOC_RE.findall(xml) if allowed_url(url)})


def parse(html: str, url: str) -> SongPage | None:
    if not allowed_url(url):
        return None
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.select_one("meta[property='og:title']")
    raw = str(meta["content"]) if meta is not None and meta.get("content") else ""
    if not raw and soup.title is not None and soup.title.string:
        raw = soup.title.string
    match = TITLE_RE.match(raw.strip())
    if match:
        title = match.group("title").strip()
        artist = match.group("artist").strip()
    else:
        title = re.sub(r"\s*Lyrics\s*&\s*Chords\s*$", "", raw, flags=re.IGNORECASE).strip()
        artist = ""
    blocks: list[str] = []
    for node in soup.select("p.whitespace-pre-wrap"):
        for chord in node.select(CHORD_NODE_SELECTOR):
            chord.decompose()
        text = node.get_text()
        if text.strip():
            blocks.append(text)
    lyrics = strip_chord_lines("\n".join(blocks))
    return SongPage(artist=artist, title=title, lyrics=lyrics)
