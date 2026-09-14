"""Generic WordPress adapter: discovery via REST API, lyrics from rendered content."""

from __future__ import annotations

import html as html_module
import re
from types import SimpleNamespace

from bs4 import BeautifulSoup

from .base import SongPage

API_PATH = "/wp-json/wp/v2/posts"
PER_PAGE = 100
TITLE_PIPE_RE = re.compile(r"^(?P<title>.+?)\s+Lyrics\s*\|\s*(?P<artist>.+)$")
TITLE_DECORATION_RE = re.compile(r"\s+Lyrics\b.*$", re.IGNORECASE | re.DOTALL)
STOP_RE = re.compile(
    r"explore more|you can watch|also read|related (posts|lyrics|songs)|share (this|on|it)|"
    r"follow us|watch (the )?video|read more",
    re.IGNORECASE,
)
SECTION_LABEL_RE = re.compile(
    r"^(intro|verse|chorus|outro|bridge|hook|refrain|pre[- ]?chorus|mukhda|antara|"
    r"voice[- ]?over|singer|music|composer|lyricist)\s*\d*\s*:?\s*$",
    re.IGNORECASE,
)
SONG_TITLE_ROLE = "song-title"


def iter_pages(client, base: str, *, source: str, max_pages: int = 20):
    page = 1
    while page <= max_pages:
        result = client.get_json(
            source,
            f"{base}{API_PATH}",
            params={"per_page": PER_PAGE, "page": page, "_fields": "id,link,title,content"},
        )
        if not result.ok or not isinstance(result.data, list) or not result.data:
            break
        for post in result.data:
            link = str(post.get("link") or "")
            content = ((post.get("content") or {}).get("rendered")) or ""
            raw_title = ((post.get("title") or {}).get("rendered")) or ""
            if not link or not content:
                continue
            prefix = f'<div data-role="{SONG_TITLE_ROLE}">{html_module.escape(html_module.unescape(raw_title))}</div>'
            yield link, prefix + content
        if len(result.data) < PER_PAGE:
            break
        page += 1


def _raw_title(soup: BeautifulSoup) -> str:
    node = soup.select_one(f'[data-role="{SONG_TITLE_ROLE}"]')
    if node is not None and node.get_text(strip=True):
        return node.get_text(" ", strip=True)
    meta = soup.select_one("meta[property='og:title']")
    if meta is not None and meta.get("content"):
        return str(meta["content"])
    node = soup.select_one("h1.entry-title, article h1")
    if node is not None and node.get_text(strip=True):
        return node.get_text(" ", strip=True)
    if soup.title is not None and soup.title.string:
        return soup.title.string.strip()
    return ""


def _split_title(raw: str) -> tuple[str, str]:
    raw = re.sub(r"\s+", " ", raw or "").strip()
    match = TITLE_PIPE_RE.match(raw)
    if match:
        return match.group("title").strip(" -|"), match.group("artist").strip(" -|")
    title = TITLE_DECORATION_RE.sub("", raw).strip(" -|")
    return title, ""


def _lyrics_from_lines(lines: list[str]) -> str:
    start = -1
    for index, line in enumerate(lines):
        if index == 0:
            continue
        if STOP_RE.search(line):
            break
        matches_heuristic = len(line) <= 80 and re.search(r"lyrics", line, re.IGNORECASE) and not line.endswith(".")
        if matches_heuristic:
            start = index
            break
    if start < 0:
        return ""
    collected: list[str] = []
    for line in lines[start + 1 :]:
        if STOP_RE.search(line):
            break
        if SECTION_LABEL_RE.match(line):
            continue
        collected.append(line)
    return "\n".join(collected).strip()


def make_adapter(*, domain: str, base: str):
    source = f"site_{domain}"

    def discover(client, max_pages: int = 20) -> list[str]:
        return sorted({link for link, _ in iter_pages(client, base, source=source, max_pages=max_pages)})

    def parse(html: str, url: str) -> SongPage | None:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "style", "noscript", "iframe", "ins", "figure"]):
            tag.decompose()
        for br in soup.find_all("br"):
            br.replace_with("\n")
        raw_title = _raw_title(soup)
        title, artist = _split_title(raw_title)
        container = soup.select_one("div.entry-content, div.post-content, article") or soup
        lines = [line.strip() for line in container.get_text("\n").splitlines() if line.strip()]
        lyrics = _lyrics_from_lines(lines)
        return SongPage(artist=artist, title=title, lyrics=lyrics)

    return SimpleNamespace(DOMAIN=domain, BASE=base, discover=discover, iter_pages=iter_pages_wrapper(base, source), parse=parse)


def iter_pages_wrapper(base: str, source: str):
    def _iter(client, max_pages: int = 20):
        yield from iter_pages(client, base, source=source, max_pages=max_pages)

    return _iter
