"""Generic Blogger (blogspot) adapter: discovery via Atom JSON feed, lyrics from feed content."""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import SimpleNamespace

from bs4 import BeautifulSoup

from .base import SongPage

FEED_PATH = "/feeds/posts/default"
DEFAULT_MAX_RESULTS = 150

CREDIT_LABEL_RE = re.compile(
    r"^(?:singer|music|song\s*writer|songwriter|lyricist|lyrics?|composer|arranger|arrenger|"
    r"producer|recorded|mixed|mastered|guitar|flute|bass|drums|studio|director|writer|cast|"
    r"album|released|label|genre|voice|vocals?|music\s*producer|music\s*composed)\b[:\s]*$",
    re.IGNORECASE,
)
TAIL_FRAGMENTS = (
    "all rights reserved",
    "media partner",
    "thank you",
    "thak you",
    "share this",
    "related posts",
    "you may also like",
    "labels:",
    "posted by",
    "no comments",
    "read more",
    "copyright",
    "writer/director",
)
TAIL_PREFIXES = ("♫", "⏭", "©", "℗", "---")
DEVANAGARI_MARKERS = ("नेपाली", "देवनागरी")
TITLE_IN_NEPALI_BY_RE = re.compile(
    r"^(?P<title>.+?)\s+Lyrics\s+in\s+Nepali\s+[Bb]y\s+(?P<artist>.+)$"
)
TITLE_LYRICS_BY_RE = re.compile(
    r"^(?P<title>.+?)\s+Lyrics\s+[Bb]y\s+(?P<artist>.+?)(?:\s*\|\|?.*)?$"
)
TITLE_PIPES_RE = re.compile(r"^(?P<title>.+?)\s+Lyrics?\s*\|\|?\s*(?P<artist>.+?)(?:\s*\|\|.*)?$")
TITLE_DASH_ARTIST_RE = re.compile(r"^(?P<title>.+?)\s*[-–]\s*(?P<artist>.+?)\s+Lyrics\s*$")
TITLE_DASH_LYRICS_RE = re.compile(r"^(?P<title>.+?)\s*[-–|]\s*Lyrics\s*$", re.IGNORECASE)


@dataclass(slots=True)
class FeedEntry:
    url: str
    title: str
    content_html: str


def _text(value) -> str:
    if isinstance(value, dict):
        return str(value.get("$t") or "")
    return str(value or "")


def _alternate_link(entry: dict) -> str:
    for link in entry.get("link") or []:
        if link.get("rel") == "alternate" and link.get("type") == "text/html" and link.get("href"):
            return str(link["href"])
    return ""


def iter_feed_entries(client, source: str, base: str, *, max_pages: int = 20, max_results: int = DEFAULT_MAX_RESULTS):
    start = 1
    for _ in range(max_pages):
        result = client.get_json(
            source,
            f"{base}{FEED_PATH}",
            params={"alt": "json", "max-results": max_results, "start-index": start},
        )
        if not result.ok or not isinstance(result.data, dict):
            break
        feed = result.data.get("feed") or {}
        entries = feed.get("entry") or []
        if not entries:
            break
        for entry in entries:
            url = _alternate_link(entry)
            if not url:
                continue
            yield FeedEntry(url=url, title=_text(entry.get("title")), content_html=_text(entry.get("content")))
        start += len(entries)
        total = _text(feed.get("openSearch$totalResults"))
        if total.isdigit() and start > int(total):
            break


def content_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("div.post-body, div.entry-content, article") or soup
    for tag in container.find_all(["script", "style", "figure", "noscript", "iframe", "ins"]):
        tag.decompose()
    for br in container.find_all("br"):
        br.replace_with("\n")
    return [line.strip() for line in container.get_text("\n").splitlines() if line.strip()]


def _is_tail(line: str) -> bool:
    lowered = line.casefold()
    if line.startswith(TAIL_PREFIXES):
        return True
    return any(fragment in lowered for fragment in TAIL_FRAGMENTS)


def _cut_tail(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if _is_tail(line):
            return lines[:index]
    return lines


def _is_credit_label(line: str) -> bool:
    return bool(CREDIT_LABEL_RE.match(line.strip()))


def lyrics_devanagari_marker(lines: list[str]) -> str:
    marker_index = -1
    for index, line in enumerate(lines):
        if any(marker in line and len(line) <= 10 for marker in DEVANAGARI_MARKERS):
            marker_index = index
    if marker_index >= 0:
        return "\n".join(_cut_tail(lines[marker_index + 1 :])).strip()
    body = [line for line in lines[1:] if not _is_credit_label(line) and len(line) <= 200]
    return "\n".join(_cut_tail(body)).strip()


def lyrics_credit_block(lines: list[str]) -> str:
    body = lines[1:] if lines else []
    last_label = -1
    for index, line in enumerate(body[:14]):
        if _is_credit_label(line):
            last_label = index
    start = last_label + 1 if last_label >= 0 else 0
    if start < len(body) and len(body[start]) <= 40:
        start += 1
    return "\n".join(_cut_tail(body[start:])).strip()


def title_artist_devanagari_marker(raw_title: str, lines: list[str]) -> tuple[str, str]:
    for pattern in (TITLE_IN_NEPALI_BY_RE, TITLE_LYRICS_BY_RE, TITLE_PIPES_RE, TITLE_DASH_ARTIST_RE):
        match = pattern.match(raw_title.strip())
        if match:
            return match.group("title").strip(" -|"), match.group("artist").strip(" -|")
    match = TITLE_DASH_LYRICS_RE.match(raw_title.strip())
    if match:
        return match.group("title").strip(" -|"), ""
    return re.sub(r"\s+Lyrics?\s*$", "", raw_title, flags=re.IGNORECASE).strip(" -|"), ""


def title_artist_credit_block(raw_title: str, lines: list[str]) -> tuple[str, str]:
    if lines:
        match = TITLE_DASH_ARTIST_RE.match(lines[0].strip())
        if match:
            return match.group("title").strip(" -|"), match.group("artist").strip(" -|")
    match = TITLE_DASH_LYRICS_RE.match(raw_title.strip())
    if match:
        return match.group("title").strip(" -|"), ""
    return re.sub(r"\s+Lyrics?\s*$", "", raw_title, flags=re.IGNORECASE).strip(" -|"), ""


def make_adapter(*, domain: str, base: str, style: str = "devanagari_marker", max_results: int = DEFAULT_MAX_RESULTS):
    lyrics_fn = lyrics_devanagari_marker if style == "devanagari_marker" else lyrics_credit_block
    title_fn = title_artist_devanagari_marker if style == "devanagari_marker" else title_artist_credit_block
    source = f"site_{domain}"

    def discover(client, max_pages: int = 20) -> list[str]:
        return sorted({entry.url for entry in iter_feed_entries(client, source, base, max_pages=max_pages, max_results=max_results)})

    def iter_pages(client, max_pages: int = 20):
        seen: set[str] = set()
        for entry in iter_feed_entries(client, source, base, max_pages=max_pages, max_results=max_results):
            if entry.url in seen:
                continue
            seen.add(entry.url)
            yield entry.url, entry.content_html

    def parse(html: str, url: str) -> SongPage | None:
        lines = content_lines(html)
        if not lines:
            return None
        title, artist = title_fn(lines[0], lines)
        lyrics = lyrics_fn(lines)
        return SongPage(artist=artist, title=title, lyrics=lyrics)

    return SimpleNamespace(
        DOMAIN=domain,
        BASE=base,
        STYLE=style,
        discover=discover,
        iter_pages=iter_pages,
        parse=parse,
    )
