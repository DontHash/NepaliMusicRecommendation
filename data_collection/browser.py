"""Tiered HTML fetching via Scrapling with disk cache (site adapters only)."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from . import config as cfg

TIERS = ("http", "dynamic", "stealthy")


class ScraplingNotInstalled(RuntimeError):
    pass


@dataclass(slots=True)
class PageResult:
    ok: bool
    status: int | None
    html: str = ""
    from_cache: bool = False
    error: str | None = None
    tier: str = "http"


_PACE_LOCK = threading.Lock()
_LAST_FETCH: dict[str, float] = {}


def _domain(url: str) -> str:
    host = urlsplit(url).netloc.lower()
    return host.split(":")[0].replace("www.", "")


def cache_path(paths, url: str) -> Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return paths.raw / "sites" / _domain(url) / f"{digest}.html"


def _response_html(response) -> str:
    for attr in ("html_content", "body", "text"):
        value = getattr(response, attr, None)
        if value is None:
            continue
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, str):
            return value
    return str(response)


def _response_status(response) -> int | None:
    status = getattr(response, "status", None)
    try:
        return int(status)
    except (TypeError, ValueError):
        return None


def _pace(domain: str, interval: float, sleep) -> None:
    with _PACE_LOCK:
        now = time.monotonic()
        last = _LAST_FETCH.get(domain)
        wait = max(0.0, interval - (now - last)) if last is not None else 0.0
        _LAST_FETCH[domain] = now + wait
    if wait > 0:
        sleep(wait)


def fetch_html(
    url: str,
    *,
    paths=None,
    refresh: bool = False,
    tier: str = "http",
    rate_interval: float = 2.0,
    sleep=time.sleep,
) -> PageResult:
    if tier not in TIERS:
        raise ValueError(f"unknown tier: {tier}")
    paths = (paths or cfg.DEFAULT_PATHS).ensure()
    target = cache_path(paths, url)
    if target.exists() and not refresh:
        return PageResult(ok=True, status=200, html=target.read_text(encoding="utf-8"), from_cache=True, tier=tier)

    try:
        from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher
    except ImportError as exc:
        raise ScraplingNotInstalled("run: pip install 'scrapling[fetchers]' && scrapling install") from exc

    domain = _domain(url)
    last_error = "fetch_failed"
    for attempt in range(1, 3):
        _pace(domain, rate_interval * attempt, sleep)
        try:
            if tier == "http":
                response = Fetcher.get(url, stealthy_headers=True)
            elif tier == "dynamic":
                response = DynamicFetcher.fetch(url, headless=True, network_idle=True)
            else:
                response = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            continue
        status = _response_status(response)
        html = _response_html(response)
        if status == 404:
            return PageResult(ok=False, status=404, error="not_found", tier=tier)
        if status is not None and status >= 400:
            last_error = f"http_{status}"
            continue
        if not html:
            last_error = "empty_html"
            continue
        _write_cache(paths, target, html, url, tier)
        return PageResult(ok=True, status=status or 200, html=html, tier=tier)
    return PageResult(ok=False, status=None, error=last_error, tier=tier)


def _write_cache(paths, target: Path, html: str, url: str, tier: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".html.tmp")
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(target)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "html",
        "tier": tier,
        "url": url,
        "path": str(target),
    }
    with open(paths.cache_index, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
