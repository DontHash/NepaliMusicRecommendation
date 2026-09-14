"""SongsDiary.com adapter (Romanized Nepali lyrics, paginated listing)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import SongPage

DOMAIN = "songsdiary.com"
BASE = "https://songsdiary.com"
SONG_LINK_RE = re.compile(r'href="(https://songsdiary\.com/\d+/[^"/]+)"')
SONG_URL_RE = re.compile(r"^https://songsdiary\.com/\d+/(?P<slug>[^/]+)$")
MIN_LINKS_PER_PAGE = 3
SKIP_LINE_FRAGMENTS = ("read in devanagari", "⚠")


def discover(client, max_pages: int = 20) -> list[str]:
    urls: set[str] = set()
    for page in range(1, max_pages + 1):
        url = f"{BASE}/" if page == 1 else f"{BASE}/?page={page}"
        html = client.get_text("site_songsdiary", url)
        if not html:
            break
        found = set(SONG_LINK_RE.findall(html))
        urls |= found
        if len(found) < MIN_LINKS_PER_PAGE:
            break
    return sorted(urls)


def parse(html: str, url: str) -> SongPage | None:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("div.lyrics")
    if container is None:
        return None
    lines: list[str] = []
    for line in container.get_text("\n").splitlines():
        line = line.strip()
        if not line:
            continue
        lowered = line.casefold()
        if any(fragment in lowered for fragment in SKIP_LINE_FRAGMENTS):
            continue
        lines.append(line)
    lyrics = "\n".join(lines).strip()

    title = artist = ""
    match = SONG_URL_RE.match(url)
    if match:
        slug = match.group("slug")
        if "-lyrics-" in slug:
            raw_title, raw_artist = slug.split("-lyrics-", 1)
            title = raw_title.replace("-", " ").strip()
            artist = raw_artist.replace("~", " & ").replace("-", " ").strip()
    return SongPage(artist=artist, title=title, lyrics=lyrics)
