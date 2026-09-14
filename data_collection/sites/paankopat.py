"""PaanKoPat.com adapter (WordPress, Romanized lyrics + chord lines)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import SongPage, strip_chord_lines

DOMAIN = "paankopat.com"
BASE = "https://paankopat.com"
SITEMAP_URL = f"{BASE}/post-sitemap.xml"
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
SITE_SUFFIX_RE = re.compile(r"\s*[-–|]\s*Paan Ko Pat.*$", re.IGNORECASE)
FILLER_RE = re.compile(r"\b(lyrics?|chords?|and)\b", re.IGNORECASE)
NOISE_LINE_RE = re.compile(r"^\s*(scale|capo|tuning|chords?|key)\s*:", re.IGNORECASE)


def discover(client, max_pages: int = 0) -> list[str]:
    xml = client.get_text("site_paankopat", SITEMAP_URL)
    if not xml:
        return []
    return sorted(set(LOC_RE.findall(xml)))


def _title_artist(soup: BeautifulSoup) -> tuple[str, str]:
    meta = soup.find("meta", attrs={"property": "og:title"})
    content = str(meta.get("content")) if meta and meta.get("content") else ""
    parts = [part.strip() for part in content.split("|") if part.strip()]
    if not parts:
        return "", ""
    title = parts[0]
    artist_raw = parts[-1] if len(parts) > 1 else ""
    artist = SITE_SUFFIX_RE.sub("", artist_raw)
    artist = FILLER_RE.sub(" ", artist)
    artist = re.sub(r"\s+", " ", artist).strip(" -|")
    return title, artist


def parse(html: str, url: str) -> SongPage | None:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("div.spnc-entry-content") or soup.select_one("article")
    if container is None:
        return None
    cleaned_lines: list[str] = []
    for line in container.get_text("\n").splitlines():
        if NOISE_LINE_RE.match(line):
            continue
        cleaned_lines.append(line)
    lyrics = strip_chord_lines("\n".join(cleaned_lines))
    title, artist = _title_artist(soup)
    return SongPage(artist=artist, title=title, lyrics=lyrics)
