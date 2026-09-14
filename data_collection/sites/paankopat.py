"""PaanKoPat.com adapter (WordPress, Romanized lyrics + chord lines)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import SongPage, strip_chord_lines

DOMAIN = "paankopat.com"
BASE = "https://paankopat.com"
SITEMAP_URL = f"{BASE}/post-sitemap.xml"
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
ROOT_LINK_RE = re.compile(r"^https://paankopat\.com/([a-z0-9][a-z0-9-]*)/$")
SITE_SUFFIX_RE = re.compile(r"\s*[-–|]\s*Paan Ko Pat.*$", re.IGNORECASE)
TITLE_SUFFIX_RE = re.compile(
    r"\s*(?:[-–|:]\s*)?(?:lyrics\s*(?:and|&)\s*chords?|chords?\s*(?:and|&)\s*lyrics?|lyrics?|chords?)\s*$",
    re.IGNORECASE,
)
FILLER_RE = re.compile(r"\b(lyrics?|chords?|and)\b", re.IGNORECASE)
NOISE_LINE_RE = re.compile(r"^\s*(scale|capo|tuning|chords?|key)\s*:", re.IGNORECASE)
NON_ARTIST_SLUGS = {
    "pop-song",
    "nepali-song",
    "modern-song",
    "folk-song",
    "adhunik-song",
    "lyrics",
    "chords",
    "song",
    "songs",
    "music",
    "topi-studios",
    "category",
    "tag",
    "author",
    "page",
    "feed",
    "comments",
}


def discover(client, max_pages: int = 0) -> list[str]:
    xml = client.get_text("site_paankopat", SITEMAP_URL)
    if not xml:
        return []
    return sorted(set(LOC_RE.findall(xml)))


def _clean_title(value: str) -> str:
    value = SITE_SUFFIX_RE.sub("", value).strip(" -|")
    previous = None
    while value and value != previous:
        previous = value
        value = TITLE_SUFFIX_RE.sub("", value).strip(" -|:,")
    return value


def _artist_from_categories(soup: BeautifulSoup) -> str:
    article = soup.find("article") or soup
    candidates: list[str] = []
    for anchor in article.find_all("a", href=True):
        match = ROOT_LINK_RE.match(anchor["href"])
        if not match:
            continue
        slug = match.group(1)
        if slug in NON_ARTIST_SLUGS or re.match(r"^\d{4}$|^\d{2}$", slug):
            continue
        text = anchor.get_text(strip=True)
        if text and text.casefold() != slug.replace("-", " "):
            candidates.append(text)
        elif text:
            candidates.append(text)
    return candidates[-1] if candidates else ""


def _title_artist(soup: BeautifulSoup) -> tuple[str, str]:
    meta = soup.find("meta", attrs={"property": "og:title"})
    content = str(meta.get("content")) if meta and meta.get("content") else ""
    parts = [part.strip() for part in content.split("|") if part.strip()]
    title = ""
    artist = ""
    if parts:
        title = _clean_title(parts[0])
        if len(parts) > 1:
            artist_raw = parts[-1]
            artist = SITE_SUFFIX_RE.sub("", artist_raw)
            artist = FILLER_RE.sub(" ", artist)
            artist = re.sub(r"\s+", " ", artist).strip(" -|")
    if not artist:
        artist = _artist_from_categories(soup)
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
